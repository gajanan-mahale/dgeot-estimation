# LT_Motor_file.py - FINAL WITH LT + CT MOTOR
def get_factors(cls):
    base={"M1":1.06,"M2":1.12,"M3":1.18,"M4":1.25,"M5":1.32,"M6":1.4,"M7":1.5,"M8":1.5}
    duty={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.05,"M5":1.06,"M6":1.1,"M7":1.12,"M8":1.2}
    service={"M1":1.0,"M2":1.0,"M3":1.0,"M4":1.1,"M5":1.01,"M6":1.1,"M7":1.2,"M8":1.2}
    Cdf = {"M1":1.0,"M2":1.06,"M3":1.12,"M4":1.18,"M5":1.25,"M6":1.32,"M7":1.4,"M8":1.5}
    cls = cls.strip().upper()
    return base.get(cls,1.32), duty.get(cls,1.06), service.get(cls,1), Cdf.get(cls,1.25)

def get_camb(Tamb):
    return {40:1.0,45:0.95,50:0.88,55:0.83,60:0.75}.get(Tamb,0.95)

def calc_ltm(SWL_T, v_mpm, duty, Tamb, WC_T, F=8, T=1.7, a=9, Eff=0.86):
    IMPACT,S,SERVICE,Cdf = get_factors(duty)
    Camb = get_camb(Tamb)
    M_rated = 1.03*SWL_T + WC_T
    term1 = (M_rated * v_mpm * S * Cdf) / (6117 * T * Camb)
    term2 = F + (1100 * a / (981 * Eff))
    KW_Mech = 0.66 * term1 * term2
    return {"S":S,"Cdf":Cdf,"Camb":Camb,"IMPACT":IMPACT,"SERVICE":SERVICE,"M_rated_T":round(M_rated,3),"KW_Mech_kW":round(KW_Mech,3)}

def calc_ctm(SWL_T, v_ct_mpm, duty, Tamb, WTrolley_T, n_motors=1, F=8, T=1.7, a=9, Eff=0.86):
    IMPACT,S,SERVICE,Cdf = get_factors(duty)
    Camb = get_camb(Tamb)
    M_rated = SWL_T + WTrolley_T
    term1 = (M_rated * v_ct_mpm * S * Cdf) / (6117 * T * Camb)
    term2 = F + (1100 * a / (981 * Eff))
    KW_Total = term1 * term2
    if n_motors == 2:
        KW_per_motor = 0.66 * KW_Total
    else:
        KW_per_motor = KW_Total
    return {"S":S,"Cdf":Cdf,"Camb":Camb,"IMPACT":IMPACT,"SERVICE":SERVICE,"M_rated_T":round(M_rated,3),"KW_Total_kW":round(KW_Total,3),"KW_Mech_kW":round(KW_per_motor,3),"n_motors":n_motors}
