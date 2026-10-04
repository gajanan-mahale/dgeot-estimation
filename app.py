import streamlit as st
from datetime import datetime
import json, os
from wire_rope import select_rope, calc_rope_length_weight
from ct_machinery import get_drum
from ct_wheel_cal import get_wheel_full as get_ct_wheel
from lt_wheel_cal import get_lt_wheel_full as get_lt_wheel
from main_dg_box import get_box_girder
from end_carriage_dg import get_end_carriage
from LT_Motor_file import calc_ltm, calc_ctm

USERS = {
    "admin": "Owner@ceo",
    "designer": "Crane@2025",
    "pratik": "Avpin@7878",
    "vinays": "Vinay@2026",
    "vikasm": "Vikas@2026"
}
TEMP_USERS = {
    "client01": {"pwd": "Client@Oct01Exp", "expiry": datetime(2026, 10, 3, 23, 59, 0)}
}
GUEST_TRACK_FILE = "/tmp/used_guest.json"

def is_guest_used(uid):
    if not os.path.exists(GUEST_TRACK_FILE): return False
    try:
        with open(GUEST_TRACK_FILE,"r") as f: data=json.load(f)
        return uid in data.get("used",[])
    except: return False

def mark_guest_used(uid):
    data={"used":[]}
    if os.path.exists(GUEST_TRACK_FILE):
        try:
            with open(GUEST_TRACK_FILE,"r") as f: data=json.load(f)
        except: pass
    if uid not in data["used"]: data["used"].append(uid)
    with open(GUEST_TRACK_FILE,"w") as f: json.dump(data,f)

st.set_page_config(page_title="DGEOT CRANE ESTIMATION SUITE", layout="wide", page_icon="🏗️")

RAIL_MASTER = [
    {"swl":5,"rail":"50x50","wt":19.625},{"swl":7.5,"rail":"50x50","wt":19.625},
    {"swl":10,"rail":"60x40","wt":18.84},{"swl":12.5,"rail":"60x40","wt":18.84},
    {"swl":15,"rail":"60x60","wt":28.26},{"swl":20,"rail":"60x60","wt":28.26},
    {"swl":25,"rail":"LBS60","wt":30.0},{"swl":30,"rail":"LBS75","wt":37.5},
    {"swl":32,"rail":"LBS90","wt":45.0},{"swl":35,"rail":"LBS90","wt":45.0},
    {"swl":40,"rail":"LBS105","wt":52.0},{"swl":45,"rail":"LBS120","wt":60.0},
    {"swl":50,"rail":"CR80","wt":64.0},{"swl":75,"rail":"CR100","wt":89.0},
]
RAIL_WT_MAP = {"50x50":19.625,"60x40":18.84,"60x60":28.26,"LBS60":30.0,"LBS75":37.5,"LBS90":45.0,"LBS105":52.0,"LBS120":60.0,"CR80":64.24,"80":64.24,"CR100":89.0,"100":89.0}

def get_rail_wt(rail_name):
    rn = rail_name.strip().lower().replace(" ","")
    norm_map = {k.strip().lower().replace(" ",""):v for k,v in RAIL_WT_MAP.items()}
    for r in RAIL_MASTER:
        nk = r["rail"].strip().lower().replace(" ","")
        if nk not in norm_map: norm_map[nk] = r["wt"]
    rn2 = rn.replace("-","").replace("_","")
    return norm_map.get(rn, norm_map.get(rn2, 19.625))

def get_rail_by_swl(swl):
    for r in RAIL_MASTER:
        if swl <= r["swl"]: return r
    return RAIL_MASTER[-1]

def get_factors(cls):
    base={"M1":1.06,"M2":1.12,"M3":1.18,"M4":1.25,"M5":1.32,"M6":1.4,"M7":1.5,"M8":1.5}
    duty={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.05,"M5":1.06,"M6":1.1,"M7":1.12,"M8":1.2}
    service={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.1,"M5":1.01,"M6":1.1,"M7":1.2,"M8":1.2}
    Cdf = {"M1":1.0,"M2":1.06,"M3":1.12,"M4":1.18,"M5":1.25,"M6":1.32,"M7":1.4,"M8":1.5}
    cls = cls.strip().upper()
    return base.get(cls,1.32), duty.get(cls,1.06), service.get(cls,1), Cdf.get(cls,1.25)

