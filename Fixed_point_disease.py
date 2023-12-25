"""
定点把握疾患の定点あたりの報告数の階級区分図作成
"""

import folium
import csv, urllib.request
import requests
import webbrowser
from datetime import datetime, date, timedelta
import tkinter as tk
from tkcalendar import DateEntry
from typing import Tuple       # 関数アノテーション用

class Mapping():
    """
    地図作成
    """
    def __init__(self, view:tk.Frame) -> None:
        """
        コンストラクタ：制御画面クラスを関連付ける
        Args:
            Frame:  画面クラス(ビュー)
        """
        self.view = view    # 制御画面クラスのオブジェクト


    def get_csv_from_web(self, today:date) -> Tuple[list, list, str, str, str, str]:
        """
        定点把握疾患の定点あたりの報告数をWebから取得
        Args:
            date:   初期表示日付
        Returns:
            list:   新型コロナデータ(都道府県と報告数のタプルのリスト)
            list:   インフルエンザデータ(都道府県と報告数のタプルのリスト)
            str:    感染症名
            str:    感染症名
            str:    期間
            str:    エラーメッセージ(エラーなしの時は空文字)
        """
        msg =""
        # today = datetime(2023, 10, 16)
        year = today.strftime('%Y')
        week = today.strftime('%U')
        # csvファイルのurl
        _url = f'https://www.niid.go.jp/niid/images/idwr/sokuho/idwr-{year}/{year}{week}/{year}-{week}-teiten.csv'
        # csvファイルの取得
        with urllib.request.urlopen(_url) as res:
            print(f'request url:{_url}')
            print(f'return  url:{res.url}')
            if res.url != _url:
                msg = "指定した日付の週にデータがありません"
                return None, None, None, None, None, None, msg
            # ヘッダに対する処理
            next(res)   # 1行目
            title = next(res).decode('cp932').split(',')[0].replace('"', '')   # 2行目 報告期間
            shippei = next(res).decode('cp932').split(',')  # 3行目 疾病
            if len(shippei) > 37:   # 2023/5/8以前のデータはない
                name_c = shippei[37].replace('"', '')            # 新型コロナ
            else:
                name_c = ""
            name_i = shippei[1].replace('"', '')             # インフルエンザ
            next(res)   # 4行目
            next(res)   # 5行目
            data = res.read()                       # 残りをすべて読む
            data = data.decode('cp932')             # urlopenで読んだ場合はデコードが必要
            data = data.splitlines()                # 行ごとに分ける
        # 新型コロナのデータ作成(データがあるものだけ、報告がないと「-」が設定されるので弾く)
        if len(shippei) > 37:   # 2023/5/8以前のデータはない
            rows_c = [(row[0], float(row[38])) for row in csv.reader(data) if row[38] and row[38] != "-"]   # 都道府県とCOVID-19定当を取得
        else:
            rows_c = []
        # インフルエンザのデータ作成(データがあるものだけ、報告がないと「-」が設定されるので弾く)
        rows_i = [(row[0], float(row[2])) for row in csv.reader(data) if row[2] and row[2] != "-"]   # 都道府県とインフルエンザ定当を取得
        return rows_c, rows_i, name_c, name_i, title, msg

    def Choropleth_map_topo(self, rows, s_name, title, max_value, out2html:bool=False) -> folium.Map:
        """
        階級区分図の作成(TopoJSONを使用)
        Args:
            list:   報告数データ(都道府県と報告数のタプルのリスト)
            str:    感染症名
            str:    期間
            int:    報告数の最大値
            bool:   HTMLファイルへ出力するか
        Returns:
            Map:    作成した地図のMapオブジェクト
        """
        # Mapオブジェクトの作成(日本地図全体が表示されるような位置と倍率を指定)
        map = folium.Map(location=[39.00, 137.00], tiles='Cartodb Positron', zoom_start=6)

        # TopoJSON の利用
        _url = "https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/topojson/s0010/prefectures.json"  # 全国都道府県 
        topo_json_data = requests.get(_url).json()

        # MapオブジェクトにTopoJSONデータを追加
        folium.TopoJson(topo_json_data, "objects.prefectures").add_to(map)

        # Choroplethの作成
        cp = folium.Choropleth(geo_data=topo_json_data
                                , topojson='objects.prefectures'  # GeoJSONへ変換するデータの位置
                                , data=rows                            # 地域区分するデータ
                                , key_on='properties.N03_001'           # 地域を特定するキー
                                , bins=range(0, int(max_value + 2), 1)  # カラーマップ
                                , fill_color='PuRd'                     # カラーマップの色
                                , fill_opacity=0.3                      # 透明度
                                , line_weight=2,                        # 境界線の幅
                                )
        cp.add_to(map)          # Mapオブジェクトに追加

        # TopoJSONの地域データに定当データを追加(ツールチップに表示するため)
        # TopoJSONのgeometriesに都道府県のデータがあるのでそこのpropertisに要素追加
        teito = dict(rows)  # リストを辞書化
        for d in topo_json_data["objects"]["prefectures"]["geometries"]:
            # "properties"の辞書に定当のキーと値を追加(都道府県名をキーにして定当を取得)
            try:    # 都道府県で回しているのでデータがないことがある
                d["properties"]["teito"] = teito[d["properties"]["N03_001"]]
            except KeyError:
                pass    # 定当のデータがない場合追加しない
        # ツールチップの追加
        folium.GeoJsonTooltip(['N03_001', 'teito'], ['地域', '人数']).add_to(cp.geojson)
        # カラーマップの幅を指定(地図を並べて表示した時に長くなるため)
        cp.color_scale.width = 200

        # タイトルを追加
        title_html = f'''
                <h3 align="center" style="font-size:20px"><b>{s_name}定点当たり報告数</b></h3>
                <h6 align="right";">{title}</h6>
                '''
        map.get_root().html.add_child(folium.Element(title_html))

        # ブログ埋め込み用iframeの作成 作成したテキストを埋め込めば地図が表示される(色分けされなかった)
        # iframe = map._repr_html_()
        # with open("ifram.txt", "w", encoding='utf-8') as f:
        #     f.write(iframe)

        # map.show_in_browser()               # こちらなら表示できるけど添付ファイルが残る

        if out2html:
            fname = f"{s_name}map.html"
            map.save(fname)
            webbrowser.open(fname)   # 開くのが早すぎで出てこない
        return map

    def tow_choropleth(self, rows_c, rows_i, name_c, name_i, title, max_c, max_i):
        """
        地図を2つ並べて表示
        Args:
            list:   新型コロナデータ(都道府県と報告数のタプルのリスト)
            list:   インフルエンザデータ(都道府県と報告数のタプルのリスト)
            str:    新型コロナ感染症名
            str:    インフルエンザ感染症名
            str:    期間
            int:    新型コロナ報告数の最大値
            int:    インフルエンザ報告数の最大値
        """
        # Figureオブジェクトの作成(ここに2つの地図を追加する)
        f = folium.Figure()
        if rows_c:  # コロナのデータがある時だけ作成
            # コロナ用階級区分図の作成
            sb1 = f.add_subplot(1, 2, 1)    # 1行2列の1番目のdivチャイルドをFigureオブジェクトに追加
            m1 = self.Choropleth_map_topo(rows_c, name_c, title, max_c)    # 地図作成
            # m1.save("COVID-19_map.html")
            sb1.add_child(m1)   # divチャイルドに地図を追加(add_child タイトルより先じゃないとタイトルが出ない)
            # タイトルを追加
            title_html = f'''
                    <h3 align="center" style="font-size:20px"><b>{name_c}定点当たり報告数</b></h3>
                    <h6 align="right";">{title}</h6>
                    '''
            m1.get_root().html.add_child(folium.Element(title_html))
        # インフルエンザ用階級区分図の作成
        sb2 = f.add_subplot(1, 2, 2)    # 1行2列の2番目のdivチャイルドをFigureオブジェクトに追加
        m2 = self.Choropleth_map_topo(rows_i, name_i, title, max_i)    # 地図作成
        # m2.save("flu_map.html")
        sb2.add_child(m2)   # divチャイルドに地図を追加(add_child タイトルより先じゃないとタイトルが出ない)
        # タイトルを追加
        title_html = f'''
                <h3 align="center" style="font-size:20px"><b>{name_i}定点当たり報告数</b></h3>
                <h6 align="right";">{title}</h6>
                '''
        m2.get_root().html.add_child(folium.Element(title_html))

        # 地図htmlをファイルに保存
        fname = "COV_flu_map.html"
        f.save(fname)
        # HTMLファイルをブラウザで表示
        webbrowser.open(fname)   # 開くのが早すぎで出てこないことがある

    def create_map(self, today:date) -> str:
        """
        地図作成
        Args:
            date:   報告者数報告日
        Returns:
            str:    実行結果のメッセージ
        """
        rows_c, rows_i, name_c, name_i, title, msg = self.get_csv_from_web(today)
        # エラーがあったら戻る
        if msg: return msg
        # 感染症にチェックが無かったら戻る
        if self.view.var_col.get() == False and self.view.var_flu.get() == False:
            return "感染症の両方か、どちらかにチェックを付けてください"
        # 定当の最大値
        max_c = max([x[1] for x in rows_c], default=0)
        max_i = max([x[1] for x in rows_i])
        # 最大値を固定にする場合
        if self.view.var_fix_max.get(): max_c = max_i = max(40, max_c, max_i)
        # どの感染症を対象にするかで出す地図を分ける
        if self.view.var_col.get() and self.view.var_flu.get(): # 新型コロナとインフルエンザ
            self.tow_choropleth(rows_c, rows_i, name_c, name_i, title, max_c, max_i)
        elif self.view.var_col.get():                           # 新型コロナ
            self.Choropleth_map_topo(rows_c, name_c, title, max_c, True)
        elif self.view.var_flu.get():                           # インフルエンザ
            self.Choropleth_map_topo(rows_i, name_i, title, max_i, True)
        print('finished')
        return "地図をブラウザに表示しました"

