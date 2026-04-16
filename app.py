"""
MotoQuant Pro — Simulation UI
==============================
Run with:
    cd "Vehicle Dynamics"
    streamlit run app.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import copy, json
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MotoQuant Pro",
    page_icon="🏍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ────────────────────────────────────────────────────────────────
# Design system matches motoquant.in landing page:
#   Background  #050508   Surface    #0d0d12   Surface-2  #121219
#   Border      #1e1e2a   Text-1     #e8e8f0   Text-2     #7878a0
#   Orange      #f97316   Orange-dim #f9731618  Blue      #60a5fa
#   Green       #22c55e   Red        #ef4444
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

/* ── Reset & base ───────────────────────────────────────────────────────── */
html, body, [class*="css"]  { font-family:'Inter',sans-serif !important; }
[data-testid="stAppViewContainer"] { background:#050508; }
.main .block-container       { padding-top:1.2rem; padding-bottom:3rem; max-width:1480px; }

/* Hide Streamlit chrome */
#MainMenu, footer, [data-testid="stToolbar"],
[data-testid="stDecoration"]          { display:none !important; }
[data-testid="stHeader"]              { background:transparent !important; }

/* ── Sidebar ────────────────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background:#08080e;
    border-right:1px solid #1a1a26;
}
[data-testid="stSidebar"] > div:first-child { padding-top:1rem; }

/* Sidebar inputs */
[data-testid="stSidebar"] input,
[data-testid="stSidebar"] textarea {
    background:#0f0f18 !important;
    border:1px solid #222230 !important;
    border-radius:7px !important;
    color:#dde0f0 !important;
    font-size:13px !important;
}
[data-testid="stSidebar"] input:focus,
[data-testid="stSidebar"] textarea:focus {
    border-color:#f97316 !important;
    box-shadow:0 0 0 2px #f9731618 !important;
}
[data-testid="stSidebar"] label { color:#7878a0 !important; font-size:11.5px !important; font-weight:500 !important; }
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] small { color:#7878a0 !important; }
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div {
    background:#0f0f18 !important;
    border-color:#222230 !important;
    color:#dde0f0 !important;
    border-radius:7px !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] {
    background:#0c0c16;
    border:1px solid #1e1e2a !important;
    border-radius:8px !important;
}

/* Sidebar slider */
[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stThumbValue"] { color:#f97316 !important; }
[data-testid="stSidebar"] [role="slider"] { background:#f97316 !important; }

/* Sidebar section heading (bold label) */
[data-testid="stSidebar"] strong { color:#c0c0d8 !important; font-weight:600 !important; }

/* ── Metric cards ───────────────────────────────────────────────────────── */
.mq-card {
    background:#0d0d14;
    border:1px solid #1e1e2a;
    border-radius:10px;
    padding:14px 10px 12px;
    text-align:center;
    position:relative;
    overflow:hidden;
    margin-bottom:6px;
}
/* Coloured top bar */
.mq-card::after {
    content:''; position:absolute; top:0; left:0; right:0; height:3px;
    background:#2a2a38; border-radius:10px 10px 0 0;
}
.mq-card-a::after { background:linear-gradient(90deg,#f97316,#fb923c); }
.mq-card-b::after { background:linear-gradient(90deg,#3b82f6,#60a5fa); }

.mq-card .lbl {
    font-size:9px; font-weight:700; color:#3a3a52;
    text-transform:uppercase; letter-spacing:1.8px; margin-bottom:5px;
}
.mq-card .val {
    font-family:'JetBrains Mono','Inter',monospace;
    font-size:30px; font-weight:600; color:#e8e8f0;
    line-height:1; font-variant-numeric:tabular-nums;
}
.mq-card-a .val { color:#fb923c; }
.mq-card-b .val { color:#93c5fd; }
.mq-card .unit { font-size:10px; color:#3a3a52; margin-top:4px; letter-spacing:0.5px; }

/* ── Stat tiles (welcome screen) ────────────────────────────────────────── */
.mq-stat {
    background:#0a0a12; border:1px solid #1a1a26; border-radius:12px;
    padding:24px 16px; text-align:center; transition:border-color 0.2s;
}
.mq-stat:hover { border-color:#2a2a3a; }
.mq-stat .s-num {
    font-family:'JetBrains Mono',monospace;
    font-size:42px; font-weight:600; color:#f97316; line-height:1;
    letter-spacing:-1px;
}
.mq-stat .s-lbl {
    font-size:11px; color:#3a3a52; text-transform:uppercase;
    letter-spacing:1.5px; margin-top:6px; font-weight:600;
}

/* ── Delta banner ───────────────────────────────────────────────────────── */
.mq-delta {
    background:linear-gradient(135deg,#0c0c14 0%,#0f0f1a 100%);
    border:1px solid #f9731628;
    border-radius:10px; padding:14px 24px;
    text-align:center; margin:12px 0;
    font-size:14px; color:#7878a0;
}
.mq-faster { color:#22c55e !important; font-weight:700; }
.mq-slower { color:#ef4444 !important; font-weight:700; }

/* ── Section dividers ───────────────────────────────────────────────────── */
.mq-sec {
    font-size:9.5px; font-weight:700; color:#2e2e42;
    text-transform:uppercase; letter-spacing:2.5px;
    padding:10px 0 5px; border-bottom:1px solid #141420;
    margin-bottom:12px;
}
hr { border:none; border-top:1px solid #141420 !important; margin:14px 0 !important; }

/* ── Build badges (A / B) ───────────────────────────────────────────────── */
.badge-a {
    display:inline-block; background:#f9731614;
    border:1px solid #f9731640; color:#fb923c;
    border-radius:5px; padding:2px 9px; font-size:11px;
    font-weight:700; margin-right:6px; letter-spacing:0.5px;
}
.badge-b {
    display:inline-block; background:#3b82f614;
    border:1px solid #3b82f640; color:#93c5fd;
    border-radius:5px; padding:2px 9px; font-size:11px;
    font-weight:700; margin-right:6px; letter-spacing:0.5px;
}

/* ── Part chips ─────────────────────────────────────────────────────────── */
.part-chip {
    display:inline-block; background:#0f0f1a;
    border:1px solid #22222e; border-radius:16px;
    padding:3px 10px; font-size:11px; color:#6868a0;
    margin:2px 2px; line-height:1.6;
}

/* ── Tabs ───────────────────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background:#0a0a12; border-radius:8px; padding:4px; gap:2px;
    border:1px solid #1a1a26;
}
.stTabs [data-baseweb="tab"] {
    background:transparent; border-radius:6px;
    color:#4a4a68; font-size:13px; font-weight:500; padding:6px 16px;
}
.stTabs [aria-selected="true"] {
    background:#141420 !important; color:#fb923c !important;
    font-weight:600 !important;
}

/* ── Primary button ─────────────────────────────────────────────────────── */
[data-testid="baseButton-primary"] {
    background:linear-gradient(135deg,#f97316 0%,#ea6c0c 100%) !important;
    border:none !important; font-weight:700 !important; color:#fff !important;
    border-radius:8px !important; height:48px !important;
    font-size:14px !important; letter-spacing:0.5px !important;
    box-shadow:0 4px 16px #f9731628 !important;
    transition:all 0.15s !important;
}
[data-testid="baseButton-primary"]:hover {
    transform:translateY(-1px) !important;
    box-shadow:0 6px 20px #f9731640 !important;
}
[data-testid="baseButton-primary"]:active { transform:translateY(0) !important; }

/* ── Expander ───────────────────────────────────────────────────────────── */
[data-testid="stExpander"] {
    background:#09090f; border:1px solid #1a1a26 !important;
    border-radius:8px !important;
}
[data-testid="stExpander"] summary { font-size:13px; font-weight:600; color:#8888a8; }
[data-testid="stExpander"] summary:hover { color:#c0c0d8; }

/* ── Dataframe / table ──────────────────────────────────────────────────── */
[data-testid="stDataFrame"] { border:1px solid #1a1a26; border-radius:8px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)


# ════════════════════════════════════════════════════════
# DATA ACCESS
# ════════════════════════════════════════════════════════

_DB_PATH = os.path.join(os.path.dirname(__file__), "motoquant.db")


def _get_db():
    from motoquant.database.connection import MotoQuantDB
    db = MotoQuantDB(_DB_PATH)
    db.connect()
    return db


def _conn():
    return _get_db().connect()


@st.cache_data
def fetch_bike_list():
    conn = _conn()
    rows = conn.execute("""
        SELECT bc.id AS cfg_id, bc.bike_model_id AS model_id,
               mfr.name AS mfr, bm.model_name AS model,
               bm.year_from, bc.config_name, bm.category
        FROM   bike_configs bc
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
            "id":       r["cfg_id"],
            "model_id": r["model_id"],
            "label":    f"{mfr} {model}{yr}{tag}",
            "mfr":      mfr,
            "model":    model,
            "category": r["category"] or "sport",
        })
    out.sort(key=lambda x: x["label"])
    return out


