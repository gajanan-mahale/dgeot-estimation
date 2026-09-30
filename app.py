import streamlit as st
from wire_rope import select_rope, calc_rope_length_weight
from ct_machinery import get_drum
from ct_wheel_cal import get_wheel_full as get_ct_wheel
from lt_wheel_cal import get_lt_wheel_full as get_lt_wheel
from main_dg_box import get_box_girder
from end_carriage_dg import get_end_carriage

USERS = {
    "admin": "Owner@ceo",
    "designer": "Crane@2025",
    "vinays": "Vinay@2026",
    "vikasm": "Vikasm@2026"
}

st.set_page_config(page_title="DGCRANE_NEW - Full Suite", layout="wide", page_icon="🏗️")

RAIL_MASTER = [
    {"swl":5,"rail":"50x50","wt":19.625},{"swl":7.5,"rail":"50x50","wt":19.625},
    {"swl":10,"rail":"60x40","wt":18.84},{"swl":12.5,"rail":"60x40","wt":18.84},
    {"swl":15,"rail":"60x60","wt":28.26},{"swl":20,"rail":"60x60","wt":28.26},
    {"swl":25,"rail":"LBS60","wt":30.0},{"swl":30,"rail":"LBS75","wt":37.5},
    {"swl":32,"rail":"LBS90","wt":45.0},{"swl":35,"rail":"LBS90","wt":45.0},
    {"swl":40,"rail":"LBS105","wt":52.0},{"swl":45,"rail":"LBS120","wt":60.0},
    {"swl":50,"rail":"LBS120","wt":60.0},
]
RAIL_WT_MAP = {
    "50x50": 19.625, "60x40": 18.84, "60x60": 28.26,
    "LBS60": 30.0, "LBS75": 37.5, "LBS90": 45.0, "LBS105": 52.0, "LBS120": 60.0,
    "CR80": 64.24, "80": 64.24, "CR100": 89.0, "100": 89.0
}

@st.cache_data
def get_rail_wt(rail_name):
    rn = rail_name.strip().lower().replace(" ", "")
    norm_map = {}
    for k,v in RAIL_WT_MAP.items():
        nk = k.strip().lower().replace(" ", "")
        norm_map[nk] = v
    for r in RAIL_MASTER:
        nk = r["rail"].strip().lower().replace(" ", "")
        if nk not in norm_map:
            norm_map[nk] = r["wt"]
    if rn in norm_map:
        return norm_map[rn]
    rn2 = rn.replace("-", "").replace("_", "")
    if rn2 in norm_map:
        return norm_map[rn2]
    return 19.625

@st.cache_data
def get_rail_by_swl(swl):
    for r in RAIL_MASTER:
        if swl <= r["swl"]: return r
    return RAIL_MASTER[-1]

@st.cache_data
def get_factors(cls):
    base={"M1":1.06,"M2":1.12,"M3":1.18,"M4":1.25,"M5":1.32,"M6":1.4,"M7":1.5,"M8":1.5}
    duty={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.05,"M5":1.06,"M6":1.1,"M7":1.12,"M8":1.2}
    cls = cls.strip().upper()
    return base.get(cls,1.32), duty.get(cls,1.06)

@st.cache_data
def calc_pmax(swl, span, wtrolley_t, Wcrane_final, TG_cm, n_ltw):
    TG_M = TG_cm/100.0
    Ha = max(1.0, TG_M*0.5)
    WC_T = Wcrane_final/1000.0
    Pmax_T = (swl+wtrolley_t)*(span+Ha)/((n_ltw/2)*span) + (WC_T-wtrolley_t)/n_ltw
    return Pmax_T*1000, Ha

# ===== LOGIN =====
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
    st.session_state.user=""

