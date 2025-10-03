
import fastf1
import pandas
import os
import matplotlib.pyplot as plt

# fastf1のキャッシュを設定（2回目以降のデータ読み込みが高速になります）
cache_path = 'ff1_cache'
if not os.path.exists(cache_path):
    print(f"Cache directory '{cache_path}' not found. Creating it...")
    os.makedirs(cache_path)

fastf1.Cache.enable_cache(cache_path)

# 2023年 日本GPのセッションを読み込む
# 'R'はRace（決勝）を意味します
session = fastf1.get_session(2023, 'Japan', 'R')
session.load()

# フェルスタッペン（VER）とノリス（NOR）のラップタイムを取得
ver_laps = session.laps.pick_driver('VER')
nor_laps = session.laps.pick_driver('NOR')

# 必要な情報だけを表示（これは以前の出力）
print("Max Verstappen Laps - 2023 Japanese GP")
print(ver_laps[['LapNumber', 'LapTime', 'TyreLife', 'Stint']])

print("\nLando Norris Laps - 2023 Japanese GP")
print(nor_laps[['LapNumber', 'LapTime', 'TyreLife', 'Stint']])

# ラップタイムを秒単位に変換（プロットしやすくするため）
ver_lap_times = ver_laps['LapTime'].dt.total_seconds()
nor_lap_times = nor_laps['LapTime'].dt.total_seconds()

# グラフの作成
plt.figure(figsize=(12, 6))
plt.plot(ver_laps['LapNumber'], ver_lap_times, label='Max Verstappen', color='blue')
plt.plot(nor_laps['LapNumber'], nor_lap_times, label='Lando Norris', color='orange')

plt.xlabel('Lap Number')
plt.ylabel('Lap Time (Seconds)')
plt.title('2023 Japanese GP Race Lap Times Comparison (VER vs NOR)')
plt.legend()
plt.grid(True)

# グラフを画像ファイルとして保存
plot_filename = 'lap_comparison.png'
plt.savefig(os.path.join(os.path.dirname(__file__), plot_filename))
print(f"Lap time comparison plot saved as {plot_filename}")

plt.show() # グラフを表示（環境によっては表示されない場合があります）
