"""
MotoQuant Pro — Simulation UI
==============================
Run with:
    cd "Vehicle Dynamics"
    streamlit run app.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import copy
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MotoQuant Pro",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stSidebar"]  { background: #0e0e0e; }
[data-testid="stSidebar"] label { color: #ccc !important; }
[data-testid="stSidebar"] p     { color: #ccc !important; }
.mq-card {
    background: #161622; border: 1px solid #e94560;
    border-radius: 8px; padding: 14px 18px; text-align: center; margin-bottom: 6px;
}
.mq-card .lbl  { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
.mq-card .val  { font-size: 34px; font-weight: 800; color: #e94560; line-height: 1.1; }
.mq-card .unit { font-size: 13px; color: #aaa; }
.mq-faster { color: #2ecc71 !important; }
.mq-slower { color: #e74c3c !important; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# DATA ACCESS  (all cached per session)
# ════════════════════════════════════════════════════════

_DB_PATH = os.path.join(os.path.dirname(__file__), "motoquant.db")


def _get_db():
    """Open a fresh DB connection — safe across Streamlit's thread pool."""
    from motoquant.database.connection import MotoQuantDB
    db = MotoQuantDB(_DB_PATH)
    db.connect()
    return db


def _conn():
    return _get_db().connect()


@st.cache_data
def fetch_bike_list():
    """Return sorted list of dicts: id, label, mfr, model, year."""
    conn = _conn()
    rows = conn.execute("""
            SELECT bc.id             AS cfg_id,
                   mfr.name          AS mfr,
                   bm.model_name     AS model,
                   bm.model_code,
                   bm.year_from,
                   bc.config_name,
                   bm.category
            FROM   bike_configs  bc
            JOIN   bike_models   bm  ON bm.id = bc.bike_model_id
            JOIN   manufacturers mfr ON mfr.id = bm.manufacturer_id
            WHERE  bc.is_current = 1
            ORDER  BY mfr.name, bm.model_name, bm.year_from
        """).fetchall()
    out = []
    for r in rows:
        mfr   = r["mfr"]   or "?"
        model = r["model"] or "?"
        yr    = f" ({r['year_from']})" if r["year_from"] else ""
        tag   = f" [{r['config_name']}]" if r["config_name"] not in ("stock", None) else ""
        out.append({
            "id":    r["cfg_id"],
            "label": f"{mfr} {model}{yr}{tag}",
            "mfr":   mfr,
            "model": model,
        })
    out.sort(key=lambda x: x["label"])
    return out


@st.cache_data
def fetch_venue_list():
    conn = _conn()
    rows = conn.execute(
        "SELECT * FROM venues WHERE is_active = 1 ORDER BY name"
    ).fetchall()
    return [dict(r) for r in rows]


def load_config(cfg_id: int, env=None):
    return _get_db().bikes.to_config(cfg_id, environment=env)


def load_env(venue_id: int):
    return _get_db().venues.to_environment(venue_id)


