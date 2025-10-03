
import fastf1
import os

# fastf1のキャッシュ設定
cache_path = 'ff1_cache'
if not os.path.exists(cache_path):
    os.makedirs(cache_path)
fastf1.Cache.enable_cache(cache_path)

def get_available_gps_debug(year):
    try:
        print(f"Fetching schedule for year: {year}")
        schedule = fastf1.get_event_schedule(year)
        print(f"Full schedule for {year}:\n{schedule}")

        # EventFormatカラムが存在するか確認
        if 'EventFormat' not in schedule.columns:
            print("'EventFormat' column not found in schedule.")
            return []

        # 決勝(Race)があるイベントのみをフィルタリング
        race_events = schedule[schedule['EventFormat'].apply(lambda x: 'Race' in x)]
        print(f"Race events for {year}:\n{race_events}")

        if not race_events.empty:
            return race_events['EventName'].tolist()
        else:
            print("No race events found with 'Race' in EventFormat.")
            return []
    except Exception as e:
        print(f"Error fetching schedule for {year}: {e}")
        return []

# 2023年のグランプリリストをデバッグ
year_to_debug = 2023
gps = get_available_gps_debug(year_to_debug)
print(f"\nAvailable GPs for {year_to_debug}: {gps}")