@st.cache_data
def fetch_venue_list():
    conn = _conn()
    rows = conn.execute("SELECT * FROM venues WHERE is_active=1 ORDER BY name").fetchall()
    return [dict(r) for r in rows]


@st.cache_data
def fetch_db_stats():
    conn = _conn()
    return {
        "bikes":  conn.execute("SELECT COUNT(*) FROM bike_models").fetchone()[0],
        "tires":  conn.execute("SELECT COUNT(*) FROM tire_models").fetchone()[0],
        "parts":  conn.execute("SELECT COUNT(*) FROM parts").fetchone()[0],
        "venues": conn.execute("SELECT COUNT(*) FROM venues").fetchone()[0],
    }


@st.cache_data
def fetch_parts_catalog():
    """All parts grouped by category, sorted by price."""
    conn = _conn()
    rows = conn.execute("""
        SELECT p.id, pc.name AS category, p.brand, p.model_name,
               p.price_inr, p.availability,
               p.param_overrides, p.param_deltas, p.param_multipliers,
               p.specifications
        FROM   parts p
        JOIN   parts_categories pc ON pc.id = p.category_id
        ORDER  BY pc.name, p.price_inr
    """).fetchall()

    catalog = {}   # {category: [part_dict, ...]}
    for r in rows:
        cat = r["category"]
        overrides  = json.loads(r["param_overrides"])  if r["param_overrides"]  else {}
        deltas     = json.loads(r["param_deltas"])     if r["param_deltas"]     else {}
        mults      = json.loads(r["param_multipliers"]) if r["param_multipliers"] else {}
        effects    = {**deltas, **overrides, **mults}   # unified view for display

        catalog.setdefault(cat, []).append({
            "id":          r["id"],
            "category":    cat,
            "brand":       r["brand"]      or "?",
            "model_name":  r["model_name"] or "?",
            "price_inr":   r["price_inr"]  or 0,
            "availability": r["availability"] or "in_stock",
            "param_overrides":  overrides,
            "param_deltas":     deltas,
            "param_multipliers": mults,
            "effects":     effects,
            "label":       f"{r['brand']} {r['model_name']}",
        })
    return catalog


def filter_parts_for_bike(catalog: dict, bike: dict) -> dict:
    """
    Return a copy of catalog with only parts that are compatible with the given bike.

    Filtering rules (in priority order):
    1. Sprockets / chains: 520-pitch parts excluded for Hayabusa (530 bike);
       530-pitch parts excluded for everything else.
    2. ECU flashes from Woolich: shown only if the part name contains words from
       the bike's model name (e.g. "K5/K6", "Hayabusa", "YZF-R1").
    3. Everything else: show always (exhausts, clutch, suspension etc. are either
       labelled universal or can be adapted; user can verify fitment).
    """
    label_lc = bike["label"].lower()
    model_lc = bike["model"].lower()
    mfr_lc   = bike["mfr"].lower()

    # Bikes that use 530-pitch chain (add more if catalog grows)
    is_530_bike = "hayabusa" in label_lc

    # Significant model keywords for ECU-flash matching (≥4 chars, non-generic)
    _stop = {"racing","stage","flash","flash","full","system","the","and","for"}
    model_kws = [w for w in model_lc.replace("/","  ").replace("-"," ").split()
                 if len(w) >= 3 and w not in _stop]

    filtered = {}
    for cat, parts in catalog.items():
        kept = []
        for p in parts:
            pname_lc = p["model_name"].lower()
            brand_lc = p["brand"].lower()

            # ── Chain-pitch filtering ──────────────────────────────────────
            if cat in ("sprocket", "chain"):
                has_520 = "520" in pname_lc
                has_530 = "530" in pname_lc
                if has_530 and not is_530_bike:
                    continue   # 530 part on a non-530 bike
                if has_520 and is_530_bike:
                    continue   # 520 part on a 530 bike

            # ── ECU flash: model-specific Woolich flashes ──────────────────
            if cat == "ecu" and "woolich" in brand_lc:
                if not any(kw in pname_lc for kw in model_kws):
                    continue   # This Woolich flash is for a different bike model

            kept.append(p)

        if kept:
            filtered[cat] = kept

    return filtered


def summarise_part_effects(part_ids: list, catalog: dict) -> dict:
    """
    Given selected part IDs, return a merged dict of net numeric changes:
    { "engine.peak_power_hp": +14.0, "chassis.dry_mass_kg": -2.5, ... }
    Boolean overrides (two_step, nitrous_active, etc.) tracked separately.
    """
    flat = {p["id"]: p for parts in catalog.values() for p in parts}
    net   = {}   # numeric
    flags = {}   # boolean overrides
    for pid in part_ids:
        p = flat.get(pid)
        if not p:
            continue
        for k, v in p["param_deltas"].items():
            net[k] = net.get(k, 0) + v
        for k, v in p["param_overrides"].items():
            if isinstance(v, bool):
                flags[k] = v
            else:
                net[k] = v          # overrides just replace
        for k, v in p["param_multipliers"].items():
            net[k] = net.get(k, 1.0) * v   # crude — multiply multipliers
    return net, flags