# ════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("## 🏍️ MotoQuant Pro")
    st.caption("First-principles drag racing engine")
    st.markdown("---")

    bikes  = fetch_bike_list()
    venues = fetch_venue_list()

    if not bikes:
        st.error("No bikes in DB.\n\n`python -m motoquant.run import --known-bikes`")
        st.stop()

    # ── Bike A ────────────────────────────────────────────────────────────────
    st.markdown("### 🔴 Bike A")
    b_labels = [b["label"] for b in bikes]
    b_idx = st.selectbox("Select bike", range(len(b_labels)),
                         format_func=lambda i: b_labels[i], key="bA")
    sel_a = bikes[b_idx]

    st.caption("Tuning overrides")
    col1, col2 = st.columns(2)
    pwr_a  = col1.slider("Power %", 70, 150, 100, key="pA",
                          help="Scale engine output — simulate tune or detuning")
    mass_a = col2.slider("Mass Δkg", -30, 30, 0, key="mA",
                          help="Add/remove mass vs stock")

    # ── Compare toggle ────────────────────────────────────────────────────────
    st.markdown("---")
    compare = st.toggle("📊 Compare two bikes", value=False)
    sel_b, pwr_b, mass_b = None, 100, 0
    if compare:
        st.markdown("### 🔵 Bike B")
        b2_idx = st.selectbox("Select bike B", range(len(b_labels)),
                              format_func=lambda i: b_labels[i],
                              index=min(1, len(b_labels)-1), key="bB")
        sel_b = bikes[b2_idx]
        col3, col4 = st.columns(2)
        pwr_b  = col3.slider("Power %", 70, 150, 100, key="pB")
        mass_b = col4.slider("Mass Δkg", -30, 30, 0, key="mB")

    # ── Venue ─────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📍 Venue")
    if not venues:
        st.warning("No venues in DB.")
        venue_id = None
    else:
        v_labels = [v["name"] for v in venues]
        v_idx = st.selectbox("Venue", range(len(v_labels)),
                             format_func=lambda i: v_labels[i], key="vsel")
        venue_id = venues[v_idx]["id"]
        v = venues[v_idx]
        st.caption(f"📍 {v.get('city','')}, {v.get('state','')}  ·  "
                   f"Alt {v.get('altitude_m',0):.0f} m  ·  {v.get('surface_type','asphalt')}")

    # ── Conditions ────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🌡 Conditions")
    c1, c2 = st.columns(2)
    t_amb   = c1.number_input("Air temp °C",    value=25.0, min_value=0.0,  max_value=55.0, step=1.0)
    t_track = c2.number_input("Track temp °C",  value=30.0, min_value=15.0, max_value=65.0, step=1.0)
    c3, c4 = st.columns(2)
    humid   = c3.number_input("Humidity %",     value=40, min_value=0, max_value=100, step=5)
    wind    = c4.number_input("Headwind km/h",  value=0.0, min_value=-30.0, max_value=30.0, step=1.0,
                              help="Positive = into you  |  Negative = tailwind")

    st.markdown("---")
    run_btn = st.button("▶  RUN SIMULATION", type="primary", use_container_width=True)


# ════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════

def make_env(venue_id, t_amb, t_track, humid, wind_kmh):
    from motoquant.models import EnvironmentParams
    env = load_env(venue_id) if venue_id else EnvironmentParams()
    env.ambient_temp_c          = float(t_amb)
    env.track_temp_c            = float(t_track)
    env.relative_humidity_pct   = float(humid)
    env.wind_speed_ms           = abs(wind_kmh / 3.6)
    env.wind_direction_deg      = 0.0 if wind_kmh >= 0 else 180.0
    return env


def tune_config(cfg, pwr_pct, mass_delta):
    cfg = copy.deepcopy(cfg)
    if pwr_pct != 100:
        f = pwr_pct / 100.0
        cfg.engine.peak_power_hp *= f
        if cfg.engine.dyno_curve is not None:
            cfg.engine.dyno_curve.torque_nm = cfg.engine.dyno_curve.torque_nm * f
    if mass_delta != 0:
        cfg.chassis.dry_mass_kg += mass_delta
    return cfg


def simulate(cfg):
    from motoquant import MotoQuantEngine
    return MotoQuantEngine(cfg).run()