def calc_pmax(swl, span, wtrolley_t, Wcrane_final, TG_cm, n_ltw):
    TG_M = TG_cm/100.0
    Ha = max(1.0, TG_M*0.5)
    WC_T = Wcrane_final/1000.0
    Pmax_T = (swl+wtrolley_t)*(span+Ha)/((n_ltw/2)*span) + (WC_T-wtrolley_t)/n_ltw
    return Pmax_T*1000, Ha

if "logged_in" not in st.session_state:
    st.session_state.logged_in=False
    st.session_state.user=""

def login_page():
    st.title("🔐 DGEOT CRANE ESTIMATION SUITE - Login")
    st.caption(f"Server Time: {datetime.now().strftime('%d-%m-%Y %H:%M')}")
    uid=st.text_input("Login ID")
    pwd=st.text_input("Password", type="password")
    if st.button("Login", type="primary", use_container_width=True):
        if uid in USERS and USERS[uid]==pwd:
            st.session_state.logged_in=True
            st.session_state.user=uid
            st.rerun()
        elif uid in TEMP_USERS:
            guest = TEMP_USERS[uid]
            now = datetime.now()
            if now > guest["expiry"]:
                st.error(f"Guest ID {uid} EXPIRED on {guest['expiry'].strftime('%d-%m %H:%M')}")
            elif is_guest_used(uid):
                st.error(f"Guest ID {uid} already used - One time only")
            elif guest["pwd"]==pwd:
                mark_guest_used(uid)
                st.session_state.logged_in=True
                st.session_state.user=uid+" (Guest - 1 Day One-Time)"
                st.success(f"Guest login OK - Expires {guest['expiry'].strftime('%d-%m %H:%M')}")
                st.rerun()
            else: st.error("Invalid Guest Password")
        else: st.error("Invalid ID or Password")

if not st.session_state.logged_in:
    login_page()
    st.stop()

st.sidebar.success(f"Welcome {st.session_state.user.upper()} Sir! 👋")
st.sidebar.title("DGEOT CRANE SUITE")
if st.sidebar.button("Logout", key="logout_unique", use_container_width=True):
    st.session_state.logged_in=False
    st.rerun()

st.title("🏗️ DGEOT CRANE ESTIMATION SUITE")
st.caption("BY : GAJANAN MAHALE")

c1,c2,c3,c4=st.columns(4)
with c1:
    swl=st.number_input("Enter SWL (T) [10]", value=10.0, step=0.5)
    span=st.number_input("Enter Span (m) [20]", value=20.0, step=0.5)
    lift=st.number_input("Enter Lift Height (m) [10]", value=10.0, step=0.5)
    v_ltm = st.selectbox("LT Speed V mpm [15]", list(range(10, 26, 1)), index=5)
with c2:
    duty=st.selectbox("Enter Duty M1-M8 [M5]", ["M1","M2","M3","M4","M5","M6","M7","M8"], index=4)
    falls=st.number_input("Enter No. of Falls [4]", value=4.0, step=1.0)
    core=st.selectbox("Enter core steel/fiber [fiber]", ["fiber","steel"], index=0)
    v_ctm = st.selectbox("CT Speed V mpm [10]", list(range(10, 21, 1)), index=0)
    reeving=2
with c3:
    auto=get_rail_by_swl(swl)
    lt_rail_name=st.selectbox(f"Enter LT Rail [{auto['rail']}]", ["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"])
    ct_rail_name=st.selectbox(f"Enter CT Rail [{lt_rail_name}]", ["50x50","60x40","60x60","LBS60","LBS75","LBS90","LBS105","LBS120","CR80","CR100"])
    st.write(f"Auto rail for SWL {swl}T = {auto['rail']}")
    Tamb = st.selectbox("Tamb / Camb deg C [45]", list(range(40, 61, 5)), index=1)
    n_ct_motors = st.selectbox("No. of CT Motors [1]", [1, 2], index=0)
