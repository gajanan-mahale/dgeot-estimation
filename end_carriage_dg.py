# end_carriage_dg.py / end_carriage_dgr.py - FINAL SUITE
# IMPACT, DF from dgcrane_suite.py + TG_cm from ct_machinery (drum+1000) or user input

import numpy as np

# --- TRY IMPORT FROM SUITE ---
try:
    from dgcrane_suite import get_factors as suite_get_factors
    HAS_SUITE = True
except ImportError:
    try:
        from eot_crane import get_factors as suite_get_factors
        HAS_SUITE = False
    except:
        HAS_SUITE = False
        def suite_get_factors(cls):
            impact_map={"M1":1.06,"M2":1.12,"M3":1.18,"M4":1.25,"M5":1.32,"M6":1.4,"M7":1.4,"M8":1.5}
            duty_map={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.05,"M5":1.06,"M6":1.1,"M7":1.12,"M8":1.2}
            return impact_map.get(cls,1.32), duty_map.get(cls,1.06)

from main_dg_box import get_box_girder

try:
    from ct_machinery import get_drum
    HAS_CT_MACH = True
except ImportError:
    HAS_CT_MACH = False
    get_drum = None

def calc_tg_from_drum(SWL_T, rope_dia=None, lift_m=10, falls=4, reeving=2, duty="M5", drum_length_mm=None):
    """ TG = drum_length_mm + 1000 mm -> TG_cm = /10 """
    if drum_length_mm is not None:
        return (drum_length_mm + 1000)/10
    if HAS_CT_MACH and rope_dia is not None:
        try:
            drum = get_drum(SWL_T, rope_dia, lift_m, falls, reeving, duty)
            return (drum['drum_length_mm'] + 1000)/10
        except:
            pass
    return 300

