# ct_wheel_cal.py - CT Wheel Dia + Wt - FINAL

RAIL_TOP = {
    "50x50": 50,
    "60x40": 60,
    "60x60": 60,
    "LBS60": 57.15,
    "LBS75": 61.91,
    "LBS90": 66.68,
    "LBS105": 71,
    "LBS120": 73,
    "CR80": 80,
    "CR100": 100,
    "CR 80": 80,
    "CR 100": 100,
}
WHEEL_STD = [130,160,200,250,320,400,500,630]

# Wt of 1 set = 4 wheels (from your pic)
WHEEL_WT_SET = {
    130: 80,
    160: 150,
    200: 200,
    250: 250,
    320: 500,
    400: 910,
    500: 1450,
    630: 2100,
}

C1_TABLE = [
    (200, 0.66), (160, 0.72), (125, 0.77), (112, 0.79), (100, 0.82),
    (90, 0.84), (80, 0.87), (71, 0.89), (63, 0.91), (56, 0.92),
    (50, 0.94), (45, 0.96), (40, 0.97), (35.5, 0.99), (31.5, 1.0),
    (28, 1.02), (25, 1.03), (22.4, 1.04), (20, 1.06), (18, 1.07),
    (16, 1.09), (14, 1.10), (12.5, 1.11), (11.2, 1.12), (10, 1.13),
    (8, 1.14), (6.3, 1.15), (5.6, 1.16), (5, 1.17),
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

def get_wheel_full(swl_t, wtrolley_t, n_ctw, ct_rail_name, duty):
    if wtrolley_t is None or wtrolley_t==0:
        wtrolley_t=0.2*swl_t
    pmax=((swl_t*1.03+wtrolley_t)/n_ctw)*1.3*1000
    pmin_total=wtrolley_t*0.33*1000
    pmin_w=pmin_total/n_ctw
    pmean_kg=(2*pmax+pmin_w)/3
    pmean_n=pmean_kg*9.81

    key=ct_rail_name.strip().upper().replace(" ","")
    lookup={k.upper().replace(" ",""):v for k,v in RAIL_TOP.items()}
    top=lookup.get(key,60)
    if key not in lookup:
        for k,v in lookup.items():
            if k in key or key in k:
                top=v; break
    a=top-2
    rpm=140 if swl_t<15 else 25
    c1=get_c1(rpm)
    c2=get_c2(duty)
    dmin=pmean_n/(PL*a*c1*c2)
    d_sel=next((d for d in WHEEL_STD if d>=dmin), WHEEL_STD[-1])

    wt_per_set=WHEEL_WT_SET.get(d_sel,0)
    if n_ctw==4:
        total_wt=wt_per_set*1
        sets=1
    elif n_ctw==8:
        total_wt=wt_per_set*2
        sets=2
    else:
        total_wt=wt_per_set*(n_ctw/4)
        sets=n_ctw/4

    return {
        "swl_t":swl_t,"wtrolley_t":round(wtrolley_t,3),"n_ctw":n_ctw,
        "ct_rail":ct_rail_name,"rail_top":top,"a_mm":round(a,2),
        "pmax_kg":round(pmax,1),"pmin_wheel_kg":round(pmin_w,1),
        "pmean_kg":round(pmean_kg,1),"pmean_n":round(pmean_n,1),
        "rpm":rpm,"c1":round(c1,4),"c2":c2,"pl":PL,
        "dmin_mm":round(dmin,1),"d_sel_mm":d_sel,
        "wt_per_set_kg":wt_per_set,"sets":sets,"total_wt_kg":round(total_wt,1),
        "wt_per_wheel_kg":round(wt_per_set/4,1) if wt_per_set else 0
    }

def main():
    print("========== CT WHEEL DIA + WT CALC ==========")
    swl=float(input("Enter SWL (T) [10]: ") or 10)
    wt_def=round(0.2*swl,2)
    wt=float(input(f"Enter W Trolley (Ton) [{wt_def}]: ") or wt_def)
    n=int(input("Enter No of CT wheels [4]: ") or 4)
    print(f"Available rails: {list(RAIL_TOP.keys())[:8]} + CR80=80, CR100=100")
    rail=input("Enter CT Rail [50x50]: ").strip() or "50x50"
    duty=input("Enter Duty [M5]: ").strip() or "M5"
    r=get_wheel_full(swl,wt,n,rail,duty)
    print(f"\nPmax={r['pmax_kg']} Kg, Pmin={r['pmin_wheel_kg']} Kg, Pmean={r['pmean_kg']} Kg={r['pmean_n']} N")
    print(f"Rail {r['ct_rail']} top={r['rail_top']} a={r['a_mm']} mm, RPM {r['rpm']} C1={r['c1']} C2={r['c2']}")
    print(f"Dmin={r['dmin_mm']} mm -> Selected {r['d_sel_mm']} mm")
    print(f"Weight: {r['wt_per_set_kg']} Kg/set (4 Nos), Total for {r['n_ctw']} wheels = {r['total_wt_kg']} Kg")

if __name__=="__main__":
    main()