def card(col, label, value, unit):
    col.markdown(
        f'<div class="mq-card">'
        f'<div class="lbl">{label}</div>'
        f'<div class="val">{value}</div>'
        f'<div class="unit">{unit}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def splits_table(r, prefix=""):
    return pd.DataFrame({
        "Split": ["60 ft", "330 ft", "⅛ mile", "1000 ft", "¼ mile"],
        f"{prefix}Time (s)": [f"{r.time_60ft:.3f}", f"{r.time_330ft:.3f}",
                               f"{r.time_eighth:.3f}", f"{r.time_1000ft:.3f}",
                               f"{r.time_quarter:.3f}"],
        f"{prefix}Speed (km/h)": [f"{r.speed_60ft*3.6:.1f}", f"{r.speed_330ft*3.6:.1f}",
                                   f"{r.speed_eighth*3.6:.1f}", f"{r.speed_1000ft*3.6:.1f}",
                                   f"{r.speed_quarter*3.6:.1f}"],
    })


CHART_DARK = dict(paper_bgcolor="#0d0d0d", plot_bgcolor="#111111",
                  font=dict(color="#ccc", size=12), margin=dict(l=50,r=20,t=36,b=40))


def build_main_chart(ra, la, rb=None, lb=None):
    fig = make_subplots(rows=2, cols=2,
                         subplot_titles=("Speed  (km/h)", "Engine RPM",
                                         "Gear", "Traction  (%)"),
                         vertical_spacing=0.18, horizontal_spacing=0.1)
    def _add(r, label, color, dash="solid"):
        kw = dict(name=label, line=dict(color=color, width=2, dash=dash))
        fig.add_trace(go.Scatter(x=r.t, y=r.v*3.6,       **kw),                          row=1, col=1)
        fig.add_trace(go.Scatter(x=r.t, y=r.rpm,          **kw, showlegend=False),        row=1, col=2)
        fig.add_trace(go.Scatter(x=r.t, y=r.gear,
                                 name=label, showlegend=False,
                                 line=dict(color=color, width=2, dash=dash, shape="hv")), row=2, col=1)
        fig.add_trace(go.Scatter(x=r.t, y=r.traction_pct, **kw, showlegend=False),       row=2, col=2)

    _add(ra, la, "#e94560")
    if rb is not None:
        _add(rb, lb, "#00cfff", dash="dash")

    fig.update_xaxes(title_text="Time (s)", gridcolor="#2a2a2a")
    fig.update_yaxes(gridcolor="#2a2a2a")
    fig.update_yaxes(title_text="km/h", row=1, col=1)
    fig.update_yaxes(title_text="RPM",  row=1, col=2)
    fig.update_yaxes(title_text="Gear", row=2, col=1)
    fig.update_yaxes(title_text="%",    row=2, col=2)
    fig.update_layout(**CHART_DARK, height=460,
                      legend=dict(orientation="h", x=0.5, y=1.06, xanchor="center"))
    return fig


def build_extra_chart(ra, rb=None):
    fig = make_subplots(rows=1, cols=3,
                         subplot_titles=("Tire temp  (°C)", "Drive force  (N)", "Aero drag  (N)"),
                         horizontal_spacing=0.1)
    def _add(r, color, dash="solid"):
        kw = dict(showlegend=False, line=dict(color=color, width=2, dash=dash))
        fig.add_trace(go.Scatter(x=r.t, y=r.T_tire,  **kw), row=1, col=1)
        fig.add_trace(go.Scatter(x=r.t, y=r.F_drive, **kw), row=1, col=2)
        fig.add_trace(go.Scatter(x=r.t, y=r.F_drag,  **kw), row=1, col=3)
    _add(ra, "#e94560")
    if rb is not None:
        _add(rb, "#00cfff", dash="dash")
    fig.update_xaxes(title_text="Time (s)", gridcolor="#2a2a2a")
    fig.update_yaxes(gridcolor="#2a2a2a")
    fig.update_layout(**CHART_DARK, height=280)
    return fig


def spec_df(cfg):
    rows = [
        ("Peak power",    f"{cfg.engine.peak_power_hp:.0f} hp @ {cfg.engine.peak_power_rpm:.0f} rpm"),
        ("Peak torque",   f"{cfg.engine.peak_torque_nm:.0f} Nm @ {cfg.engine.peak_torque_rpm:.0f} rpm"),
        ("Displacement",  f"{cfg.engine.displacement_cc:.0f} cc"),
        ("Dry mass",      f"{cfg.chassis.dry_mass_kg:.1f} kg"),
        ("Total mass",    f"{cfg.chassis.total_mass_kg:.1f} kg"),
        ("Gears",         f"{cfg.drivetrain.num_gears}"),
        ("Redline",       f"{cfg.engine.redline_rpm:.0f} rpm"),
        ("Drivetrain η",  f"{cfg.drivetrain.drivetrain_efficiency()*100:.1f}%"),
        ("Cd·A",          f"{cfg.aero.cd_a_effective:.4f} m²"),
        ("Gear ratios",   "  ".join(f"{r:.3f}" for r in cfg.drivetrain.gear_ratios)),
        ("Final drive",   f"{cfg.drivetrain.final_drive_ratio:.3f}  "
                          f"({cfg.drivetrain.front_sprocket}T / {cfg.drivetrain.rear_sprocket}T)"),
    ]
    return pd.DataFrame(rows, columns=["Parameter", "Value"])


def cond_df(cfg):
    from motoquant.submodels import EnvironmentalModel
    em = EnvironmentalModel(cfg)
    s  = em.summary()
    rows = [
        ("Air density",       f"{s['rho_kg_m3']:.4f} kg/m³"),
        ("Density altitude",  f"{s['density_alt_ft']:.0f} ft"),
        ("Power correction",  f"{s['power_correction']:.4f}  ({s['da_power_loss_pct']:.2f}% loss)"),
        ("Headwind",          f"{s['v_headwind_ms']*3.6:.1f} km/h"),
        ("Grip multiplier",   f"{s['grip_multiplier']:.3f}"),
        ("RR multiplier",     f"{s['rr_multiplier']:.3f}"),
        ("Ambient temp",      f"{s['ambient_temp_c']:.1f} °C"),
        ("Track temp",        f"{s['track_temp_c']:.1f} °C"),
    ]
    return pd.DataFrame(rows, columns=["Condition", "Value"])


# ════════════════════════════════════════════════════════
# MAIN PANEL
# ════════════════════════════════════════════════════════

st.markdown("# 🏍️ MotoQuant Pro")
st.caption("First-principles motorcycle quarter-mile physics engine  ·  "
           "Aamby Valley · MMRT · BIC · Kari · Hyderabad")
st.markdown("---")

if not run_btn:
    # ── Welcome screen ────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    c1.info("**1 · Pick a bike**\nChoose any bike from the database. "
            "Adjust power % or mass Δ to simulate tuning.")
    c2.info("**2 · Set venue & conditions**\nPick a drag strip. "
            "Override temperature, humidity, and headwind.")
    c3.info("**3 · Run**\nHit **▶ RUN SIMULATION** to compute a full "
            "quarter-mile run with splits, charts, and traction data.")
    st.markdown("---")

    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("Bikes in DB", len(bikes))
    col_b.metric("Venues",      len(venues))
    try:
        conn = _conn()
        n_parts = conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0]
        n_tires = conn.execute("SELECT COUNT(*) FROM tire_models").fetchone()[0]
        col_c.metric("Parts",  n_parts)
        col_d.metric("Tires",  n_tires)
    except Exception:
        pass

    with st.expander("All bikes in database"):
        df_bikes = pd.DataFrame(bikes)[["label"]].rename(columns={"label": "Bike"})
        st.dataframe(df_bikes, use_container_width=True, hide_index=True)

