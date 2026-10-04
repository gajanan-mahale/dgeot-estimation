# KW_Mech AS PER IS:3177(2020)

def get_factors(duty, Tamb):
    duty = duty.upper().strip()
    
    # S factor
    if duty == "M6":
        S = 1.1
    elif duty == "M7":
        S = 1.1
    elif duty == "M8":
        S = 1.2
    else: # M3, M4, M5
        S = 1.0

    # Cdf factor
    cdf_map = {
        "M5": 1.25,
        "M6": 1.32,
        "M7": 1.4,
        "M8": 1.5
    }
    Cdf = cdf_map.get(duty, 1.25) # 1.18 for M4, 1.12 for M3 as per standard

    # Camb factor - Ambient temp correction
    camb_map = {
        40: 1.0,
        45: 0.95,
        50: 0.88,
        55: 0.83,
        60: 0.75
    }
    Camb = camb_map.get(Tamb, 0.95)
    if Tamb not in camb_map:
        print(f"Warning: Tamb {Tamb} not standard, using Camb=1.0")
        
    return S, Cdf, Camb

def calc_ltm(SWL_T, v_mpm, duty, Tamb, WC_T, F=8, T=1.7, a=9, Eff=0.86):
    """
    SWL_T : tonn
    v_mpm : velocity in m/min
    WC_T : Weight of crane in tonn final
    """
    S, Cdf, Camb = get_factors(duty, Tamb)
    
    # Rated mass
    M_rated = 1.03 * SWL_T + WC_T
    M = M_rated # in Tonne for formula
    V = v_mpm
    
   # Formula: KW_Mech = (M*V*S*Cdf / 6.117 * T * Camb) * (F + (1100*a / 981*Eff))
    
    term1 = (M * V * S * Cdf) / (6117 * T * Camb)
    term2 = F + (1100 * a / (981 * Eff))
    
    KW_Mech = 0.66 * term1 * term2   # No. of LT motors are always 2
    
    return {
        "S": S,
        "Cdf": Cdf,
        "Camb": Camb,
        "M_rated_T": round(M_rated, 3),
        "KW_Mech_kW": round(KW_Mech, 3),
    }

# ========= HOW TO USE IN dgsuit.py =========
if __name__ == "__main__":
    # Example inputs from dgsuit.py
    SWL_T = 20
    v = 15 # mpm
    duty = "M5"
    Tamb = 45
    w_crane = 16.86 # tonn

    result = calc_ltm(SWL_T, v, duty, Tamb, w_crane)
    print("LT motor power = ",result['KW_Mech_kW'], "kw")