def load_config(cfg_id, env=None):
    return _get_db().bikes.to_config(cfg_id, environment=env)


def load_env(venue_id):
    return _get_db().venues.to_environment(venue_id)


@st.cache_data
def fetch_tires_for_bike(bike_model_id, position):
    """OEM-fitted tires first, then all others. Returns (fitted_list, others_list)."""
    conn = _conn()
    fitted = conn.execute("""
        SELECT tm.id, tm.model_name, tm.size_designation, tm.compound_type,
               tm.mu_peak, tm.price_inr, COALESCE(mfr.name,'Unknown') AS brand
        FROM   bike_tire_fitments f
        JOIN   tire_models tm          ON tm.id = f.tire_model_id
        LEFT   JOIN tire_manufacturers mfr ON mfr.id = tm.manufacturer_id
        WHERE  f.bike_model_id=? AND f.position=?
        ORDER  BY tm.mu_peak DESC
    """, (bike_model_id, position)).fetchall()
    fitted_ids = {r["id"] for r in fitted}

    others = conn.execute("""
        SELECT tm.id, tm.model_name, tm.size_designation, tm.compound_type,
               tm.mu_peak, tm.price_inr, COALESCE(mfr.name,'Unknown') AS brand
        FROM   tire_models tm
        LEFT   JOIN tire_manufacturers mfr ON mfr.id = tm.manufacturer_id
        ORDER  BY tm.compound_type, tm.mu_peak DESC
    """).fetchall()

    def _label(r): return (f"{r['brand']} {r['model_name']} — "
                           f"{r['size_designation']}  [{r['compound_type']}]  μ={r['mu_peak']:.2f}"
                           + (f"  ₹{r['price_inr']:.0f}" if r['price_inr'] else ""))
    fitted_out = [{"id": r["id"], "label": _label(r), "fitted": True}  for r in fitted]
    others_out = [{"id": r["id"], "label": _label(r), "fitted": False}
                  for r in others if r["id"] not in fitted_ids]
    return fitted_out, others_out


def apply_tire_override(cfg, front_id, rear_id, db):
    if not front_id and not rear_id:
        return cfg
    cfg  = copy.deepcopy(cfg)
    conn = db.connect()
    if rear_id:
        t = conn.execute("SELECT * FROM tire_models WHERE id=?", (rear_id,)).fetchone()
        if t:
            if t["mu_peak"]:          cfg.tires.mu_peak                = t["mu_peak"]
            if t["pacejka_B"]:        cfg.tires.pacejka_B              = t["pacejka_B"]
            if t["pacejka_C"]:        cfg.tires.pacejka_C              = t["pacejka_C"]
            if t["pacejka_D"]:        cfg.tires.pacejka_D              = t["pacejka_D"]
            if t["pacejka_E"]:        cfg.tires.pacejka_E              = t["pacejka_E"]
            if t["optimal_temp_c"]:   cfg.tires.optimal_temp_c         = t["optimal_temp_c"]
            if t["rolling_radius_m"]: cfg.tires.rear_rolling_radius_m  = t["rolling_radius_m"]
    if front_id:
        t = conn.execute("SELECT * FROM tire_models WHERE id=?", (front_id,)).fetchone()
        if t and t["rolling_radius_m"]:
            cfg.tires.front_rolling_radius_m = t["rolling_radius_m"]
    return cfg


def apply_parts(cfg, part_ids):
    """Apply a list of part IDs to cfg via bridge.apply_part_to_config. Returns new cfg."""
    if not part_ids:
        return cfg
    from motoquant.database.bridge import apply_part_to_config
    conn = _conn()
    for pid in part_ids:
        row = conn.execute("SELECT * FROM parts WHERE id=?", (pid,)).fetchone()
        if row:
            cfg = apply_part_to_config(cfg, dict(row))
    return cfg


def get_tire_label(tire_id):
    if not tire_id:
        return None
    conn = _conn()
    t = conn.execute("""SELECT tm.model_name, tm.size_designation, tm.compound_type,
                               tm.mu_peak, tm.price_inr,
                               COALESCE(mfr.name,'Unknown') AS brand
                        FROM tire_models tm
                        LEFT JOIN tire_manufacturers mfr ON mfr.id=tm.manufacturer_id
                        WHERE tm.id=?""", (tire_id,)).fetchone()
    if t:
        lbl = f"{t['brand']} {t['model_name']} {t['size_designation']} [{t['compound_type']}]  μ={t['mu_peak']:.2f}"
        if t['price_inr']:
            lbl += f"  ₹{t['price_inr']:.0f}"
        return lbl
    return None


# ════════════════════════════════════════════════════════
# SIDEBAR WIDGETS
# ════════════════════════════════════════════════════════

def _sec(label):
    st.markdown(f'<div class="mq-sec">{label}</div>', unsafe_allow_html=True)


def _searchable_bike(suffix, bikes, default_idx=0):
    """
    Search input + filtered selectbox for bike selection.

    UX: typing into the search box immediately auto-selects the first
    matching result — no dropdown click required. The selectbox key
    incorporates the query so the widget resets to index 0 on each
    new search term, making the first match the live selection.
    Users can still open the dropdown to pick a different match.
    """
    q = st.text_input("🔍 Search bikes", placeholder="e.g. R1, GSX-R, Hayabusa, KTM…",
                      key=f"bsearch_{suffix}", label_visibility="collapsed")
    if q:
        filtered = [b for b in bikes if q.lower() in b["label"].lower()]
    else:
        filtered = bikes

    if not filtered:
        st.caption("No matches — clear the search to see all bikes.")
        return None

    labels = [b["label"] for b in filtered]

    # Key changes with query → widget resets to index 0 on each new search
    # so the first result is auto-selected without opening the dropdown
    sel_key = f"bsel_{suffix}_{q[:30].replace(' ', '_')}"
    idx = st.selectbox(
        "Bike", range(len(labels)),
        format_func=lambda i: labels[i],
        index=0 if q else min(default_idx, len(filtered)-1),
        key=sel_key,
        label_visibility="collapsed",
    )

    if q:
        n = len(filtered)
        st.caption(f"{'1 match' if n == 1 else f'{n} matches'} · **{labels[idx]}** selected"
                   + (" — open dropdown to choose another" if n > 1 else ""))

    return filtered[idx]