else:
    # ════════════════════════════════════════════
    # SIMULATE
    # ════════════════════════════════════════════
    env = make_env(venue_id, t_amb, t_track, humid, wind)

    with st.spinner(f"Simulating {sel_a['label']}…"):
        try:
            cfg_a  = load_config(sel_a["id"], env)
            if cfg_a is None:
                st.error(f"Could not load config #{sel_a['id']} from DB.")
                st.stop()
            cfg_a  = tune_config(cfg_a, pwr_a, mass_a)
            res_a  = simulate(cfg_a)
        except Exception as ex:
            st.error(f"Simulation A failed: {ex}")
            st.exception(ex)
            st.stop()

    res_b, cfg_b = None, None
    lab_b = None
    if compare and sel_b:
        with st.spinner(f"Simulating {sel_b['label']}…"):
            try:
                cfg_b = load_config(sel_b["id"], env)
                if cfg_b:
                    cfg_b  = tune_config(cfg_b, pwr_b, mass_b)
                    res_b  = simulate(cfg_b)
                    lab_b  = sel_b["label"]
                    if pwr_b != 100 or mass_b != 0:
                        lab_b += f" ({pwr_b}%/{mass_b:+d}kg)"
            except Exception as ex:
                st.warning(f"Simulation B failed: {ex}")

    lab_a = sel_a["label"]
    if pwr_a != 100 or mass_a != 0:
        lab_a += f" ({pwr_a}%/{mass_a:+d}kg)"

    # ── Big metric cards ──────────────────────────────────────────────────────
    if compare and res_b:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f"#### 🔴 {lab_a}")
            mc1, mc2, mc3, mc4 = st.columns(4)
            card(mc1, "¼ Mile",   f"{res_a.time_quarter:.3f}", "s")
            card(mc2, "Trap",     f"{res_a.speed_quarter*3.6:.1f}", "km/h")
            card(mc3, "⅛ Mile",   f"{res_a.time_eighth:.3f}", "s")
            card(mc4, "60 ft",    f"{res_a.time_60ft:.3f}", "s")
        with col_right:
            st.markdown(f"#### 🔵 {lab_b}")
            mc5, mc6, mc7, mc8 = st.columns(4)
            card(mc5, "¼ Mile",   f"{res_b.time_quarter:.3f}", "s")
            card(mc6, "Trap",     f"{res_b.speed_quarter*3.6:.1f}", "km/h")
            card(mc7, "⅛ Mile",   f"{res_b.time_eighth:.3f}", "s")
            card(mc8, "60 ft",    f"{res_b.time_60ft:.3f}", "s")

        dt = res_b.time_quarter - res_a.time_quarter
        dv = (res_b.speed_quarter - res_a.speed_quarter) * 3.6
        cls_dt = "mq-faster" if dt > 0 else "mq-slower"
        winner = lab_a if dt > 0 else lab_b
        st.markdown(
            f'<p style="text-align:center;font-size:18px;">'
            f'Δ ET = <span class="{cls_dt}">{dt:+.3f} s</span>  ·  '
            f'Δ Trap = {dv:+.1f} km/h  ·  <b>{winner}</b> wins</p>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"#### {lab_a}")
        mc1, mc2, mc3, mc4 = st.columns(4)
        card(mc1, "Quarter Mile ET", f"{res_a.time_quarter:.3f}", "seconds")
        card(mc2, "Trap Speed",      f"{res_a.speed_quarter*3.6:.1f}", "km/h")
        card(mc3, "⅛ Mile ET",       f"{res_a.time_eighth:.3f}", "seconds")
        card(mc4, "60 ft",           f"{res_a.time_60ft:.3f}", "seconds")

    st.markdown("---")

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Charts", "⏱ Splits", "🔧 Specs", "🌤 Conditions"])

    with tab1:
        st.plotly_chart(build_main_chart(res_a, lab_a, res_b, lab_b),
                        use_container_width=True)
        with st.expander("Detailed channels — tire temp · drive force · aero drag"):
            st.plotly_chart(build_extra_chart(res_a, res_b), use_container_width=True)

    with tab2:
        if compare and res_b:
            df_a = splits_table(res_a, "A · ")
            df_b = splits_table(res_b, "B · ")
            df_m = df_a.merge(df_b, on="Split")
            st.dataframe(df_m, use_container_width=True, hide_index=True)
        else:
            st.dataframe(splits_table(res_a), use_container_width=True, hide_index=True)

    with tab3:
        if compare and cfg_b:
            col_l, col_r = st.columns(2)
            with col_l:
                st.caption(f"🔴 {lab_a}")
                st.dataframe(spec_df(cfg_a), use_container_width=True, hide_index=True)
            with col_r:
                st.caption(f"🔵 {lab_b}")
                st.dataframe(spec_df(cfg_b), use_container_width=True, hide_index=True)
        else:
            st.dataframe(spec_df(cfg_a), use_container_width=True, hide_index=True)

    with tab4:
        venue_name = venues[v_idx]["name"] if venue_id else "Custom"
        st.caption(f"📍 {venue_name}  ·  {t_amb}°C  ·  {humid}% RH  ·  "
                   f"Headwind {wind} km/h  ·  Track {t_track}°C")
        st.dataframe(cond_df(cfg_a), use_container_width=True, hide_index=True)
