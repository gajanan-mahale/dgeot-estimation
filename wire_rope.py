# wire_rope.py 

# ====== YOUR TABLE for wire rope selection ======
FIBER_CORE = [
    {"dia":10, "constr":"6x36", "bs_ton":6.42, "bs_kn":63, "wt_kg_100m":40.8},
    {"dia":11, "constr":"6x36", "bs_ton":6.28, "bs_kn":76.2, "wt_kg_100m":49.4},
    {"dia":12, "constr":"6x36", "bs_ton":9.25, "bs_kn":90.7, "wt_kg_100m":58.8},
    {"dia":14, "constr":"6x36", "bs_ton":12.64, "bs_kn":124, "wt_kg_100m":80.2},
    {"dia":16, "constr":"6x36", "bs_ton":14.7, "bs_kn":161, "wt_kg_100m":104},
    {"dia":18, "constr":"6x36", "bs_ton":17.2, "bs_kn":168.67, "wt_kg_100m":132},
    {"dia":20, "constr":"6x36", "bs_ton":23.8, "bs_kn":233.4, "wt_kg_100m":163},
    {"dia":22, "constr":"6x36", "bs_ton":28.71, "bs_kn":281.5, "wt_kg_100m":197},
    {"dia":24, "constr":"6X36", "bs_ton":34.3, "bs_kn":336.4, "wt_kg_100m":235},
    {"dia":26, "constr":"6x36", "bs_ton":40.07, "bs_kn":393, "wt_kg_100m":276},
    {"dia":28, "constr":"6x36", "bs_ton":46.6, "bs_kn":457, "wt_kg_100m":320},
    {"dia":32, "constr":"6X36", "bs_ton":60.78, "bs_kn":596, "wt_kg_100m":418},
    {"dia":36, "constr":"6x36", "bs_ton":76.99, "bs_kn":755, "wt_kg_100m":531},
    {"dia":40, "constr":"6x36", "bs_ton":102.99, "bs_kn":1010, "wt_kg_100m":655},
    {"dia":44, "constr":"6x36", "bs_ton":124.41, "bs_kn":1220, "wt_kg_100m":793},
    {"dia":48, "constr":"6X36", "bs_ton":147.86, "bs_kn":1450, "wt_kg_100m":943},
    {"dia":52, "constr":"6X36", "bs_ton":173.35, "bs_kn":1700, "wt_kg_100m":1111},
]

STEEL_CORE = [
    {"dia":12, "constr":"6x36", "bs_ton":8.26, "bs_kn":81, "wt_kg_100m":90},
    {"dia":14, "constr":"6x36", "bs_ton":11.22, "bs_kn":110, "wt_kg_100m":122},
    {"dia":16, "constr":"6x36", "bs_ton":14.68, "bs_kn":144, "wt_kg_100m":160},
    {"dia":18, "constr":"6x36", "bs_ton":18.66, "bs_kn":183, "wt_kg_100m":202},
    {"dia":20, "constr":"6x36", "bs_ton":22.94, "bs_kn":225, "wt_kg_100m":250},
    {"dia":22, "constr":"6x36", "bs_ton":27.84, "bs_kn":273, "wt_kg_100m":302},
    {"dia":24, "constr":"6x36", "bs_ton":33.14, "bs_kn":325, "wt_kg_100m":359},
    {"dia":26, "constr":"6x36", "bs_ton":38.85, "bs_kn":381, "wt_kg_100m":422},
    {"dia":28, "constr":"6x36", "bs_ton":45.07, "bs_kn":442, "wt_kg_100m":489},
    {"dia":30, "constr":"6x36", "bs_ton":51.7, "bs_kn":507, "wt_kg_100m":562},
    {"dia":32, "constr":"6x36", "bs_ton":58.84, "bs_kn":577, "wt_kg_100m":639},
    {"dia":36, "constr":"6x36", "bs_ton":74.44, "bs_kn":730, "wt_kg_100m":809},
    {"dia":38, "constr":"6x36", "bs_ton":83.01, "bs_kn":814, "wt_kg_100m":901},
    {"dia":40, "constr":"6x36", "bs_ton":91.98, "bs_kn":902, "wt_kg_100m":999},
    {"dia":42, "constr":"6x36", "bs_ton":101.36, "bs_kn":994, "wt_kg_100m":1101},
]

