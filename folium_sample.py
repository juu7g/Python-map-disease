"""
folium を使った地図作成サンプル
"""

import folium
import webbrowser
import requests

def basic_map_geo():
    # 単純な地図の表示(色々なタイルで地図の違いを見る)
    _zoom = 10
    map = folium.Map(location=[35.69, 139.70], tiles='Cartodb dark_matter', zoom_start=_zoom)
    map = folium.Map(location=[35.69, 139.70], tiles='Cartodb Positron', zoom_start=_zoom)
    map = folium.Map(location=[35.69, 139.70], zoom_start=_zoom)   # same OpenStreetMap

    # GeoJSON の利用
    _url = "https://raw.githubusercontent.com/niiyz/JapanCityGeoJson/master/geojson/custom/tokyo23.json"    # 23区きめ細かい
    _url = "https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/geojson/s0001/N03-21_210101.json"  # 全国市区町村 少し大雑把
    # _url = "https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/geojson/s0010/prefectures.json"  # 全国都道府県 
    folium.GeoJson(_url).add_to(map)
    map.show_in_browser()

    # map.save('maptest.html')
    # webbrowser.open('maptest.html')

def basic_map_topo():
    # 単純な地図の表示
    map = folium.Map(location=[35.69, 139.70]
                    , zoom_start=10
                    , tiles='Cartodb Positron')

    # TopoJSON の利用
    _url = "https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/topojson/s0010/prefectures.json"  # 全国都道府県 
    topo_json_data = requests.get(_url).json()
    # print(topo_json_data)
    folium.TopoJson(topo_json_data
                    , "objects.prefectures").add_to(map)
    map.show_in_browser()

    # map.save('maptest.html')
    # webbrowser.open('maptest.html')

def get_csv_from_web():
    # 定当データの取得
    import csv, urllib.request
    from datetime import datetime
    now = datetime(2023, 10, 16)
    year = now.strftime('%Y')
    week = now.strftime('%U')
    _url = f'https://www.niid.go.jp/niid/images/idwr/sokuho/idwr-{year}/{year}{week}/{year}-{week}-teiten.csv'
    with urllib.request.urlopen(_url) as res:
        print(f'return url:{res.url}')
        if res.url != _url: return [("", "")]
        # ヘッダに対する処理
        next(res)   # 1行目
        title = next(res).decode('cp932').split(',')[0].replace('"', '')   # 2行目 報告期間
        shippei = next(res).decode('cp932').split(',')  # 3行目 疾病
        name_c = shippei[37].replace('"', '')            # 新型コロナ
        name_i = shippei[1].replace('"', '')             # インフルエンザ
        next(res)   # 4行目
        next(res)   # 5行目
        data = res.read()
        data = data.decode('cp932')
        data = data.splitlines()
    rows_c = [(row[0], float(row[38])) for row in csv.reader(data) if row[38]]   # 都道府県とCOVID-19定当を取得
    rows_i = [(row[0], float(row[2])) for row in csv.reader(data) if row[2]]   # 都道府県とインフルエンザ定当を取得
    # 定当の最大値
    max_value = max(max([x[1] for x in rows_c]), max([x[1] for x in rows_i]))
    return rows_c, rows_i, name_c, name_i, title, max_value

def Choropleth_map_geo(rows, max_value):
    """
    階級区分図の作成(TopoJSONを使用)
    Args:
        list:   報告数データ(都道府県と報告数のタプルのリスト)
        int:    報告数の最大値
    Returns:
        Map:    作成した地図のMapオブジェクト
    """
    # Mapオブジェクトの作成(日本地図全体が表示されるような位置と倍率を指定)
    map = folium.Map(location=[39.00, 137.00], tiles='Cartodb Positron', zoom_start=6)

    # GeoJSON の利用
    _url = "https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/geojson/s0010/prefectures.json"  # 全国都道府県 
    # topo_json_data = requests.get(_url).json()

    # MapオブジェクトにTopoJSONデータを追加
    folium.GeoJson(_url).add_to(map)

    # Choroplethの作成
    cp = folium.Choropleth(geo_data=_url
                            , data=rows                             # 地域区分するデータ
                            , key_on='properties.N03_001'           # 地域を特定するキー
                            # , bins=range(0, int(max_value + 2), 1)  # カラーマップ
                            # , fill_color='PuRd'                     # カラーマップの色
                            , fill_opacity=0.3                      # 透明度
                            , line_weight=2,                        # 境界線の幅
                            )
    cp.add_to(map)          # Mapオブジェクトに追加


    map.show_in_browser()               # こちらなら表示できるけど添付ファイルが残る

    return map

def Choropleth_map_topo(rows, max_value):
    """
    階級区分図の作成(TopoJSONを使用)
    Args:
        list:   報告数データ(都道府県と報告数のタプルのリスト)
        int:    報告数の最大値
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
                            , topojson='objects.prefectures'    # GeoJSONへ変換するデータの位置
                            , data=rows                             # 地域区分するデータ
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
        d["properties"]["teito"] = teito[d["properties"]["N03_001"]]
    # ツールチップの追加
    folium.GeoJsonTooltip(['N03_001', 'teito'], ['地域', '人数']).add_to(cp.geojson)
    # カラーマップの幅を指定(地図を並べて表示した時に長くなるため)
    cp.color_scale.width = 200

    # ブログ埋め込み用iframeの作成 作成したテキストを埋め込めば地図が表示される(色分けされなかった)
    # iframe = map._repr_html_()
    # with open("ifram.txt", "w", encoding='utf-8') as f:
    #     f.write(iframe)

    map.show_in_browser()               # こちらなら表示できるけど添付ファイルが残る

    # map.save('maptest.html')
    # webbrowser.open('maptest.html')   # 開くのが早すぎで出てこない
    return map

def tow_choropleth(rows_c, rows_i, name_c, name_i, title, max_value):
    f = folium.Figure()
    sb1 = f.add_subplot(1, 2, 1)
    sb2 = f.add_subplot(1, 2, 2)
    m1 = Choropleth_map_topo(rows_c, max_value)
    m2 = Choropleth_map_topo(rows_i, max_value)
    # add_child タイトルより先じゃないとタイトルが出ない
    sb1.add_child(m1)
    sb2.add_child(m2)
    # タイトルを追加
    title_html = f'''
             <h3 align="center" style="font-size:20px"><b>{name_c}定点当たり報告数</b></h3>
             <h6 align="right";">{title}</h6>
             '''
    m1.get_root().html.add_child(folium.Element(title_html))
    title_html = f'''
             <h3 align="center" style="font-size:20px"><b>{name_i}定点当たり報告数</b></h3>
             <h6 align="right";">{title}</h6>
             '''
    m2.get_root().html.add_child(folium.Element(title_html))

    # 地図htmlをファイルに保存
    f.save('maptest.html')

    # HTMLファイルをブラウザで表示
    webbrowser.open('maptest.html')

basic_map_geo()
# basic_map_topo()
# rows_c, rows_i, name_c, name_i, title, max_value = get_csv_from_web()
# Choropleth_map_geo(rows_c, max([x[1] for x in rows_c]))
# Choropleth_map_topo(rows_c, max([x[1] for x in rows_c]))
# tow_choropleth(rows_c, rows_i, name_c, name_i, title, max_value)
print('finished')