def _tire_selector(bike_model_id, suffix, label="Rear tyre", position="rear"):
    """
    Search + filtered selectbox for tire selection. OEM fitments shown first.

    Same auto-select-on-search behaviour as _searchable_bike: typing into the
    search bar immediately pre-selects the first matching tire — no dropdown
    click required.
    """
    fitted, others = fetch_tires_for_bike(bike_model_id, position)

    q = st.text_input(f"🔍 {label}", placeholder="Brand, size or compound — e.g. Pirelli, 190/55, slick…",
                      key=f"tsearch_{position}_{suffix}", label_visibility="collapsed")

    all_entries = (
        [{"id": None,    "label": "⚙️ Stock (OEM — no override)", "fitted": None}]
        + [{"id": t["id"], "label": f"✅ {t['label']}", "fitted": True}  for t in fitted]
        + [{"id": t["id"], "label": f"   {t['label']}", "fitted": False} for t in others]
    )

    if q:
        filtered = [e for e in all_entries
                    if e["id"] is None or q.lower() in e["label"].lower()]
    else:
        filtered = all_entries

    if not filtered:
        st.caption("No tyre matches — clear search to see all.")
        return None

    # Pre-select first OEM fitment when no search, else auto-select first match
    default = (1 if fitted and not q else 0)
    default = min(default, len(filtered) - 1)

    labels = [e["label"] for e in filtered]

    # Key resets widget to index 0 on each new query → first match auto-selected
    tsel_key = f"tsel_{position}_{suffix}_{q[:30].replace(' ', '_')}"
    idx = st.selectbox(
        label, range(len(labels)),
        format_func=lambda i: labels[i],
        index=0 if q else default,
        key=tsel_key,
        label_visibility="collapsed",
    )

    chosen = filtered[idx]

    if q:
        n = len(filtered) - 1  # exclude the "stock" entry
        st.caption(f"{'1 tyre' if n <= 1 else f'{n} tyres'} matched · **{labels[idx].strip()}** selected"
                   + (" — open dropdown to choose another" if n > 1 else ""))
    elif chosen["fitted"] is True:
        st.caption("✅ OEM fitment for this bike")
    elif chosen["fitted"] is False:
        st.caption("⚠️ Not in OEM fitment list — verify size compatibility")

    return chosen["id"]


CAT_EMOJI = {
    "sprocket":"⚙️","chain":"🔗","exhaust":"💨","ecu":"🖥️",
    "clutch_kit":"🔧","nitrous":"💉","air_filter":"🌬️",
    "fuel_system":"⛽","suspension":"🏗️","brakes":"🛑",
    "wheelie_bar":"📐","boost_kit":"🚀","battery":"🔋",
    "bodywork":"🏎️","quickshifter":"⚡","swingarm_ext":"📏","tire":"🛞",
}
CAT_LABEL = {
    "sprocket":"Sprocket","chain":"Chain","exhaust":"Exhaust",
    "ecu":"ECU / Flash","clutch_kit":"Clutch Kit","nitrous":"Nitrous",
    "air_filter":"Air Filter","fuel_system":"Fuel System",
    "suspension":"Suspension","brakes":"Brakes","wheelie_bar":"Wheelie Bar",
    "boost_kit":"Boost / Turbo","battery":"Battery","bodywork":"Bodywork",
    "quickshifter":"Quickshifter","swingarm_ext":"Swingarm Ext.","tire":"Tire",
}


def _parts_panel(suffix, bike_catalog):
    """
    Multi-select parts panel for a pre-filtered catalog.
    Returns (list_of_part_ids, total_cost_inr).
    bike_catalog should already be filtered for the selected bike.
    """
    all_cats = sorted(bike_catalog.keys())
    if not all_cats:
        st.caption("No compatible parts found for this bike.")
        return [], 0.0

    cat_filt = st.multiselect(
        "Filter categories",
        all_cats,
        default=[],
        format_func=lambda c: f"{CAT_EMOJI.get(c,'')} {CAT_LABEL.get(c,c).title()}",
        key=f"cat_filt_{suffix}",
        placeholder="All categories",
        label_visibility="collapsed",
    )
    show_cats = cat_filt if cat_filt else all_cats

    selected_ids = []
    total_cost   = 0.0

    for cat in show_cats:
        if cat not in bike_catalog:
            continue
        parts      = bike_catalog[cat]
        emoji      = CAT_EMOJI.get(cat, "")
        cat_lbl    = CAT_LABEL.get(cat, cat).title()

        # Build per-part labels with availability + effects summary
        part_labels = []
        for p in parts:
            avail     = "📦" if p["availability"] == "in_stock" else "🚢"
            price_str = f"₹{p['price_inr']:,.0f}" if p["price_inr"] else "—"
            fx = []
            for k, v in p["effects"].items():
                short = k.split(".")[-1].replace("_"," ")
                if isinstance(v, bool):
                    if v: fx.append(short)
                elif isinstance(v, (int, float)):
                    fx.append(f"{'+' if v>0 else ''}{v:.1f} {short}")
            fx_str = "  ·  " + " / ".join(fx[:3]) if fx else ""
            part_labels.append(f"{avail} {p['brand']} {p['model_name']}  ({price_str}){fx_str}")

        chosen_idxs = st.multiselect(
            f"{emoji} {cat_lbl}",
            range(len(parts)),
            format_func=lambda i, pl=part_labels: pl[i],   # capture pl to avoid closure bug
            default=[],
            key=f"parts_{cat}_{suffix}",
        )
        for i in chosen_idxs:
            selected_ids.append(parts[i]["id"])
            total_cost += parts[i]["price_inr"]

    return selected_ids, total_cost