with c4:
    wt_def=round(0.2*swl,2)
    wtrolley_t=st.number_input(f"Enter W Trolley (T) [{wt_def}]", value=float(wt_def), step=0.1)
    n_ctw=st.number_input("Enter No of CT wheels [4]", value=4, min_value=2, max_value=16, step=2)
    n_ltw=st.number_input("Enter No of LT wheels [4]", value=4, min_value=4, max_value=16, step=2)

impact,duty_f,service_f,cdf_f=get_factors(duty)
st.write(f"Duty {duty} -> IMPACT={impact} DF={duty_f} SERVICE={service_f} Cdf={cdf_f} | LT={lt_rail_name} CT={ct_rail_name} | V_LT={v_ltm} V_CT={v_ctm} N_CT_Mot={n_ct_motors} Tamb={Tamb}")

if st.button("Run FULL SUITE Calculation", type="primary", use_container_width=True):
    rope_res=select_rope(swl,falls,duty,core)
    sel=rope_res["selected"]
    length,wt=calc_rope_length_weight(lift,falls,sel["wt_kg_100m"])
    final_dia=sel["dia"]
    st.subheader("--- WIRE ROPE ---")
    st.write(f"Selected Rope: {final_dia} mm, FOS {rope_res['actual_fos']:.2f} | Length {length:.1f}m Wt {wt:.1f}kg")
    drum_res=get_drum(swl,final_dia,lift,falls,reeving,duty)
    drum_len=drum_res['drum_length_mm']
    st.subheader("--- CT DRUM ---")
    st.write(f"Drum {drum_res['drum_od']} dia X {drum_res['drum_thk_mm']} thk X {drum_len} length")
    TG_cm=(drum_len+1200)/10
    st.subheader(f"Trolley Gauge TG={TG_cm:.0f}cm")
    ct_res=get_ct_wheel(swl_t=swl, wtrolley_t=wtrolley_t, n_ctw=n_ctw, ct_rail_name=ct_rail_name, duty=duty)
    st.subheader(f"--- CT WHEEL Rail={ct_rail_name} ---")
    st.write(f"CT: Dmin={ct_res['dmin_mm']}mm -> Selected={ct_res['d_sel_mm']}mm Wt={ct_res['total_wt_kg']}Kg")
    st.subheader("--- DG BOX GIRDER ---")
    box_sol=get_box_girder(SWL_T=swl, SPAN_M=span, duty=duty, IMPACT=impact, DF=duty_f)
    if not box_sol:
        st.error("No box girder solution")
        st.stop()
    Wg=box_sol['Wg']
    st.write(f"Box Girder: H={box_sol['H']:.1f}cm Wt of 1 girder={Wg:.0f}Kg")
    st.subheader("--- END CARRIAGE ---")
    P=(swl*1000 + wtrolley_t*1000)/2
    ec_sol=get_end_carriage(SWL_T=swl, SPAN_M=span, Wg=Wg, P_override=P, WT_HOIST_override=wtrolley_t*1000, TG_cm=TG_cm, duty=duty, IMPACT=impact, DF=duty_f, rope_dia=final_dia, lift_m=lift, falls=falls, drum_length_mm=drum_len)
    if not ec_sol:
        st.error("No end carriage solution")
        st.stop()
    st.write(f"End Car: H={ec_sol['H']:.1f} cm Wec 1 NO={ec_sol['Wec_one']:.0f}Kg 2 NOS={ec_sol['Wec_total']:.0f}Kg Wt of crane est={ec_sol['WCRANE']:.0f}Kg")
    Wcrane_est=ec_sol['WCRANE']
    st.subheader(f"--- LT WHEEL Rail={lt_rail_name} ---")
    lt_res = get_lt_wheel(swl_t=swl, wcrane_t=Wcrane_est/1000, n_ltw=n_ltw, lt_rail_name=lt_rail_name, duty=duty, span_m=span, wtrolley_t=wtrolley_t, TG_cm=TG_cm)
    st.write(f"LT: Dmin={lt_res['dmin_mm']} -> Selected={lt_res['d_sel_mm']}mm Wt={lt_res['total_wt_kg']}Kg")
    platform_wt = 65*span + 250
    ct_rail_wt_total = get_rail_wt(ct_rail_name) * span * 2
    Wcrane_final = 2*Wg + ec_sol['Wec_total'] + wtrolley_t*1000 + lt_res['total_wt_kg'] + ct_res['total_wt_kg'] + 100 + platform_wt + ct_rail_wt_total
    lt_res_final=get_lt_wheel(swl_t=swl, wcrane_t=Wcrane_final/1000, n_ltw=n_ltw, lt_rail_name=lt_rail_name, duty=duty)
    if lt_res_final['d_sel_mm']!=lt_res['d_sel_mm']:
        lt_res=lt_res_final
        Wcrane_final = 2*Wg + ec_sol['Wec_total'] + wtrolley_t*1000 + ct_res['total_wt_kg'] + lt_res['total_wt_kg'] + 100 + platform_wt + ct_rail_wt_total
    Pmax_kg, Ha = calc_pmax(swl, span, wtrolley_t, Wcrane_final, TG_cm, n_ltw)

    LTM = calc_ltm(SWL_T=swl, v_mpm=v_ltm, duty=duty, Tamb=Tamb, WC_T=Wcrane_final/1000)
    CTM = calc_ctm(SWL_T=swl, v_ct_mpm=v_ctm, duty=duty, Tamb=Tamb, WTrolley_T=wtrolley_t, n_motors=n_ct_motors)

    st.divider()
    st.subheader("--- LT MOTOR ---")
    st.write(f"S={LTM['S']} Cdf={LTM['Cdf']} Camb={LTM['Camb']} M_rated={LTM['M_rated_T']} T | V={v_ltm} mpm")
    st.success(f"LT Motor Power = {LTM['KW_Mech_kW']} kW per motor X 2 NOS @ {v_ltm} mpm")

    st.subheader("--- CT MOTOR ---")
    st.write(f"S={CTM['S']} Cdf={CTM['Cdf']} Camb={CTM['Camb']} M_rated={CTM['M_rated_T']} T | V={v_ctm} mpm N={n_ct_motors}")
    if n_ct_motors == 1:
        st.success(f"CT Motor Power = {CTM['KW_Mech_kW']} kW X 1 NO @ {v_ctm} mpm")
    else:
        st.success(f"CT Motor Power = {CTM['KW_Mech_kW']} kW per motor X 2 NOS @ {v_ctm} mpm (Total {CTM['KW_Total_kW']} kW)")

    st.divider()
    st.subheader("========== FINAL SUMMARY ==========")
    colA,colB,colC=st.columns(3)
    with colA:
        st.metric("Duty", duty)
        st.metric("IMPACT / DF", f"{impact} / {duty_f}")
        st.metric("Box Ht", f"{box_sol['H']:.1f} cm")
        st.metric("Wt of 1 girder", f"{Wg:.0f} kg")
        st.metric("EC Height", f"{ec_sol['H']:.1f} cm")
    with colB:
        st.metric("LT Rail", lt_rail_name)
        st.metric("LT Wheel Dia", f"{lt_res['d_sel_mm']} mm")
        st.metric("CT Rail", ct_rail_name)
        st.metric("CT Wheel Dia", f"{ct_res['d_sel_mm']} mm")
        st.metric("CT Rail wt", f"{ct_rail_wt_total:.0f} kg")
    with colC:
        st.metric("Wt of Crane", f"{Wcrane_final:.0f} kg ")
        st.metric("Wt of Crane", f"{Wcrane_final/1000:.2f} Ton")
        st.metric("Ha ", f"{Ha:.3f} m")
        st.metric("Platform wt", f"{platform_wt:.0f} kg")
        st.success(f"Pmax = {Pmax_kg:.0f} kg = {Pmax_kg/1000:.3f} Ton")

    st.info(f"LT: {LTM['KW_Mech_kW']} kW x 2 | CT: {CTM['KW_Mech_kW']} kW x {n_ct_motors} @ Tamb {Tamb}C")