def login_page():
    st.title("🔐 DGCRANE_NEW - Login")
    col1,col2=st.columns([1,2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/1995/1995515.png", width=120)
        st.info("Login required - Full Accuracy Mode")
    with col2:
        uid=st.text_input("Login ID")
        pwd=st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            if uid in USERS and USERS[uid]==pwd:
                st.session_state.logged_in=True
                st.session_state.user=uid
                st.rerun()
            else:
                st.error("Invalid ID or Password")
        # st.caption("admin / Owner@ceo, designer /Crane@2025, vinays / Vinay@2026, vikasm / Vikasm@2026")

if not st.session_state.logged_in:
    login_page()
    st.stop()

st.sidebar.success(f"Logged in: {st.session_state.user}")
st.sidebar.title("DGCRANE_NEW")
if st.sidebar.button("Logout (Keep Cache) ⚡", key="logout_keep_unique", use_container_width=True):
    st.session_state.logged_in=False
    st.rerun()
if st.sidebar.button("Logout + Clear Cache", key="logout_clear_unique",use_container_width=True):
    st.session_state.logged_in=False
    st.cache_data.clear()
    st.rerun()

# ===== MAIN - EXACT COPY OF YOUR dgcrane_new.py LOGIC =====
st.title("🏗️ DGCRANE FULL SUITE")
st.caption("BY: GAJANAN MAHALE")

# Inputs - same as your input() prompts
c1,c2,c3,c4=st.columns(4)
with c1:
    swl=st.number_input("Enter SWL (T) [10]", value=10.0, step=0.5)
    span=st.number_input("Enter Span (m) [20]", value=20.0, step=0.5)
    lift=st.number_input("Enter Lift Height (m) [10]", value=10.0, step=0.5)
with c2:
    duty=st.selectbox("Enter Duty M1-M8 [M5]", ["M1","M2","M3","M4","M5","M6","M7","M8"], index=4)
    falls=st.number_input("Enter No. of Falls [4]", value=4.0, step=1.0)
    core=st.selectbox("Enter core steel/fiber [fiber]", ["fiber","steel"], index=0)
    reeving=2
with c3:
    auto=get_rail_by_swl(swl)
    # st.write(f"**Auto rail for SWL {swl}T = {auto['rail']}**")
    lt_rail_name=st.selectbox(f"Enter LT Rail size [{auto['rail']}]", ["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"], index=["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"].index(auto['rail']) if auto['rail'] in ["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"] else 1)
    ct_rail_name=st.selectbox(f"Enter CT Rail size [{lt_rail_name}]", ["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"], index=["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"].index(lt_rail_name) if lt_rail_name in ["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"] else 1)
with c4:
    wt_def=round(0.2*swl,2)
    wtrolley_t=st.number_input(f"Enter W Trolley (T) [{wt_def}]", value=float(wt_def), step=0.1)
    n_ctw=st.number_input("Enter No of CT wheels [4]", value=4, min_value=2, max_value=16, step=2)
    n_ltw=st.number_input("Enter No of LT wheels [4]", value=4, min_value=4, max_value=16, step=2)

impact,duty_f=get_factors(duty)
st.info(f"Duty {duty} -> IMPACT={impact} DF={duty_f} (from dg_suite M8=1.5) | LT Rail STORED={lt_rail_name} will reuse for LT wheel, no re-ask | CT Rail STORED={ct_rail_name} will reuse for CT wheel & rail wt")

if st.button("Run Calculation", type="primary", use_container_width=True):
    st.subheader("--- WIRE ROPE ---")
    rope_res=select_rope(swl,falls,duty,core)
    sel=rope_res["selected"]
    length,wt=calc_rope_length_weight(lift,falls,sel["wt_kg_100m"])
    final_dia=sel["dia"]
    st.write(f"Selected Rope: {final_dia} mm, FOS {rope_res['actual_fos']:.2f} | Length {length:.1f}m Wt {wt:.1f}kg")

    st.subheader("--- CT DRUM ---")
    drum_res=get_drum(swl,final_dia,lift,falls,reeving,duty)
    drum_len=drum_res['drum_length_mm']
    st.write(f"Drum {drum_res['drum_od']} dia X {drum_res['drum_thk_mm']} thk (eff {drum_res['drum_thk_eff_mm']} mm) X {drum_len} length")

    # Trolley Gauge
    calc_gauge=drum_len+1200
    calc_TG_cm=calc_gauge/10
    st.subheader(f"Trolley Gauge - TG=Drum+1200={calc_gauge}mm = {calc_TG_cm:.0f}cm")
    TG_cm=st.number_input(f"Trolley Gauge in cm [Default Drum+1200={calc_TG_cm:.0f} cm]", value=float(calc_TG_cm), key="tg_input")
    trolley_gauge=TG_cm*10
    st.write(f"TG = {TG_cm:.1f} cm | Wheelbase = {TG_cm}+150 = {TG_cm+150}cm")

    st.subheader(f"--- CT WHEEL ---")
    # st.write(f"Using stored CT Rail = {ct_rail_name}")
    ct_res=get_ct_wheel(swl_t=swl, wtrolley_t=wtrolley_t, n_ctw=n_ctw, ct_rail_name=ct_rail_name, duty=duty)
    st.write(f"CT: Dmin={ct_res['dmin_mm']}mm -> Sel={ct_res['d_sel_mm']}mm Wt={ct_res['total_wt_kg']}Kg")
    # st.json(ct_res)

    st.subheader("--- DG BOX GIRDER ---")
    box_sol=get_box_girder(SWL_T=swl, SPAN_M=span, duty=duty, IMPACT=impact, DF=duty_f)
    if not box_sol:
        st.error("No box girder solution")
        st.stop()
    Wg=box_sol['Wg']
    st.write(f"Box: H={box_sol['H']:.1f}cm Wgirder for 1NO={Wg:.0f}Kg IMPACT={box_sol.get('IMPACT',impact)} DF={box_sol.get('DF',duty_f)} Camber={box_sol.get('camber',0)}cm")
    # st.json(box_sol)

    st.subheader("--- END CARRIAGE ---")
    st.write(f"Wheelbase = {TG_cm+150}cm TG {TG_cm}cm")
    P=(swl*1000 + wtrolley_t*1000)/2
    ec_sol=get_end_carriage(SWL_T=swl, SPAN_M=span, Wg=Wg, P_override=P, WT_HOIST_override=wtrolley_t*1000, TG_cm=TG_cm, duty=duty, IMPACT=impact, DF=duty_f, rope_dia=final_dia, lift_m=lift, falls=falls, drum_length_mm=drum_len)
    if not ec_sol:
        st.error("No end carriage solution")
        st.stop()
    st.write(f"EC: H={ec_sol['H']:.1f} Wecfor 1NO={ec_sol['Wec_one']:.0f}Kg 2={ec_sol['Wec_total']:.0f}Kg Wcrane est={ec_sol['WCRANE']:.0f}Kg IMPACT={impact}")
    # st.json(ec_sol)
    Wcrane_est=ec_sol['WCRANE']

    st.subheader(f"--- LT WHEEL ---")
    # st.write(f"Using stored LT Rail = {lt_rail_name} (no re-ask)")
    lt_res=get_lt_wheel(swl_t=swl, wcrane_t=Wcrane_est/1000, n_ltw=n_ltw, lt_rail_name=lt_rail_name, duty=duty)
    st.write(f"LT: Dmin={lt_res['dmin_mm']} -> Sel={lt_res['d_sel_mm']}mm Wt={lt_res['total_wt_kg']}Kg")
    # st.json(lt_res)

    # FINAL WCRANE
    platform_wt = 65*span + 250
    ct_rail_wt_per_m = get_rail_wt(ct_rail_name)
    ct_rail_wt_total = ct_rail_wt_per_m * span * 2
    Wcrane_final = 2*Wg + ec_sol['Wec_total'] + wtrolley_t*1000 + lt_res['total_wt_kg'] + ct_res['total_wt_kg'] + 100 + platform_wt + ct_rail_wt_total

    lt_res_final=get_lt_wheel(swl_t=swl, wcrane_t=Wcrane_final/1000, n_ltw=n_ltw, lt_rail_name=lt_rail_name, duty=duty)
    if lt_res_final['d_sel_mm']!=lt_res['d_sel_mm']:
        st.warning(f"LT changed: {lt_res['d_sel_mm']} -> {lt_res_final['d_sel_mm']}mm")
        lt_res=lt_res_final
        Wcrane_final = 2*Wg + ec_sol['Wec_total'] + wtrolley_t*1000 + ct_res['total_wt_kg'] + lt_res['total_wt_kg'] + 100 + platform_wt + ct_rail_wt_total
        st.write(f"Wcrane TOTOL {Wcrane_final:.0f}Kg")

    Pmax_kg, Ha = calc_pmax(swl, span, wtrolley_t, Wcrane_final, TG_cm, n_ltw)

    st.divider()
    st.subheader("========== FINAL SUMMARY ==========")
    colA,colB,colC=st.columns(3)
    with colA:
        st.metric("Duty", duty)
        st.metric("IMPACT / DF", f"{impact} / {duty_f}")
        st.metric("Box H", f"{box_sol['H']:.1f} cm")
        st.metric("Wg 1 girder kg", f"{Wg:.0f}")
        st.metric("EC H", f"{ec_sol['H']:.1f}")
    with colB:
        st.metric("LT Rail STORED", lt_rail_name)
        st.metric("LT Wheel Dia", f"{lt_res['d_sel_mm']} mm")
        st.metric("CT Rail STORED", ct_rail_name)
        st.metric("CT Wheel Dia", f"{ct_res['d_sel_mm']} mm")
        st.metric("CT Rail wt", f"{ct_rail_wt_total:.0f} kg ({ct_rail_wt_per_m} kg/m x {span}m x2)")
        st.metric("Platform wt", f"{platform_wt:.0f} kg (65*span+250)")
    with colC:
        st.metric("Wcrane FINAL kg", f"{Wcrane_final:.0f}")
        st.metric("Wcrane T", f"{Wcrane_final/1000:.2f}")
        st.metric("Ha m", f"{Ha:.3f}")
        st.success(f"Pmax Static = {Pmax_kg:.0f} kg = {Pmax_kg/1000:.3f} T")

    st.code(f"Wcrane = 2*Wg({2*Wg:.0f}) + Wec({ec_sol['Wec_total']:.0f}) + Wtrolley({wtrolley_t*1000:.0f}) + LTwt({lt_res['total_wt_kg']:.0f}) + CTwt({ct_res['total_wt_kg']:.0f}) +100 + Platform({platform_wt:.0f}) + CTRail({ct_rail_wt_total:.0f}) = {Wcrane_final:.0f}Kg", language="text")
    # st.write(f"**Formula: Pmax (Static wheel load without impact) = (swl+wtrolley)*(span+Ha)/((n_ltw/2)*span) + (WC_T-wtrolley)/n_ltw**")
    st.write(f"**Pmax (Static wheel load without impact) = {Pmax_kg:.0f} kg = {Pmax_kg/1000:.3f} T Ha={Ha:.3f}m**")
    # import streamlit as st

USERS = {
    "admin": "Owner@ceo",
    "designer": "Crane@2025",
    "vinays": "Vinay@2026",
    "vikasm": "Vikas@2026"
}

st.set_page_config(page_title="DGEOT ESTIMATION SUITE", layout="wide")

@st.cache_data
def get_factors_cached(cls):
    base={"M1":1.06,"M2":1.12,"M3":1.18,"M4":1.25,"M5":1.32,"M6":1.4,"M7":1.5,"M8":1.5}
    duty={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.05,"M5":1.06,"M6":1.1,"M7":1.12,"M8":1.2}
    return base.get(cls.strip().upper(),1.32), duty.get(cls.strip().upper(),1.06)

@st.cache_data
def get_rail_wt_cached(rail_name):
    RAIL_WT_MAP={"50x50":19.625,"60x40":18.84,"60x60":28.26,"LBS60":30.0,"LBS75":37.5,"LBS90":45.0,"LBS105":52.0,"LBS120":60.0,"CR80":64.24,"CR100":89.0}
    rn=rail_name.strip().lower().replace(" ","")
    norm={k.lower().replace(" ",""):v for k,v in RAIL_WT_MAP.items()}
    return norm.get(rn,19.625)

@st.cache_data
def get_rail_by_swl_cached(swl):
    RAIL_MASTER=[{"swl":5,"rail":"50x50"},{"swl":7.5,"rail":"50x50"},{"swl":10,"rail":"60x40"},{"swl":12.5,"rail":"60x40"},{"swl":15,"rail":"60x60"},{"swl":20,"rail":"60x60"},{"swl":25,"rail":"LBS60"},{"swl":30,"rail":"LBS75"},{"swl":32,"rail":"LBS90"},{"swl":35,"rail":"LBS90"},{"swl":40,"rail":"LBS105"},{"swl":45,"rail":"LBS120"},{"swl":50,"rail":"LBS120"}]
    for r in RAIL_MASTER:
        if swl<=r["swl"]: return r
    return RAIL_MASTER[-1]

@st.cache_data(show_spinner=False)
def cached_box_girder(SWL_T, SPAN_M, duty):
    # ... full box girder with next thickness upgrade (cached)

@st.cache_data
def cached_pmax_static(swl, span, wtrolley_t, WC_T, TG_cm, n_ltw):
    TG_M=TG_cm/100.0
    Ha=max(1.0, TG_M*0.5)
    Pmax_T=(swl+wtrolley_t)*(span+Ha)/((n_ltw/2)*span)+(WC_T-wtrolley_t)/n_ltw
    return Pmax_T*1000, Ha

# LOGIN with CACHE
if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
    
if not st.session_state.logged_in:
    # login page
    st.stop()

# # LOGOUT KEEP CACHE
# if st.sidebar.button("Logout (Keep Cache) ⚡"):
#     st.session_state.logged_in=False
#     st.rerun()  # cache stays
# if st.sidebar.button("Logout + Clear Cache"):
#     st.session_state.logged_in=False
#     st.cache_data.clear()
#     st.rerun()