# ════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown(
        '<div style="padding:10px 0 4px;">'
        '<span style="font-size:20px;font-weight:800;color:#e8e8f0;letter-spacing:-0.3px;">Moto</span>'
        '<span style="font-size:20px;font-weight:800;color:#f97316;letter-spacing:-0.3px;">Quant</span>'
        '<span style="font-size:20px;font-weight:300;color:#2e2e42;"> Pro</span>'
        '</div>'
        '<div style="font-size:10px;color:#2e2e42;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px;">'
        'The physics of faster</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<hr>', unsafe_allow_html=True)

    bikes   = fetch_bike_list()
    venues  = fetch_venue_list()
    catalog = fetch_parts_catalog()

    if not bikes:
        st.error("No bikes in DB.\n\n`python -m motoquant.run import --known-bikes`")
        st.stop()

    # ── Bike A ────────────────────────────────────────────────────────────────
    _sec("🔴  Bike A")
    sel_a = _searchable_bike("A", bikes, default_idx=0)
    if sel_a is None:
        st.stop()

    # Basic / Advanced toggle
    mode_a = st.radio("Mode", ["⚡ Basic", "🔧 Advanced"], key="mode_A",
                      horizontal=True, label_visibility="collapsed",
                      help="Basic: direct power/mass sliders.  Advanced: parts catalog controls your build.")
    adv_a = (mode_a == "🔧 Advanced")

    if adv_a:
        st.caption("Advanced mode — select parts below. Power is set by parts, not a slider.")
        mass_a  = st.slider("Extra mass Δ kg", -30, 30, 0, key="mA",
                             help="Additional mass on top of parts (fuel load, ballast, etc.)")
        pwr_a = 100   # parts handle power in advanced mode
    else:
        col1, col2 = st.columns(2)
        pwr_a   = col1.slider("Power %",   70, 150, 100, key="pA",
                               help="Scale engine output vs. stock")
        mass_a  = col2.slider("Mass Δ kg", -30,  30,   0, key="mA",
                               help="Add / remove mass vs. stock dry weight")

    rider_a = st.slider("Rider weight kg", 50, 130, 75, key="rA",
                         help="Rider + gear. Affects total mass, CoG, weight transfer.")

    st.markdown("**🛞 Tyres**")
    st.caption("✅ = OEM fitment  |  Search by brand, size or compound")
    tire_rear_a  = _tire_selector(sel_a["model_id"], "A",   "Rear tyre",  "rear")
    tire_front_a = _tire_selector(sel_a["model_id"], "A_f", "Front tyre", "front")

    parts_a, cost_a = [], 0.0
    if adv_a:
        bike_catalog_a = filter_parts_for_bike(catalog, sel_a)
        with st.expander("🔧 Parts / Build", expanded=True):
            st.caption(f"Showing parts compatible with {sel_a['label']}. "
                       "Incompatible chain pitch / model-specific flashes are hidden.")
            parts_a, cost_a = _parts_panel("A", bike_catalog_a)
            if parts_a:
                # Show net effects preview
                net_a, flags_a = summarise_part_effects(parts_a, bike_catalog_a)
                chips = []
                KEY_LABEL = {
                    "engine.peak_power_hp": "hp", "engine.peak_torque_nm": "Nm",
                    "chassis.dry_mass_kg": "kg mass", "drivetrain.front_sprocket": "front sprocket",
                    "drivetrain.rear_sprocket": "rear sprocket",
                }
                for k, v in net_a.items():
                    if isinstance(v, float) and k in KEY_LABEL:
                        sign = "+" if v > 0 else ""
                        chips.append(f"{sign}{v:.1f} {KEY_LABEL[k]}")
                for k, v in flags_a.items():
                    if v:
                        chips.append(k.split(".")[-1].replace("_"," "))
                if chips:
                    st.markdown(
                        "**Net effect:**  " + "  ·  ".join(f"`{c}`" for c in chips[:6])
                        + f"\n\n💰 Build cost: **₹{cost_a:,.0f}**")
            else:
                st.caption("No parts selected yet.")

    # ── Compare ───────────────────────────────────────────────────────────────
    st.markdown('<hr style="margin:12px 0;">', unsafe_allow_html=True)
    compare = st.toggle("📊 Compare two bikes", value=False)

    sel_b = None; pwr_b = 100; mass_b = 0; rider_b = 75
    tire_rear_b = None; tire_front_b = None; parts_b = []; cost_b = 0.0

    if compare:
        _sec("🔵  Bike B")
        sel_b = _searchable_bike("B", bikes, default_idx=min(1, len(bikes)-1))
        if sel_b is None:
            sel_b = bikes[0]

        mode_b = st.radio("Mode", ["⚡ Basic", "🔧 Advanced"], key="mode_B",
                          horizontal=True, label_visibility="collapsed")
        adv_b = (mode_b == "🔧 Advanced")

        if adv_b:
            st.caption("Advanced mode — parts control power.")
            mass_b  = st.slider("Extra mass Δ kg", -30, 30, 0, key="mB")
            pwr_b = 100
        else:
            col3, col4 = st.columns(2)
            pwr_b  = col3.slider("Power %",   70, 150, 100, key="pB")
            mass_b = col4.slider("Mass Δ kg", -30,  30,   0, key="mB")

        rider_b = st.slider("Rider weight kg", 50, 130, 75, key="rB")

        st.markdown("**🛞 Tyres**")
        st.caption("✅ = OEM fitment  |  Search by brand, size or compound")
        tire_rear_b  = _tire_selector(sel_b["model_id"], "B",   "Rear tyre",  "rear")
        tire_front_b = _tire_selector(sel_b["model_id"], "B_f", "Front tyre", "front")

        if adv_b:
            bike_catalog_b = filter_parts_for_bike(catalog, sel_b)
            with st.expander("🔧 Parts / Build", expanded=True):
                st.caption(f"Showing parts compatible with {sel_b['label']}.")
                parts_b, cost_b = _parts_panel("B", bike_catalog_b)
                if parts_b:
                    net_b, flags_b = summarise_part_effects(parts_b, bike_catalog_b)
                    chips_b = []
                    for k, v in net_b.items():
                        if isinstance(v, float) and k in {
                            "engine.peak_power_hp","engine.peak_torque_nm",
                            "chassis.dry_mass_kg","drivetrain.front_sprocket",
                            "drivetrain.rear_sprocket",
                        }:
                            chips_b.append(f"{'+' if v>0 else ''}{v:.1f} {k.split('.')[-1].replace('_',' ')}")
                    for k, v in flags_b.items():
                        if v: chips_b.append(k.split(".")[-1].replace("_"," "))
                    if chips_b:
                        st.markdown(
                            "**Net effect:**  " + "  ·  ".join(f"`{c}`" for c in chips_b[:6])
                            + f"\n\n💰 Build cost: **₹{cost_b:,.0f}**")
                else:
                    st.caption("No parts selected yet.")

    # ── Venue ─────────────────────────────────────────────────────────────────
    st.markdown('<hr style="margin:12px 0;">', unsafe_allow_html=True)
    _sec("📍  Venue")
    if not venues:
        st.warning("No venues in DB.")
        venue_id = None
    else:
        v_labels = [v["name"] for v in venues]
        v_idx = st.selectbox("Venue", range(len(v_labels)),
                             format_func=lambda i: v_labels[i],
                             key="vsel", label_visibility="collapsed")
        venue_id = venues[v_idx]["id"]
        v = venues[v_idx]
        flag = "🇮🇳" if v.get("country") in ("India","IN") else "🌍"
        st.caption(f"{flag} {v.get('city','')}  ·  Alt {v.get('altitude_m',0):.0f} m  ·  {v.get('surface_type','asphalt')}")

    # ── Conditions ────────────────────────────────────────────────────────────
    st.markdown('<hr style="margin:12px 0;">', unsafe_allow_html=True)
    _sec("🌡  Conditions")
    c1, c2 = st.columns(2)
    t_amb   = c1.number_input("Air °C",        value=25.0, min_value=0.0,  max_value=55.0, step=1.0)
    t_track = c2.number_input("Track °C",      value=30.0, min_value=15.0, max_value=65.0, step=1.0)
    c3, c4 = st.columns(2)
    humid   = c3.number_input("Humidity %",    value=40,   min_value=0,    max_value=100,  step=5)
    wind    = c4.number_input("Headwind km/h", value=0.0,  min_value=-30., max_value=30.,  step=1.0,
                              help="Positive = headwind  |  Negative = tailwind")

    st.markdown('<hr style="margin:12px 0;">', unsafe_allow_html=True)
    run_btn = st.button("▶  RUN SIMULATION", type="primary", use_container_width=True)


# ════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════

def make_env(venue_id, t_amb, t_track, humid, wind_kmh):
    from motoquant.models import EnvironmentParams
    env = load_env(venue_id) if venue_id else EnvironmentParams()
    env.ambient_temp_c        = float(t_amb)
    env.track_temp_c          = float(t_track)
    env.relative_humidity_pct = float(humid)
    env.wind_speed_ms         = abs(wind_kmh / 3.6)
    env.wind_direction_deg    = 0.0 if wind_kmh >= 0 else 180.0
    return env


