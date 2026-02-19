import streamlit as st
import fastf1
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

# --- Page Config ---
st.set_page_config(
    page_title="F1 Lap Analysis",
    page_icon="🏎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Hide Streamlit default header padding */
    .block-container { padding-top: 1.5rem; }

    /* F1-style title bar */
    .f1-header {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 4px;
    }
    .f1-title {
        font-size: 2rem;
        font-weight: 900;
        color: #ffffff;
        letter-spacing: 3px;
        text-transform: uppercase;
        border-left: 5px solid #e10600;
        padding-left: 14px;
        line-height: 1.1;
    }
    .f1-subtitle {
        font-size: 0.85rem;
        color: #888888;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding-left: 19px;
        margin-top: 2px;
    }

    /* KPI card */
    .kpi-card {
        background: #242424;
        border-radius: 8px;
        padding: 16px 18px;
        margin-bottom: 8px;
    }
    .kpi-driver {
        font-size: 1.1rem;
        font-weight: 800;
        letter-spacing: 2px;
        margin-bottom: 10px;
    }
    .kpi-row {
        margin-top: 8px;
    }
    .kpi-label {
        font-size: 0.65rem;
        color: #777777;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 1.15rem;
        font-weight: 600;
        color: #ffffff;
        line-height: 1.2;
    }
    .kpi-value-sm {
        font-size: 0.95rem;
        color: #cccccc;
        line-height: 1.2;
    }

    /* Section header with red underline */
    .section-header {
        font-size: 1.1rem;
        font-weight: 700;
        color: #ffffff;
        text-transform: uppercase;
        letter-spacing: 2px;
        border-bottom: 2px solid #e10600;
        padding-bottom: 6px;
        margin-top: 8px;
        margin-bottom: 16px;
    }

    /* Sidebar section label */
    .sidebar-section {
        font-size: 0.7rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 4px;
    }

    /* Tab styling */
    .stTabs [data-baseweb="tab"] {
        color: #aaaaaa;
    }
    .stTabs [aria-selected="true"] {
        color: #ffffff !important;
        border-bottom-color: #e10600 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- FastF1 Cache ---
cache_path = 'ff1_cache'
os.makedirs(cache_path, exist_ok=True)
fastf1.Cache.enable_cache(cache_path)

# --- Constants ---
TYRE_COLORS = {
    'SOFT': '#FF3333',
    'MEDIUM': '#FFD700',
    'HARD': '#EEEEEE',
    'INTERMEDIATE': '#39B54A',
    'WET': '#0067FF',
    'UNKNOWN': '#888888',
    'TEST_UNKNOWN': '#888888',
}

DRIVER_COLORS = [
    '#e10600',  # F1 red
    '#00D2BE',  # Mercedes teal
    '#FFF500',  # Renault yellow
    '#0090FF',  # Williams blue
    '#FF8000',  # McLaren orange
]


# --- Helper functions ---
def format_laptime(seconds):
    if pd.isna(seconds):
        return "N/A"
    minutes = int(seconds // 60)
    secs = seconds % 60
    return f"{minutes}:{secs:06.3f}"


def laptime_td_to_str(td):
    if pd.isna(td):
        return None
    total = td.total_seconds()
    minutes = int(total // 60)
    secs = total % 60
    return f"{minutes:02d}:{secs:06.3f}"


def get_pit_laps(laps_df):
    """Return lap numbers after which a pit stop was made (last lap of each non-final stint)."""
    pit_laps = []
    stints = sorted(laps_df['Stint'].dropna().unique())
    for stint in stints[:-1]:
        last_lap = laps_df[laps_df['Stint'] == stint]['LapNumber'].max()
        if not pd.isna(last_lap):
            pit_laps.append(int(last_lap))
    return pit_laps


# --- Cached data loaders ---
@st.cache_resource
def get_available_gps(year):
    try:
        schedule = fastf1.get_event_schedule(year)
        return schedule['EventName'].tolist()
    except Exception as e:
        st.error(f"スケジュール取得エラー ({year}): {e}")
        return []


@st.cache_resource
def load_session(year, gp, session_type):
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load(laps=True, telemetry=False, weather=False, messages=False)
        return session
    except Exception as e:
        st.error(f"セッションデータ読み込みエラー: {e}")
        return None


@st.cache_resource
def load_session_with_telemetry(year, gp, session_type):
    try:
        session = fastf1.get_session(year, gp, session_type)
        session.load(laps=True, telemetry=True, weather=False, messages=False)
        return session
    except Exception as e:
        st.error(f"テレメトリー読み込みエラー: {e}")
        return None


# ============================================================
# MAIN APP
# ============================================================

# --- Header ---
st.markdown("""
<div class="f1-header">
    <div>
        <div class="f1-title">F1 Lap Analysis</div>
        <div class="f1-subtitle">Formula 1 Race Data Visualization</div>
    </div>
</div>
""", unsafe_allow_html=True)
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.markdown('<div class="sidebar-section">Race Selection</div>', unsafe_allow_html=True)
    year = st.selectbox('Year', options=range(2025, 2017, -1), index=0)

    available_gps = get_available_gps(year)
    gp = st.selectbox('Grand Prix', options=available_gps)
    session_type = st.selectbox('Session Type', options=['Race', 'Qualifying', 'Sprint'])

    st.divider()
    st.markdown('<div class="sidebar-section">Driver Selection</div>', unsafe_allow_html=True)

# --- Session load ---
if not (gp and session_type):
    st.info("サイドバーでYear・Grand Prix・Session Typeを選択してください。")
    st.stop()

session = load_session(year, gp, session_type)
if session is None:
    st.stop()

drivers = sorted(session.drivers)
driver_names = [session.get_driver(d)['Abbreviation'] for d in drivers]

with st.sidebar:
    selected_drivers = st.multiselect(
        'Drivers (max 5)',
        options=driver_names,
        default=driver_names[:2] if len(driver_names) >= 2 else driver_names,
        max_selections=5,
    )

if not selected_drivers:
    st.info("少なくとも1人のドライバーを選択してください。")
    st.stop()

# --- Gather lap data ---
all_laps: dict[str, pd.DataFrame] = {}
for drv in selected_drivers:
    laps = session.laps.pick_driver(drv).copy()
    laps['LapTime(s)'] = laps['LapTime'].dt.total_seconds()
    all_laps[drv] = laps

# ============================================================
# KPI SUMMARY CARDS
# ============================================================
st.markdown('<div class="section-header">Session Summary</div>', unsafe_allow_html=True)

kpi_cols = st.columns(len(selected_drivers))
for idx, drv in enumerate(selected_drivers):
    laps = all_laps[drv]
    valid = laps.dropna(subset=['LapTime(s)'])
    fastest = valid['LapTime(s)'].min()
    average = valid['LapTime(s)'].mean()
    pit_count = max(0, laps['Stint'].nunique() - 1)
    drv_color = DRIVER_COLORS[idx % len(DRIVER_COLORS)]

    with kpi_cols[idx]:
        st.markdown(f"""
        <div class="kpi-card" style="border-top: 3px solid {drv_color};">
            <div class="kpi-driver" style="color: {drv_color};">{drv}</div>
            <div class="kpi-row">
                <div class="kpi-label">Fastest Lap</div>
                <div class="kpi-value">{format_laptime(fastest)}</div>
            </div>
            <div class="kpi-row">
                <div class="kpi-label">Avg Lap Time</div>
                <div class="kpi-value-sm">{format_laptime(average)}</div>
            </div>
            <div class="kpi-row">
                <div class="kpi-label">Pit Stops</div>
                <div class="kpi-value-sm">{pit_count}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.divider()

# ============================================================
# LAP TIME CHART
# ============================================================
st.markdown('<div class="section-header">Lap Time Comparison</div>', unsafe_allow_html=True)

fig = go.Figure()
all_pit_laps: set[int] = set()

for idx, drv in enumerate(selected_drivers):
    laps = all_laps[drv]
    drv_color = DRIVER_COLORS[idx % len(DRIVER_COLORS)]
    valid = laps.dropna(subset=['LapTime(s)'])

    # Pit stop detection
    pit_laps = get_pit_laps(laps)
    all_pit_laps.update(pit_laps)

    # Continuous line (without gaps at pit laps)
    fig.add_trace(go.Scatter(
        x=valid['LapNumber'],
        y=valid['LapTime(s)'],
        mode='lines',
        name=drv,
        line=dict(color=drv_color, width=2),
        showlegend=True,
        hoverinfo='skip',
        legendgroup=drv,
    ))

    # Scatter points colored by tyre compound
    for compound in valid['Compound'].dropna().unique():
        comp_laps = valid[valid['Compound'] == compound]
        comp_color = TYRE_COLORS.get(str(compound).upper(), TYRE_COLORS['UNKNOWN'])

        fig.add_trace(go.Scatter(
            x=comp_laps['LapNumber'],
            y=comp_laps['LapTime(s)'],
            mode='markers',
            name=f"{compound}",
            legendgroup=f"tyre_{compound}",
            legendgrouptitle_text="" if idx > 0 else None,
            showlegend=(idx == 0),  # Show tyre legend only once
            marker=dict(
                color=comp_color,
                size=7,
                line=dict(color=drv_color, width=1.5),
            ),
            text=[format_laptime(t) for t in comp_laps['LapTime(s)']],
            customdata=list(zip(
                comp_laps['LapNumber'],
                comp_laps['TyreLife'].fillna(0).astype(int),
                comp_laps['Compound'],
                [drv] * len(comp_laps),
            )),
            hovertemplate=(
                "<b>%{customdata[3]}</b>  Lap %{customdata[0]}<br>"
                "Time: <b>%{text}</b><br>"
                "Tyre: %{customdata[2]}  (life: %{customdata[1]} laps)<br>"
                "<extra></extra>"
            ),
        ))

# Pit stop vertical lines
for pit_lap in sorted(all_pit_laps):
    fig.add_vline(
        x=pit_lap + 0.5,
        line_dash="dot",
        line_color="#555555",
        line_width=1,
        annotation_text="PIT",
        annotation_position="top",
        annotation_font_color="#777777",
        annotation_font_size=9,
    )

fig.update_layout(
    plot_bgcolor='#1a1a1a',
    paper_bgcolor='#1a1a1a',
    font=dict(color='#ffffff', family='Arial'),
    title=dict(
        text=f"{year}  {gp}  —  {session_type}",
        font=dict(size=16, color='#cccccc'),
        x=0.0,
        xanchor='left',
    ),
    xaxis=dict(
        title='Lap Number',
        gridcolor='#2a2a2a',
        showgrid=True,
        zeroline=False,
        tickfont=dict(color='#aaaaaa'),
        title_font=dict(color='#aaaaaa'),
    ),
    yaxis=dict(
        title='Lap Time (s)',
        gridcolor='#2a2a2a',
        showgrid=True,
        zeroline=False,
        tickfont=dict(color='#aaaaaa'),
        title_font=dict(color='#aaaaaa'),
        tickformat='.1f',
    ),
    legend=dict(
        bgcolor='#242424',
        bordercolor='#3a3a3a',
        borderwidth=1,
        font=dict(color='#cccccc', size=11),
        groupclick='toggleitem',
    ),
    hovermode='closest',
    height=480,
    margin=dict(l=60, r=30, t=50, b=50),
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# ============================================================
# TELEMETRY COMPARISON
# ============================================================
st.markdown('<div class="section-header">Telemetry Comparison</div>', unsafe_allow_html=True)

with st.expander("ラップを選択してテレメトリーを表示", expanded=False):
    st.caption("※ テレメトリーデータのロードには数十秒かかる場合があります。")

    telem_cols = st.columns(len(selected_drivers))
    selected_telem_laps: dict[str, int] = {}

    for idx, drv in enumerate(selected_drivers):
        valid_lap_numbers = sorted(
            all_laps[drv].dropna(subset=['LapTime(s)'])['LapNumber'].astype(int).tolist()
        )
        with telem_cols[idx]:
            lap_num = st.selectbox(
                f"{drv} — Lap",
                options=valid_lap_numbers,
                key=f"telem_{drv}",
            )
            selected_telem_laps[drv] = lap_num

    if st.button("📡  テレメトリーをロード", type="primary"):
        with st.spinner("テレメトリーデータを読み込んでいます..."):
            telem_session = load_session_with_telemetry(year, gp, session_type)

        if telem_session:
            telem_fig = make_subplots(
                rows=3, cols=1,
                subplot_titles=('Speed (km/h)', 'Throttle (%)', 'Brake'),
                shared_xaxes=True,
                vertical_spacing=0.06,
            )

            telem_data: dict[str, pd.DataFrame] = {}

            for idx, drv in enumerate(selected_drivers):
                drv_color = DRIVER_COLORS[idx % len(DRIVER_COLORS)]
                lap_num = selected_telem_laps[drv]
                try:
                    drv_lap = (
                        telem_session.laps
                        .pick_driver(drv)
                        .query(f'LapNumber == {lap_num}')
                        .iloc[0]
                    )
                    tel = drv_lap.get_telemetry()
                    if tel is not None and len(tel) > 0:
                        telem_data[drv] = tel
                        kw = dict(line=dict(color=drv_color, width=1.5))
                        telem_fig.add_trace(
                            go.Scatter(x=tel['Distance'], y=tel['Speed'],
                                       name=drv, legendgroup=drv, **kw),
                            row=1, col=1,
                        )
                        telem_fig.add_trace(
                            go.Scatter(x=tel['Distance'], y=tel['Throttle'],
                                       name=drv, legendgroup=drv, showlegend=False, **kw),
                            row=2, col=1,
                        )
                        telem_fig.add_trace(
                            go.Scatter(x=tel['Distance'], y=tel['Brake'].astype(int),
                                       name=drv, legendgroup=drv, showlegend=False, **kw),
                            row=3, col=1,
                        )
                except (IndexError, Exception) as e:
                    st.warning(f"{drv} Lap {lap_num} のテレメトリー取得に失敗: {e}")

            telem_fig.update_layout(
                plot_bgcolor='#1a1a1a',
                paper_bgcolor='#1a1a1a',
                font=dict(color='#ffffff'),
                height=650,
                title=dict(
                    text="Telemetry — " + "  vs  ".join(
                        f"{d} (Lap {selected_telem_laps[d]})" for d in selected_drivers
                    ),
                    font=dict(size=14, color='#cccccc'),
                ),
                legend=dict(
                    bgcolor='#242424',
                    bordercolor='#3a3a3a',
                    borderwidth=1,
                    font=dict(color='#cccccc'),
                ),
                margin=dict(l=60, r=30, t=60, b=50),
            )
            for i in range(1, 4):
                telem_fig.update_yaxes(gridcolor='#2a2a2a', tickfont=dict(color='#aaaaaa'), row=i, col=1)
                telem_fig.update_xaxes(gridcolor='#2a2a2a', tickfont=dict(color='#aaaaaa'), row=i, col=1)
            telem_fig.update_xaxes(title_text='Distance (m)', title_font=dict(color='#aaaaaa'), row=3, col=1)

            st.plotly_chart(telem_fig, use_container_width=True)

            # ---- Track Map ----
            drivers_with_xy = [
                d for d in selected_drivers
                if d in telem_data
                and 'X' in telem_data[d].columns
                and 'Y' in telem_data[d].columns
            ]
            if drivers_with_xy:
                st.markdown(
                    '<div class="section-header" style="margin-top:16px;">Track Map — Speed</div>',
                    unsafe_allow_html=True,
                )
                track_cols = st.columns(len(drivers_with_xy))
                for idx, drv in enumerate(drivers_with_xy):
                    tel = telem_data[drv]
                    lap_num = selected_telem_laps[drv]

                    track_fig = go.Figure()
                    track_fig.add_trace(go.Scatter(
                        x=tel['X'],
                        y=tel['Y'],
                        mode='markers',
                        marker=dict(
                            color=tel['Speed'],
                            colorscale='RdYlGn',
                            size=4,
                            colorbar=dict(
                                title='km/h',
                                thickness=12,
                                title_font=dict(color='#aaaaaa', size=11),
                                tickfont=dict(color='#aaaaaa'),
                            ),
                            showscale=True,
                        ),
                        hovertemplate='Speed: %{marker.color:.0f} km/h<extra></extra>',
                    ))
                    track_fig.update_layout(
                        plot_bgcolor='#1a1a1a',
                        paper_bgcolor='#1a1a1a',
                        height=380,
                        title=dict(
                            text=f"{drv} — Lap {lap_num}",
                            font=dict(color='#cccccc', size=13),
                            x=0.0,
                            xanchor='left',
                        ),
                        xaxis=dict(
                            showgrid=False,
                            zeroline=False,
                            showticklabels=False,
                            scaleanchor='y',
                            scaleratio=1,
                        ),
                        yaxis=dict(
                            showgrid=False,
                            zeroline=False,
                            showticklabels=False,
                        ),
                        margin=dict(l=10, r=70, t=40, b=10),
                    )
                    with track_cols[idx]:
                        st.plotly_chart(track_fig, use_container_width=True)
            elif telem_data:
                st.info("このセッションのテレメトリーにはX/Y座標データが含まれていないため、トラックマップを表示できません。")

st.divider()

# ============================================================
# RAW LAP DATA
# ============================================================
st.markdown('<div class="section-header">Raw Lap Data</div>', unsafe_allow_html=True)

tabs = st.tabs(selected_drivers)
for tab, drv in zip(tabs, selected_drivers):
    with tab:
        display = all_laps[drv].copy()
        display['LapTime'] = display['LapTime'].apply(laptime_td_to_str)
        st.dataframe(
            display[['LapNumber', 'LapTime', 'Compound', 'TyreLife', 'Stint']],
            hide_index=True,
            use_container_width=True,
        )