# ====== YOUR FINAL Cdf & Zp LOGIC ======
Cdf = {"M1":1.8, "M2":1.25, "M3":1.32, "M4":1.4, "M5":1.5, "M6":1.6, "M7":1.6, "M8":1.7}
Zp = 4 #old design

def get_fos_wire(duty):
    duty = duty.upper()
    cdf_val = Cdf.get(duty, 1.5)
    fos = Zp * cdf_val
    # min 6
    if fos < 6:
        fos = 6
    return round(fos,2), cdf_val

def select_rope(swl_t, falls, duty, core_type="steel"):
    fos_wire, cdf_val = get_fos_wire(duty)

    S_ton = swl_t / falls
    S_kn = S_ton * 9.81

    required_bs_ton = S_ton * fos_wire
    required_bs_kn = S_kn * fos_wire

    table = STEEL_CORE if core_type.lower().startswith("steel") else FIBER_CORE

    selected = None
    for r in sorted(table, key=lambda x: x["dia"]):
        if r["bs_ton"] >= required_bs_ton:
            selected = r
            break
    if not selected:
        selected = table[-1]

    actual_fos = selected["bs_ton"] / S_ton if S_ton>0 else 0

    return {
        "S_ton": round(S_ton,3),
        "S_kn": round(S_kn,3),
        "Zp": Zp,
        "Cdf": cdf_val,
        "fos_required": fos_wire,
        "required_bs_ton": round(required_bs_ton,3),
        "required_bs_kn": round(required_bs_kn,3),
        "selected": selected,
        "actual_fos": round(actual_fos,2)
    }

def calc_rope_length_weight(lift_m, falls, wt_per_100m, extra_m=10):
    length = lift_m * falls + extra_m
    weight = (length / 100.0) * wt_per_100m
    return round(length,1), round(weight,1)

# def main():
#     print("==== WIRE ROPE SELECTION 6X36 construction ====")
#     # swl = float(input("Enter SWL (T) [10]: ") or 10)
#     # lift = float(input("Enter Lift (m) [10]: ") or 10)
#     falls = int(input("Enter No. of Falls [4]: ") or 4)
#     # duty = (input("Enter Duty M1-M8 [M5]: ") or "M5").strip()
#     core = (input("Core steel/fiber [steel]: ") or "steel").strip()

#     result = select_rope(swl, falls, duty, core)
#     sel = result["selected"]
#     length, wt = calc_rope_length_weight(lift, falls, sel["wt_kg_100m"])

    # print(f"\n--- FOS CALC ---")
    # print(f"Duty {duty.upper()} -> Cdf={result['Cdf']}, Zp={result['Zp']}")
    # print(f"fos_wire = Zp * Cdf = {result['Zp']} * {result['Cdf']} = {result['fos_required']}")
    # print(f"S = SWL/Falls = {swl}/{falls} = {result['S_ton']} Ton")

    # print(f"\n--- SELECTED ---")
    # print(f"Required BS = S * fos = {result['required_bs_ton']} Ton")
    # print(f"Selected: {sel['dia']} mm, BS={sel['bs_ton']} Ton / {sel['bs_kn']} kN")
    # print(f"Actual FOS = {sel['bs_ton']}/{result['S_ton']} = {result['actual_fos']}")

    print(f"\n--- OUTPUT ---")
    print(f"Wire Rope Dia: {sel['dia']} mm")
    print(f"Length: {length} mtr (Lift*Falls + 10m extra)")
    print(f"Weight: {wt} kg")
    print(f"Actual FOS: {result['actual_fos']}")

    return {
        "dia": sel["dia"],
        "length": length,
        "weight": wt,
        "fos_actual": result["actual_fos"],
        "fos_required": result["fos_required"],
        "bs_ton": sel["bs_ton"]
    }

# if __name__ == "__main__":
#     main()