class MyFrame(tk.Frame):
    """
    操作画面クラス
    """
    def __init__(self, master) -> None:
        """
        コンストラクタ：画面作成
        """
        super().__init__(master)
        # タイトル
        lbl_title = tk.Label(self, text="定点把握疾患の定点あたりの報告数")
        lbl_title.pack()
        # カレンダー    最新データは今日の16に前の週からなのでカレンダーの初期値とする
        latest_date = date.today() - timedelta(days=16)
        self.tkcal = DateEntry(self, year=latest_date.year, month=latest_date.month, day=latest_date.day, date_pattern='y/m/d', locale='ja_JP')
        self.tkcal.pack()
        # 作成ボタン
        btn_exe = tk.Button(self, text='地図作成', command=self.create_map)
        btn_exe.pack()
        # チェックボックス(最大値)
        self.var_fix_max = tk.BooleanVar(self, True)
        chb_fix_max = tk.Checkbutton(self, variable=self.var_fix_max, text="最大値を40に固定(オフはデータ依存)")
        chb_fix_max.pack()
        # メッセージ欄
        self.var_msg = tk.StringVar(self)
        lbl_msg = tk.Label(self, textvariable=self.var_msg, width=40, relief=tk.RIDGE)
        lbl_msg.pack(side=tk.BOTTOM, fill="x")
        # チェックボックス(コロナ)
        self.var_col = tk.BooleanVar(self, True)
        chb_col = tk.Checkbutton(self, variable=self.var_col, text="新型コロナ")
        chb_col.pack(side=tk.LEFT)
        # チェックボックス(インフルエンザ)
        self.var_flu = tk.BooleanVar(self, True)
        chb_flu = tk.Checkbutton(self, variable=self.var_flu, text="インフルエンザ")
        chb_flu.pack(side=tk.RIGHT)

    def set_control(self, ctrl:Mapping):
        """
        コントロールの指定とボタンの操作をパイント
        Args:
            Mapping:    コントロールオブジェクト(地図作成オブジェクト)
        """
        self.ctrl = ctrl
    
    def create_map(self):
        """
        地図作成(カレンダーから日付を取得して地図を作成)
        """
        self.var_msg.set("")
        self.update_idletasks()
        today = self.tkcal.get_date()
        msg = self.ctrl.create_map(today)
        self.var_msg.set(msg)

class App(tk.Tk):
    """
    アプリケーションクラス
    """
    def __init__(self) -> None:
        """
        コンストラクタ：操作画面クラスと制御クラスを作成し関連付ける
        """
        super().__init__()

        self.title("定点把握疾患")              # タイトル
        my_frame = MyFrame(self)                    # MyFrameクラス(V)のインスタンス作成
        my_frame.pack()
        ctr = Mapping(my_frame)         # 制御クラス(C)のインスタンス作成
        my_frame.set_control(ctr)       # MyFrameクラスに制御クラスを関連付ける

if __name__ == '__main__':
    app = App()
    app.mainloop()