def get_end_carriage(
    SWL_T,
    SPAN_M,
    Wg=None,
    P_override=None,
    WT_HOIST_override=None,
    TG_cm=None, # None = auto from ct_machinery, 300 = user input
    duty="M5",
    IMPACT=None,
    DF=None,
    W_CT_override=None,
    W_PLFM_override=None,
    rope_dia=None, # for TG auto
    lift_m=10,
    falls=4,
    reeving=2,
    drum_length_mm=None, # direct from ct_machinery
    E=2.1e6
):
    '''
    Inputs from dgcrane_suite.py:
    - SWL_T, SPAN_M, Wg, P, WT_HOIST, TG_cm, duty, IMPACT, DF
    - TG_cm: if None -> auto from ct_machinery.get_drum()
    - IMPACT, DF: if None -> from suite_get_factors(duty)
    '''
    SWL = SWL_T*1000
    SPAN = SPAN_M*100
    WT_HOIST = WT_HOIST_override if WT_HOIST_override is not None else 0.2*SWL
    P = P_override if P_override is not None else (SWL + WT_HOIST)/2

    if Wg is None:
        sol_box = get_box_girder(SWL_T, SPAN_M, W_CT_override, W_PLFM_override)
        Wg = sol_box['Wg'] if sol_box else 0

    # IMPACT & DF from dgcrane_suite.py
    if IMPACT is None or DF is None:
        imp, df = suite_get_factors(duty)
        if IMPACT is None: IMPACT = imp
        if DF is None: DF = df

    # TG from ct_machinery OR user input
    if TG_cm is None:
        TG_cm = calc_tg_from_drum(SWL_T, rope_dia, lift_m, falls, reeving, duty, drum_length_mm)

    TG = TG_cm
    wheelbase = TG + 150
    L_EC = wheelbase + 50
    ALLOW_DEF_THEO = wheelbase / 750
    ALLOW_DEF = ALLOW_DEF_THEO - 0.025
    BT_ALLOW = 38

    if SWL_T <= 10:
        t_top_list = [0.8, 1.0, 1.2, 1.6]
        t_bot_list = [0.6, 0.8, 1.0, 1.2, 1.6]
        t_web_list = [0.6, 0.8]
        h_start, h_end, h_step = 27, 60, 1
        b_add_max = 6
        B_INSIDE_BASE = 25
    elif SWL_T <= 25:
        t_top_list = [1.2, 1.6, 2.0, 2.5]
        t_bot_list = [0.8, 1.0, 1.2, 1.6, 2.0]
        t_web_list = [0.8, 1.0, 1.2]
        h_start, h_end, h_step = 27, 65, 2
        b_add_max = 10
        B_INSIDE_BASE = 30
    else:
        t_top_list = [1.6, 2.0, 2.5, 3.2]
        t_bot_list = [1.0, 1.2, 1.6, 2.0, 2.5, 3.2]
        t_web_list = [0.8, 1.0, 1.2, 1.6, 2.0]
        h_start, h_end, h_step = 30, 100, 2
        b_add_max = 15
        B_INSIDE_BASE = 30

    def calc_sect(t_top_in, b_inside_in, t_bot_in, t_web_in, h_web_in):
        t_top = t_top_in; t_bot = t_bot_in; t_web = t_web_in; h_web = h_web_in
        b_inside = round(b_inside_in)
        if b_inside / t_top > BT_ALLOW: return None
        b_top = b_inside + 5; b_bot = b_top; H = t_top + h_web + t_bot
        if L_EC / H >= 25: return None
        A_top = b_top * t_top; A_bot = b_bot * t_bot; A_web = 2 * h_web * t_web
        A = A_top + A_bot + A_web
        y_top = H - t_top/2; y_bot = t_bot/2; y_web = t_bot + h_web/2
        Y_bar = (A_top*y_top + A_bot*y_bot + A_web*y_web) / A
        I_web_self = 2 * (t_web * h_web**3)/12
        Ixx = ( A_top*(y_top-Y_bar)**2 + A_bot*(Y_bar-y_bot)**2 + I_web_self )
        Iyy_top = (t_top * b_top**3)/12; Iyy_bot = (t_bot * b_bot**3)/12
        Iyy_web = 2 * (h_web*t_web)*(b_inside/2 + t_web/2)**2
        Iyy = Iyy_top + Iyy_bot + Iyy_web
        Z_top = Ixx / (H - Y_bar); Z_bot = Ixx / Y_bar; Z_yy = Iyy / (b_bot/2)
        W_plates = A * L_EC * 0.00785 * 1.05
        W_diaphragm = h_web * b_inside * 0.6 * 0.007854 * L_EC * 1.9/100
        Wec = (W_plates + W_diaphragm +125 ) * 1.1
        M = P*75*IMPACT + Wec*L_EC/8
        delta_live = (P*L_EC**3)/(48*E*Ixx)
        VMAX = IMPACT*(P + Wg)
        s_top = M / Z_top; s_bot = M / Z_bot; s_lat = (M*0.05) / Z_yy; s_web = VMAX/A_web
        return {
            'b_top':b_top,'b_bot':b_bot,'b_inside':b_inside,
            't_top':t_top,'t_bot':t_bot,'t_web':t_web,'h_web':h_web,'H':H,
            'Wec':Wec,'M':M,'delta_live':delta_live,'s_top_comb':s_top+s_lat,'s_bot_comb':s_bot+s_lat,
            'ok_top_comb':(s_top+s_lat) < 1230,'ok_bot_comb':(s_bot+s_lat) < 1530,
            'bt_ratio':b_inside/t_top,'bt_ok':b_inside/t_top <= 38,
            'ALLOW_DEF': ALLOW_DEF, 'ALLOW_THEO': ALLOW_DEF_THEO, 'B_BASE': B_INSIDE_BASE,
            'ok_s_web':(s_web)<1100, 'VMAX':VMAX, 'GIRDER_WT':Wg, 's_web':s_web,
            'wheelbase':wheelbase, 'TG':TG, 'L_EC':L_EC, 'IMPACT':IMPACT, 'DF':DF
        }

    solution = None
    for t_web in t_web_list:
        if solution: break
        for t_bot in t_bot_list:
            if solution: break
            allowed_t_top = [t for t in t_top_list if t < (2*t_bot - 0.001)] if abs(t_bot-0.6)<0.001 else t_top_list
            for b_add in range(0, b_add_max):
                if solution: break
                b_inside = B_INSIDE_BASE + b_add
                for t_top in allowed_t_top:
                    if solution: break
                    for h_web in range(h_start, h_end, h_step):
                        r = calc_sect(t_top, b_inside, t_bot, t_web, h_web)
                        if r is None: continue
                        if r['ok_top_comb'] and r['ok_bot_comb'] and r['bt_ok'] and r['delta_live'] <= ALLOW_DEF:
                            solution = r
                            break
    if not solution:
        return None

    r = solution
    Wec_one = r['Wec']
    Wec_tot = 2*Wec_one
    WCRANE = 2*Wg + 2*Wec_one + WT_HOIST + 100 + 250
    W_L = (P/4)*(SPAN-100)/SPAN + (WCRANE-WT_HOIST)/4
    r['Wec_one']=Wec_one
    r['Wec_total']=Wec_tot
    r['WCRANE']=WCRANE
    r['W_L']=W_L
    r['SWL_T']=SWL_T
    r['SPAN_M']=SPAN_M
    r['WT_HOIST']=WT_HOIST
    r['P']=P
    r['Wg']=Wg
    return r

