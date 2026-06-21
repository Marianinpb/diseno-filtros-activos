# archivo: inventory_match.py

import csv
import math

def cargar_resistencias(path: str):
    rs = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rs.append(float(row["R_ohm"]))
    return sorted(rs)

def cargar_capacitores(path: str):
    cs = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cs.append(float(row["C_f"]))
    return sorted(cs)

def mas_cercano(lista_vals, objetivo):
    """
    Devuelve el valor de lista_vals más cercano a 'objetivo'.
    """
    return min(lista_vals, key=lambda v: abs(v - objetivo))

def aproximar_etapa_ideal_con_inventario(etapa_ideal, resistencias, capacitores):
    """
    etapa_ideal: dict devuelto por disenar_etapa_mfb (status='ok')
    resistencias: lista de R disponibles (ohms)
    capacitores: lista de C disponibles (farads)

    Devuelve dict con los valores reales y el error relativo en R y C.
    """
    if etapa_ideal["status"] != "ok":
        return {
            "status": "invalid",
            "reason": etapa_ideal.get("reason", "Etapa no realizable"),
        }

    Rmin_id = etapa_ideal["Rmin"]
    Rmax_id = etapa_ideal["Rmax"]
    Csmall_id = etapa_ideal["Csmall"]
    Cbig_id = etapa_ideal["Cbig"]

    Rmin_real = mas_cercano(resistencias, Rmin_id)
    Rmax_real = mas_cercano(resistencias, Rmax_id)
    Csmall_real = mas_cercano(capacitores, Csmall_id)
    Cbig_real = mas_cercano(capacitores, Cbig_id)

    # errores relativos simples
    def rel_err(real, ideal):
        return (real - ideal) / ideal if ideal != 0 else math.nan
    def rel_err_pct(real, ideal):
        if ideal == 0:
            return math.nan
        return 100.0 * (real - ideal) / ideal

    return {
        "status": "ok",
        "Rmin_ideal": Rmin_id,
        "Rmax_ideal": Rmax_id,
        "Csmall_ideal": Csmall_id,
        "Cbig_ideal": Cbig_id,
        "Rmin_real": Rmin_real,
        "Rmax_real": Rmax_real,
        "Csmall_real": Csmall_real,
        "Cbig_real": Cbig_real,
        "err_Rmin": rel_err(Rmin_real, Rmin_id),
        "err_Rmax": rel_err(Rmax_real, Rmax_id),
        "err_Csmall": rel_err(Csmall_real, Csmall_id),
        "err_Cbig": rel_err(Cbig_real, Cbig_id),
        "Q": etapa_ideal["Q"],
        "f0_hz": etapa_ideal["f0_hz"],
        "fsf": etapa_ideal["fsf"],
        "n_cap_ratio": etapa_ideal["n_cap_ratio"],
        "err_Rmin_pct": rel_err_pct(Rmin_real, Rmin_id),
        "err_Rmax_pct": rel_err_pct(Rmax_real, Rmax_id),
        "err_Csmall_pct": rel_err_pct(Csmall_real, Csmall_id),
        "err_Cbig_pct": rel_err_pct(Cbig_real, Cbig_id),
    }
