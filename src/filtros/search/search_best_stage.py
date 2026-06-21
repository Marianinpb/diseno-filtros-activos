import math
from filtros.data.inventario_yaml import cargar_inventario_desde_yaml
from filtros.core.design_mfb import calc_m, calc_r_min, DesignError


def mas_cercano(lista_vals, objetivo):
    return min(lista_vals, key=lambda v: abs(v - objetivo))


def error_rel2(real, ideal):
    if ideal == 0:
        return math.inf
    e = (real - ideal) / ideal
    return e * e


def buscar_mejor_combinacion_para_etapa(q, fsf, f0_hz, path_yaml="data/valores.yaml"):
    """
    Busca entre todas las combinaciones factibles de Csmall/Cbig (del inventario)
    y la Rmin/Rmax resultante, la que minimiza un error simple vs los valores
    "ideales" que salen de tus fórmulas.

    Nota: de momento definimos los ideales con el mismo Csmall/Cbig que estamos
    probando, así que el error se basa solo en qué tan bien pueden aproximar
    Rmin/Rmax tus resistencias reales.
    Más adelante podemos cambiar esto para comparar contra un diseño "ideal global".
    """
    resistencias, capacitores = cargar_inventario_desde_yaml(path_yaml)

    mejor = None
    mejor_error = math.inf

    for i, Csmall in enumerate(capacitores):
        for Cbig in capacitores[i:]:
            n = Cbig / Csmall  # n_cap_ratio

            # 1) Ver región de realizabilidad (discriminante)
            try:
                m_val = calc_m(n, q)
            except DesignError:
                continue  # este par (Csmall,Cbig) no sirve

            # 2) Calcular Rmin ideal para esta combinacion
            try:
                Rmin_id = calc_r_min(
                    c_small=Csmall,
                    fsf=fsf,
                    m=m_val,
                    n_cap_ratio=n,
                    f0_hz=f0_hz,
                )
            except DesignError:
                continue

            Rmax_id = m_val * Rmin_id

            # 3) Buscar resistencias reales más cercanas
            Rmin_real = mas_cercano(resistencias, Rmin_id)
            Rmax_real = mas_cercano(resistencias, Rmax_id)

            # 4) Error simple
            err = (
                error_rel2(Rmin_real, Rmin_id)
                + error_rel2(Rmax_real, Rmax_id)
            )

            if err < mejor_error:
                mejor_error = err
                mejor = {
                    "Csmall": Csmall,
                    "Cbig": Cbig,
                    "n_cap_ratio": n,
                    "m": m_val,
                    "Rmin_ideal": Rmin_id,
                    "Rmax_ideal": Rmax_id,
                    "Rmin_real": Rmin_real,
                    "Rmax_real": Rmax_real,
                    "fsf": fsf,
                    "Q": q,
                    "f0_hz": f0_hz,
                    "error_metric": err,
                }

    return mejor


if __name__ == "__main__":
    # Ejemplo: etapa 1 Butterworth orden 4 (según tu CSV)
    # Q = 0.5412, fsf = 1.0, f0 = 1 kHz
    q = 0.5412
    fsf = 1.0
    f0 = 1000.0

    best = buscar_mejor_combinacion_para_etapa(q, fsf, f0, path_yaml="data/valores.yaml")

    print("Mejor combinación encontrada para esta etapa:")
    from pprint import pprint
    pprint(best)