def get_end_carriage_dgr(*args, **kwargs):
    return get_end_carriage(*args, **kwargs)

if __name__ == "__main__":
    SWL_T = float(input("ENTER SWL IN TON :"))
    SPAN_M = float(input("ENTER SPAN IN METERS:"))
    duty = input("ENTER DUTY M1-M8 [M5]:").strip() or "M5"
    imp, df = suite_get_factors(duty)
    print(f"Using IMPACT={imp} DF={df} from dgcrane_suite.py / duty {duty}")

    # TG - user input OR auto from ct_machinery
    tg_in = input("ENTER TROLLEY GAUGE CM [blank=auto from ct_machinery]:").strip()
    if tg_in:
        TG = float(tg_in)
        drum_len = None
        rope_dia = None
    else:
        if HAS_CT_MACH:
            rope_dia = float(input("ENTER ROPE DIA mm for TG auto [16]:") or 16)
            lift_m = float(input("ENTER LIFT m [10]:") or 10)
            falls = float(input("ENTER FALLS [4]:") or 4)
            drum = get_drum(SWL_T, rope_dia, lift_m, falls, 2, duty)
            drum_len = drum['drum_length_mm']
            TG = (drum_len + 1000)/10
            print(f"TG auto = (drum {drum_len} +1000)/10 = {TG:.1f}cm")
        else:
            TG = 300

    box = get_box_girder(SWL_T, SPAN_M)
    Wg = box['Wg'] if box else 0
    P = (SWL_T*1000 + 0.2*SWL_T*1000)/2
    WT_HOIST = 0.2*SWL_T*1000

    sol = get_end_carriage(SWL_T, SPAN_M, Wg, P, WT_HOIST, TG_cm=TG, duty=duty, IMPACT=imp, DF=df)

    if sol:
        print(f"\nWheelbase={sol['wheelbase']}cm TG {sol['TG']}cm IMPACT {sol['IMPACT']}")
        print(f"FOR END CARRIAGE : Ttop={sol['t_top']} Btop={sol['b_top']} Tbot={sol['t_bot']} Bbot={sol['b_bot']} Binside={sol['b_inside']} H={sol['H']:.1f} s_web={sol['s_web']:.0f}")
        print(f"Wt 1 Girder {Wg:.0f}Kg Wec 1 {sol['Wec_one']:.0f}Kg Total {sol['Wec_total']:.0f}Kg Wcrane {sol['WCRANE']:.0f}Kg WL {sol['W_L']:.0f}Kg")
    else:
        print("No solution, try boggie design")