def tune_config(cfg, pwr_pct, mass_delta, rider_kg):
    cfg = copy.deepcopy(cfg)
    if pwr_pct != 100:
        f = pwr_pct / 100.0
        cfg.engine.peak_power_hp *= f
        if cfg.engine.dyno_curve is not None:
            cfg.engine.dyno_curve.torque_nm = cfg.engine.dyno_curve.torque_nm * f
    if mass_delta != 0:
        cfg.chassis.dry_mass_kg += mass_delta
    cfg.chassis.rider_mass_kg = float(rider_kg)
    return cfg


def simulate(cfg):
    from motoquant import MotoQuantEngine
    return MotoQuantEngine(cfg).run()


def card(col, label, value, unit, variant=""):
    col.markdown(
        f'<div class="mq-card {variant}">'
        f'<div class="lbl">{label}</div>'
        f'<div class="val">{value}</div>'
        f'<div class="unit">{unit}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def splits_table(r, prefix=""):
    return pd.DataFrame({
        "Split":                ["60 ft","330 ft","⅛ mile","1000 ft","¼ mile"],
        f"{prefix}Time (s)":    [f"{r.time_60ft:.3f}",f"{r.time_330ft:.3f}",
                                  f"{r.time_eighth:.3f}",f"{r.time_1000ft:.3f}",
                                  f"{r.time_quarter:.3f}"],
        f"{prefix}Speed (km/h)":[f"{r.speed_60ft*3.6:.1f}",f"{r.speed_330ft*3.6:.1f}",
                                  f"{r.speed_eighth*3.6:.1f}",f"{r.speed_1000ft*3.6:.1f}",
                                  f"{r.speed_quarter*3.6:.1f}"],
    })


CHART_DARK = dict(
    paper_bgcolor="#060609", plot_bgcolor="#0a0a11",
    font=dict(color="#6060a8", size=11, family="Inter"),
    margin=dict(l=48, r=16, t=40, b=36),
)
# Build A: orange (#fb923c), Build B: blue (#93c5fd) — matches UI card colours
COLOR_A = "#fb923c"
COLOR_B = "#93c5fd"


def build_main_chart(ra, la, rb=None, lb=None):
    fig = make_subplots(rows=2, cols=2,
                        subplot_titles=("Speed (km/h)", "Engine RPM", "Gear", "Traction (%)"),
                        vertical_spacing=0.22, horizontal_spacing=0.12)
    def _add(r, label, color, dash="solid"):
        kw = dict(name=label, line=dict(color=color, width=2.5, dash=dash))
        fig.add_trace(go.Scatter(x=r.t, y=r.v*3.6,       **kw),                       row=1, col=1)
        fig.add_trace(go.Scatter(x=r.t, y=r.rpm,         **kw, showlegend=False),      row=1, col=2)
        fig.add_trace(go.Scatter(x=r.t, y=r.gear, showlegend=False,
                                 line=dict(color=color, width=2.5, dash=dash, shape="hv")), row=2, col=1)
        fig.add_trace(go.Scatter(x=r.t, y=r.traction_pct,**kw, showlegend=False),      row=2, col=2)
    _add(ra, la, COLOR_A)
    if rb is not None:
        _add(rb, lb, COLOR_B, dash="dash")
    grid_kw = dict(gridcolor="#101018", zeroline=False)
    fig.update_xaxes(title_text="Time (s)", **grid_kw)
    fig.update_yaxes(**grid_kw)
    fig.update_yaxes(title_text="km/h", row=1, col=1)
    fig.update_yaxes(title_text="RPM",  row=1, col=2)
    fig.update_yaxes(title_text="Gear", row=2, col=1)
    fig.update_yaxes(title_text="%",    row=2, col=2)
    for ann in fig.layout.annotations:
        ann.font.color = "#404060"; ann.font.size = 11
    fig.update_layout(**CHART_DARK, height=490,
                      legend=dict(orientation="h", x=0.5, y=1.08, xanchor="center",
                                  bgcolor="rgba(0,0,0,0)", font=dict(size=12, color="#9898c0")))
    return fig


def build_extra_chart(ra, rb=None):
    fig = make_subplots(rows=1, cols=3,
                        subplot_titles=("Tyre temp (°C)", "Drive force (N)", "Aero drag (N)"),
                        horizontal_spacing=0.12)
    def _add(r, color, dash="solid"):
        kw = dict(showlegend=False, line=dict(color=color, width=2.5, dash=dash))
        fig.add_trace(go.Scatter(x=r.t, y=r.T_tire,  **kw), row=1, col=1)
        fig.add_trace(go.Scatter(x=r.t, y=r.F_drive, **kw), row=1, col=2)
        fig.add_trace(go.Scatter(x=r.t, y=r.F_drag,  **kw), row=1, col=3)
    _add(ra, COLOR_A)
    if rb is not None:
        _add(rb, COLOR_B, dash="dash")
    grid_kw = dict(gridcolor="#101018", zeroline=False)
    fig.update_xaxes(title_text="Time (s)", **grid_kw)
    fig.update_yaxes(**grid_kw)
    for ann in fig.layout.annotations:
        ann.font.color = "#404060"; ann.font.size = 11
    fig.update_layout(**CHART_DARK, height=300)
    return fig


def spec_df(cfg, rider_kg, parts_labels=None):
    rows = [
        ("Peak power",   f"{cfg.engine.peak_power_hp:.0f} hp @ {cfg.engine.peak_power_rpm:.0f} rpm"),
        ("Peak torque",  f"{cfg.engine.peak_torque_nm:.0f} Nm @ {cfg.engine.peak_torque_rpm:.0f} rpm"),
        ("Displacement", f"{cfg.engine.displacement_cc:.0f} cc"),
        ("Dry mass",     f"{cfg.chassis.dry_mass_kg:.1f} kg"),
        ("Rider weight", f"{rider_kg:.0f} kg"),
        ("Total mass",   f"{cfg.chassis.total_mass_kg:.1f} kg"),
        ("Gears",        str(cfg.drivetrain.num_gears)),
        ("Redline",      f"{cfg.engine.redline_rpm:.0f} rpm"),
        ("Drivetrain η", f"{cfg.drivetrain.drivetrain_efficiency()*100:.1f}%"),
        ("Cd·A",         f"{cfg.aero.cd_a_effective:.4f} m²"),
        ("Gear ratios",  "  ".join(f"{r:.3f}" for r in cfg.drivetrain.gear_ratios)),
        ("Final drive",  f"{cfg.drivetrain.final_drive_ratio:.3f}  "
                         f"({cfg.drivetrain.front_sprocket}T / {cfg.drivetrain.rear_sprocket}T)"),
    ]
    if parts_labels:
        rows.append(("Build parts", ", ".join(parts_labels)))
    return pd.DataFrame(rows, columns=["Parameter", "Value"])


def cond_df(cfg):
    from motoquant.submodels import EnvironmentalModel
    em = EnvironmentalModel(cfg)
    s  = em.summary()
    rows = [
        ("Air density",      f"{s['rho_kg_m3']:.4f} kg/m³"),
        ("Density altitude", f"{s['density_alt_ft']:.0f} ft"),
        ("Power correction", f"{s['power_correction']:.4f}  ({s['da_power_loss_pct']:.2f}% loss)"),
        ("Headwind",         f"{s['v_headwind_ms']*3.6:.1f} km/h"),
        ("Grip multiplier",  f"{s['grip_multiplier']:.3f}"),
        ("RR multiplier",    f"{s['rr_multiplier']:.3f}"),
        ("Ambient temp",     f"{s['ambient_temp_c']:.1f} °C"),
        ("Track temp",       f"{s['track_temp_c']:.1f} °C"),
    ]
    return pd.DataFrame(rows, columns=["Condition", "Value"])


def _parts_summary_label(part_ids, catalog):
    """Short label list for each selected part."""
    flat = {p["id"]: f"{p['brand']} {p['model_name']}"
            for parts in catalog.values() for p in parts}
    return [flat[pid] for pid in part_ids if pid in flat]


# ════════════════════════════════════════════════════════
# MAIN PANEL
# ════════════════════════════════════════════════════════

st.markdown(
    '<div style="display:flex;align-items:center;gap:0;margin-bottom:2px;">'
    '<span style="font-size:26px;font-weight:800;color:#e8e8f0;letter-spacing:-0.5px;line-height:1;">Moto</span>'
    '<span style="font-size:26px;font-weight:800;color:#f97316;letter-spacing:-0.5px;line-height:1;">Quant</span>'
    '<span style="font-size:26px;font-weight:300;color:#3a3a52;letter-spacing:-0.5px;line-height:1;">&nbsp;Pro</span>'
    '</div>'
    '<div style="font-size:11.5px;color:#3a3a52;margin:4px 0 20px;letter-spacing:0.3px;">'
    'First-principles quarter-mile physics engine&nbsp;&nbsp;·&nbsp;&nbsp;'
    'Aamby Valley · MMRT · BIC · Kari · Hyderabad'
    '</div>',
    unsafe_allow_html=True,
)

if not run_btn:
    # ── Welcome ───────────────────────────────────────────────────────────────
    stats = fetch_db_stats()
    c1, c2, c3, c4 = st.columns(4)
    for col, num, lbl in [
        (c1, stats["bikes"],  "Bikes"),
        (c2, stats["tires"],  "Tires"),
        (c3, stats["parts"],  "Parts"),
        (c4, stats["venues"], "Venues"),
    ]:
        col.markdown(
            f'<div class="mq-stat"><div class="s-num">{num}</div>'
            f'<div class="s-lbl">{lbl}</div></div>',
            unsafe_allow_html=True)

    st.markdown('<hr style="margin:18px 0;">', unsafe_allow_html=True)

    step_css = ("background:#0a0a12;border:1px solid #1a1a26;border-radius:12px;"
                "padding:20px 18px;height:100%;")
    num_css  = ("display:inline-flex;align-items:center;justify-content:center;"
                "width:28px;height:28px;border-radius:8px;"
                "background:#f9731618;border:1px solid #f9731640;"
                "color:#fb923c;font-weight:700;font-size:13px;margin-bottom:10px;")
    g1, g2, g3 = st.columns(3)
    for col, n, title, desc in [
        (g1, 1, "Pick a bike",
         "135 bikes across 20+ manufacturers, including KTM, Bajaj, TVS, Royal Enfield, CFMoto, and Benelli. "
         "Adjust power %, mass delta, and rider weight."),
        (g2, 2, "Set tyres & parts",
         "OEM-matched tyres shown first. Add real drag-prep parts — sprockets, ECU flashes, "
         "nitrous, turbo kits — and see live build cost in ₹."),
        (g3, 3, "Run & analyse",
         "Full RK4 quarter-mile sim returns splits, v(t), RPM, traction %, and drive force. "
         "Compare two builds head-to-head with ΔET and ΔTrap."),
    ]:
        col.markdown(
            f'<div style="{step_css}"><div style="{num_css}">{n}</div>'
            f'<div style="font-weight:600;color:#c8c8e0;font-size:14px;margin-bottom:6px;">{title}</div>'
            f'<div style="font-size:12px;color:#484860;line-height:1.6;">{desc}</div></div>',
            unsafe_allow_html=True)

    st.markdown('<hr style="margin:18px 0;">', unsafe_allow_html=True)
    with st.expander("📋 All bikes in database", expanded=False):
        df_bikes = pd.DataFrame(bikes)[["label","mfr","category"]].rename(
            columns={"label":"Bike","mfr":"Manufacturer","category":"Category"})
        st.dataframe(df_bikes, use_container_width=True, hide_index=True)

else:
    # ════════════════════════════════════════════
    # SIMULATE
    # ════════════════════════════════════════════
    env = make_env(venue_id, t_amb, t_track, humid, wind)

    with st.spinner(f"Simulating {sel_a['label']}…"):
        try:
            cfg_a = load_config(sel_a["id"], env)
            if cfg_a is None:
                st.error(f"Could not load config #{sel_a['id']} from DB."); st.stop()
            cfg_a = tune_config(cfg_a, pwr_a, mass_a, rider_a)
            cfg_a = apply_tire_override(cfg_a, tire_front_a, tire_rear_a, _get_db())
            cfg_a = apply_parts(cfg_a, parts_a)
            res_a = simulate(cfg_a)
        except Exception as ex:
            st.error(f"Simulation A failed: {ex}"); st.exception(ex); st.stop()

    res_b, cfg_b = None, None
    lab_b = None
    if compare and sel_b:
        with st.spinner(f"Simulating {sel_b['label']}…"):
            try:
                cfg_b = load_config(sel_b["id"], env)
                if cfg_b:
                    cfg_b = tune_config(cfg_b, pwr_b, mass_b, rider_b)
                    cfg_b = apply_tire_override(cfg_b, tire_front_b, tire_rear_b, _get_db())
                    cfg_b = apply_parts(cfg_b, parts_b)
                    res_b = simulate(cfg_b)
                    lab_b = sel_b["label"]
                    if pwr_b != 100 and mass_b != 0:
                        lab_b += f" ({pwr_b}%/{mass_b:+d}kg)"
                    elif pwr_b != 100:
                        lab_b += f" ({pwr_b}%)"
                    elif mass_b != 0:
                        lab_b += f" ({mass_b:+d}kg)"
            except Exception as ex:
                st.warning(f"Simulation B failed: {ex}")

    lab_a = sel_a["label"]
    # Only include power% when it's non-neutral (Advanced mode always = 100,
    # so "100%/-20kg" is confusing — just show the mass delta in that case)
    if pwr_a != 100 and mass_a != 0:
        lab_a += f" ({pwr_a}%/{mass_a:+d}kg)"
    elif pwr_a != 100:
        lab_a += f" ({pwr_a}%)"
    elif mass_a != 0:
        lab_a += f" ({mass_a:+d}kg)"

    # ── Parts tags in label ────────────────────────────────────────────────────
    parts_labels_a = _parts_summary_label(parts_a, catalog)
    parts_labels_b = _parts_summary_label(parts_b, catalog) if compare else []

    # ── Result cards ─────────────────────────────────────────────────────────
    if compare and res_b:
        col_left, col_right = st.columns(2)
        with col_left:
            st.markdown(f'<span class="badge-a">A</span>'
                        f'<span style="font-weight:700;color:#dde0f0;font-size:13px;">{lab_a}</span>',
                        unsafe_allow_html=True)
            if parts_labels_a:
                # Show up to 8 chips; [:4] was silently hiding parts beyond 4
                st.markdown(" ".join(f'<span class="part-chip">{p}</span>' for p in parts_labels_a[:8]),
                            unsafe_allow_html=True)
            # In compare mode each side is ~50% viewport — use 2×2 so cards
            # don't overflow into a ragged wrap at typical screen widths
            mc1, mc2 = st.columns(2)
            mc3, mc4 = st.columns(2)
            card(mc1,"¼ Mile",  f"{res_a.time_quarter:.3f}",    "s",   "mq-card-a")
            card(mc2,"Trap",    f"{res_a.speed_quarter*3.6:.1f}","km/h","mq-card-a")
            card(mc3,"⅛ Mile",  f"{res_a.time_eighth:.3f}",     "s",   "mq-card-a")
            card(mc4,"60 ft",   f"{res_a.time_60ft:.3f}",       "s",   "mq-card-a")
        with col_right:
            st.markdown(f'<span class="badge-b">B</span>'
                        f'<span style="font-weight:700;color:#dde0f0;font-size:13px;">{lab_b}</span>',
                        unsafe_allow_html=True)
            if parts_labels_b:
                st.markdown(" ".join(f'<span class="part-chip">{p}</span>' for p in parts_labels_b[:8]),
                            unsafe_allow_html=True)
            mc5, mc6 = st.columns(2)
            mc7, mc8 = st.columns(2)
            card(mc5,"¼ Mile",  f"{res_b.time_quarter:.3f}",    "s",   "mq-card-b")
            card(mc6,"Trap",    f"{res_b.speed_quarter*3.6:.1f}","km/h","mq-card-b")
            card(mc7,"⅛ Mile",  f"{res_b.time_eighth:.3f}",     "s",   "mq-card-b")
            card(mc8,"60 ft",   f"{res_b.time_60ft:.3f}",       "s",   "mq-card-b")

        dt   = res_b.time_quarter - res_a.time_quarter
        dv   = (res_b.speed_quarter - res_a.speed_quarter) * 3.6
        cls  = "mq-faster" if dt > 0 else "mq-slower"
        cls2 = "mq-faster" if dv < 0 else "mq-slower"
        winner = f'<span class="badge-a">A</span> {lab_a}' if dt > 0 \
                 else f'<span class="badge-b">B</span> {lab_b}'
        st.markdown(
            f'<div class="mq-delta">'
            f'Δ ET = <span class="{cls}">{dt:+.3f}s</span>'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;'
            f'Δ Trap = <span class="{cls2}">{dv:+.1f} km/h</span>'
            f'&nbsp;&nbsp;·&nbsp;&nbsp;🏆 {winner}'
            + (f'&nbsp;&nbsp;·&nbsp;&nbsp;Build cost A: ₹{cost_a:,.0f}' if cost_a else "")
            + (f'  /  B: ₹{cost_b:,.0f}' if cost_b else "")
            + '</div>',
            unsafe_allow_html=True)

    else:
        st.markdown(f'<span class="badge-a">A</span>'
                    f'<span style="font-weight:700;color:#dde0f0;font-size:13px;">{lab_a}</span>',
                    unsafe_allow_html=True)
        if parts_labels_a:
            st.markdown(" ".join(f'<span class="part-chip">{p}</span>' for p in parts_labels_a[:6]),
                        unsafe_allow_html=True)
        mc1,mc2,mc3,mc4 = st.columns(4)
        card(mc1,"Quarter Mile ET", f"{res_a.time_quarter:.3f}",    "seconds","mq-card-a")
        card(mc2,"Trap Speed",      f"{res_a.speed_quarter*3.6:.1f}","km/h",  "mq-card-a")
        card(mc3,"⅛ Mile ET",       f"{res_a.time_eighth:.3f}",     "seconds","mq-card-a")
        card(mc4,"60 ft",           f"{res_a.time_60ft:.3f}",       "seconds","mq-card-a")
        if cost_a:
            st.markdown(
                f'<div style="font-size:12px;color:#606080;margin-top:6px;">'
                f'🔧 Build cost: ₹{cost_a:,.0f}</div>',
                unsafe_allow_html=True)

    st.markdown('<hr style="margin:18px 0;">', unsafe_allow_html=True)

    # ── Tabs ─────────────────────────────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Charts", "⏱ Splits", "🔧 Specs", "🌤 Conditions"])

    with tab1:
        st.plotly_chart(build_main_chart(res_a, lab_a, res_b, lab_b), use_container_width=True)
        with st.expander("Detailed channels — tyre temp · drive force · aero drag"):
            st.plotly_chart(build_extra_chart(res_a, res_b), use_container_width=True)

    with tab2:
        st.markdown('<div style="font-size:12px;color:#505070;margin-bottom:6px;">Times in seconds · Speeds in km/h</div>',
                    unsafe_allow_html=True)
        if compare and res_b:
            df_m = splits_table(res_a,"A · ").merge(splits_table(res_b,"B · "), on="Split")
            st.dataframe(df_m, use_container_width=True, hide_index=True)
        else:
            st.dataframe(splits_table(res_a), use_container_width=True, hide_index=True)

    with tab3:
        if compare and cfg_b:
            c_l, c_r = st.columns(2)
            with c_l:
                st.markdown(f'<span class="badge-a">A</span> <b>{lab_a}</b>', unsafe_allow_html=True)
                st.dataframe(spec_df(cfg_a, rider_a, parts_labels_a), use_container_width=True, hide_index=True)
            with c_r:
                st.markdown(f'<span class="badge-b">B</span> <b>{lab_b}</b>', unsafe_allow_html=True)
                st.dataframe(spec_df(cfg_b, rider_b, parts_labels_b), use_container_width=True, hide_index=True)
        else:
            st.dataframe(spec_df(cfg_a, rider_a, parts_labels_a), use_container_width=True, hide_index=True)

    with tab4:
        if compare and cfg_b:
            c_l, c_r = st.columns(2)
            with c_l:
                st.markdown(f'<span class="badge-a">A</span> <b>{lab_a}</b>', unsafe_allow_html=True)
                st.dataframe(cond_df(cfg_a), use_container_width=True, hide_index=True)
            with c_r:
                st.markdown(f'<span class="badge-b">B</span> <b>{lab_b}</b>', unsafe_allow_html=True)
                st.dataframe(cond_df(cfg_b), use_container_width=True, hide_index=True)
        else:
            st.dataframe(cond_df(cfg_a), use_container_width=True, hide_index=True)
