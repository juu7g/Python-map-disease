"""
GeoPandas test
"""
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
from datetime import date, timedelta

plt.rcParams['font.family'] = 'Meiryo'
plt.show()

# 地図データ取得
url1 = "https://raw.githubusercontent.com/smartnews-smri/japan-topography/main/data/municipality/geojson/s0010/prefectures.json"  # 全国都道府県 
gdf = gpd.read_file(url1)
# gdf.plot()

# 色分けデータ取得
today = date.today() - timedelta(days=16)
year = today.strftime('%Y')
week = today.strftime('%V')
url2 = f"https://www.niid.go.jp/niid/images/idwr/sokuho/idwr-{year}/{year}{week}/{year}-{week}-teiten.csv"
print(f"日付：{today.strftime('%Y/%m/%d')}、週：{week}")

# 色分け用データ作成
# case 1    1回の読み込みで見出しまで作る
# import numpy as np
# try:
#         df = pd.read_csv(url2, encoding='cp932', skiprows=[4], header=[2, 3])
#         lvl0 = np.where(df.columns.levels[0].str.contains('Unnamed'), '', df.columns.levels[0])
#         a = [x for x in df.columns.levels[0] if not 'Unnamed' in x]
#         i = pd.Index(a).repeat(2)
#         # マルチインデックスの更新方法を検討したが断念
# except:
#         print('感染症データがない日付を指定されました')
# #         exit()

# case 2    ヘッダーとデータを分けて作る
# データ部分の作成
try:
    df = pd.read_csv(url2, encoding='cp932', skiprows=5, header=None)  # ヘッダー部分を読まない
except:
    print('感染症データがない日付を指定されました')
    exit()

df = df.dropna(how='all')   # すべての列がNAの行を削除
# ヘッダー部分の作成(ヘッダー部分をデータとして読み込む(2行スキップして2行だけ読む))
cdf = pd.read_csv(url2, encoding='cp932', skiprows=2, nrows=2, header=None)
cdf = cdf.ffill(axis=1)     # 感染症名が左のカラムにしかないので右にコピー
cdf = cdf.fillna('N03_001') # 先頭にNAが残るのでN03_001を設定
df.columns = pd.MultiIndex.from_frame(cdf.T)    # カラム名にするためマルチインデックス化(データは行列を入れ替えて読む)
s1df = df.drop(columns='報告', level=1)         # マルチインデックスのレベル1が「報告」の列を削除
s1df.columns = s1df.columns.droplevel(1)        # マルチインデックスのレベル1を削除、シングル化

# データを都道府県名をキーにして地図データgdfにマージ
gdf = gdf.merge(s1df, on='N03_001', how='left')

# 地図作成
_, axes = plt.subplots(1, 2, figsize=(12, 6))     # 二つ分の図領域を作成
ax1 = gdf.plot(ax=axes[0], column='インフルエンザ', cmap='PuRd', vmin=0, vmax=40
        , legend=True, legend_kwds={'label':'インフルエンザ', 'location':'left'})
ax1.set_axis_off()              # 目盛軸を非表示
ax1.set_title('インフルエンザ')
ax1.set_xlim(130, 145)
ax1.set_ylim(30, 45)
gdf.apply(lambda x: ax1.annotate(x.インフルエンザ, (x.geometry.centroid.x, x.geometry.centroid.y), fontsize=6, color='yellow' if x.インフルエンザ > 8 else "black"), axis=1)

ax2 = gdf.plot(ax=axes[1], column='COVID-19', cmap='PuRd', vmin=0, vmax=40
        , legend=True, legend_kwds={'label':'COVID-19'})
ax2.set_axis_off()              # 目盛軸を非表示
ax2.set_title('COVID-19')
ax2.set_xlim(130, 145)
ax2.set_ylim(30, 45)
gdf.apply(lambda x: ax2.annotate(x["COVID-19"], (x.geometry.centroid.x, x.geometry.centroid.y), fontsize=6, color='yellow' if x["COVID-19"] > 8 else "black"), axis=1)

plt.show()