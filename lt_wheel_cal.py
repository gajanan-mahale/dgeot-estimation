# lt_wheel_cal.py - LT Wheel Dia + Wt
# Everything same as CT, only Wtrolley replaced by Wcrane

RAIL_TOP = {
    "50x50": 50, "60x40": 60, "60x60": 60,
    "LBS60": 57.15, "LBS75": 61.91, "LBS90": 66.68,
    "LBS105": 71, "LBS120": 73,
    "CR80": 80, "CR100": 100,
}
WHEEL_STD = [130,160,200,250,320,400,500,630]
WHEEL_WT_SET = {130:80, 160:150, 200:200, 250:250, 320:500, 400:910, 500:1450, 630:2100}

C1_TABLE = [
    (200,0.66),(160,0.72),(125,0.77),(112,0.79),(100,0.82),
    (90,0.84),(80,0.87),(71,0.89),(63,0.91),(56,0.92),
    (50,0.94),(45,0.96),(40,0.97),(35.5,0.99),(31.5,1.0),
    (28,1.02),(25,1.03),(22.4,1.04),(20,1.06),(18,1.07),
    (16,1.09),(14,1.10),(12.5,1.11),(11.2,1.12),(10,1.13),
    (8,1.14),(6.3,1.15),(5.6,1.16),(5,1.17),
]

def get_c1(rpm):
    for r,c in C1_TABLE:
        if abs(r-rpm)<0.001: return c
    sd=sorted(C1_TABLE,key=lambda x:-x[0])
    if rpm>=sd[0][0]: return sd[0][1]
    if rpm<=sd[-1][0]: return sd[-1][1]
    for i in range(len(sd)-1):
        r1,c1=sd[i]; r2,c2=sd[i+1]
        if r1>=rpm>=r2:
            ratio=(r1-rpm)/(r1-r2) if r1!=r2 else 0
            return c1+ratio*(c2-c1)
    return 1.0

def get_c2(duty):
    d=duty.upper()
    if d in ["M1","M2","M3","M4","M5"]: return 1.0
    elif d=="M6": return 0.9
    else: return 0.8

PL=7.8

def get_lt_wheel_full(swl_t, wcrane_t, n_ltw, lt_rail_name, duty):
    # Wcrane replaces Wtrolley
    if wcrane_t is None or wcrane_t==0:
        wcrane_t = 0.35*swl_t + 5 # placeholder, you will calculate afterwards

    pmax=((swl_t*1.03 + wcrane_t)/n_ltw)*1.3*1000
    pmin_total=wcrane_t*0.33*1000
    pmin_w=pmin_total/n_ltw
    pmean_kg=(2*pmax+pmin_w)/3
    pmean_n=pmean_kg*9.81

    lookup={k.upper().replace(" ",""):v for k,v in RAIL_TOP.items()}
    key=lt_rail_name.strip().upper().replace(" ","")
    top=lookup.get(key,60)
    a=top-2
    rpm=140 if swl_t<15 else 25
    c1=get_c1(rpm)
    c2=get_c2(duty)
    dmin=pmean_n/(PL*a*c1*c2)
    d_sel=next((d for d in WHEEL_STD if d>=dmin), WHEEL_STD[-1])

    wt_per_set=WHEEL_WT_SET.get(d_sel,0)
    total_wt=wt_per_set*(n_ltw/4)

    return {
        "swl_t":swl_t,"wcrane_t":round(wcrane_t,3),"n_ltw":n_ltw,
        "lt_rail":lt_rail_name,"rail_top":top,"a_mm":round(a,2),
        "pmax_kg":round(pmax,1),"pmin_wheel_kg":round(pmin_w,1),
        "pmean_kg":round(pmean_kg,1),"pmean_n":round(pmean_n,1),
        "rpm":rpm,"c1":round(c1,4),"c2":c2,
        "dmin_mm":round(dmin,1),"d_sel_mm":d_sel,
        "wt_per_set_kg":wt_per_set,"total_wt_kg":round(total_wt,1),
        "wt_per_wheel_kg":round(wt_per_set/4,1)
    }