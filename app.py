
import streamlit as st
import fastf1
import pandas as pd
import matplotlib.pyplot as plt
import os

# fastf1のキャッシュ設定
cache_path = 'ff1_cache'
if not os.path.exists(cache_path):
    os.makedirs(cache_path)
fastf1.Cache.enable_cache(cache_path)

st.set_page_config(layout="wide")
st.title('F1 Lap Time Comparison App')

@st.cache_data
def load_session_data(year, gp, session_type):
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        return session
    except Exception as e:
        st.error(f"Error loading session data: {e}")
        return None

# サイドバーでの入力
st.sidebar.header('Select Race Details')
year = st.sidebar.selectbox('Year', options=range(2025, 2017, -1), index=0) # 2023年から2018年まで

# 利用可能なグランプリを取得（初回ロード時のみ）
@st.cache_data
def get_available_gps(year):
    try:
        schedule = fastf1.get_event_schedule(year)
        return schedule['EventName'].tolist()
    except Exception as e:
        st.error(f"Error fetching schedule for {year}: {e}")
        return []

available_gps = get_available_gps(year)
gp = st.sidebar.selectbox('Grand Prix', options=available_gps)
session_type = st.sidebar.selectbox('Session Type', options=['Race', 'Qualifying', 'Sprint'])

# データロード
if gp and session_type:
    session = load_session_data(year, gp, session_type)

    if session:
        # ドライバー選択
        drivers = sorted(session.drivers)
        driver_names = [session.get_driver(driver)['Abbreviation'] for driver in drivers]

        st.sidebar.header('Select Drivers for Comparison')
        driver1 = st.sidebar.selectbox('Driver 1', options=driver_names, index=0 if len(driver_names) > 0 else 0)
        driver2 = st.sidebar.selectbox('Driver 2', options=driver_names, index=1 if len(driver_names) > 1 else 0)

        if driver1 and driver2 and driver1 != driver2:
            st.subheader(f'{driver1} vs {driver2} - Lap Time Comparison')

            # ラップデータ取得
            laps_driver1 = session.laps.pick_driver(driver1)
            laps_driver2 = session.laps.pick_driver(driver2)

            # ラップタイムを秒単位に変換
            laps_driver1['LapTime(s)'] = laps_driver1['LapTime'].dt.total_seconds()
            laps_driver2['LapTime(s)'] = laps_driver2['LapTime'].dt.total_seconds()

            # プロット
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.plot(laps_driver1['LapNumber'], laps_driver1['LapTime(s)'], label=driver1, color='blue')
            ax.plot(laps_driver2['LapNumber'], laps_driver2['LapTime(s)'], label=driver2, color='orange')

            ax.set_xlabel('Lap Number')
            ax.set_ylabel('Lap Time (Seconds)')
            ax.set_title(f'{year} {gp} {session_type} Lap Times')
            ax.legend()
            ax.grid(True)

            st.pyplot(fig)

            # ラップタイムをMM:SS.mmm形式に変換するヘルパー関数
            def _convert_laptime_to_str(td):
                if pd.isna(td):
                    return None
                total_seconds = td.total_seconds()
                minutes = int(total_seconds // 60)
                seconds = total_seconds % 60
                return f"{minutes:02d}:{seconds:06.3f}"

            # 表示用にDataFrameをコピーし、LapTimeをフォーマット
            display_laps_driver1 = laps_driver1.copy()
            display_laps_driver1['LapTime'] = display_laps_driver1['LapTime'].apply(_convert_laptime_to_str)
            display_laps_driver2 = laps_driver2.copy()
            display_laps_driver2['LapTime'] = display_laps_driver2['LapTime'].apply(_convert_laptime_to_str)

            st.subheader('Raw Lap Data')
            st.write(f'{driver1} Laps')
            st.dataframe(display_laps_driver1[['LapNumber', 'LapTime', 'TyreLife', 'Stint', 'Compound']])
            st.write(f'{driver2} Laps')
            st.dataframe(display_laps_driver2[['LapNumber', 'LapTime', 'TyreLife', 'Stint', 'Compound']])
        elif driver1 == driver2:
            st.warning("Please select two different drivers for comparison.")
    else:
        st.info("Select a year, Grand Prix, and session type to load data.")
else:
    st.info("Select a year, Grand Prix, and session type to load data.")
