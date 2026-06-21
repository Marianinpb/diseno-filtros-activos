import math
from pprint import pprint

from filtros.data.inventario_yaml import cargar_inventario_desde_yaml
from filtros.core.design_mfb import (
    cargar_tablas,
    obtener_etapas,
    calc_m,
    calc_r_min,
    DesignError,
)
from filtros.search.search_best_stage import mas_cercano, error_rel2  # o copia esas funciones aquí


def buscar_mejor_combinacion_para_etapa(q, fsf, f0_hz, resistencias, capacitores):
    mejor = None
    mejor_error = math.inf

    for i, Csmall in enumerate(capacitores):
        for Cbig in capacitores[i:]:
            n = Cbig / Csmall  # Cbig >= Csmall

            try:
                m_val = calc_m(n, q)
            except DesignError:
                continue

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

            Rmin_real = mas_cercano(resistencias, Rmin_id)
            Rmax_real = mas_cercano(resistencias, Rmax_id)

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


def disenar_filtro_mfb_con_busqueda(
    fc_global_hz: float,
    orden: int,
    tipo_filtro: str,
    path_yaml: str = "data/valores.yaml",
    path_csv_tablas: str = "data/filtros_pares.csv",
):
    """
    Para cada etapa (según tablas TI) busca la mejor combinación
    de Csmall/Cbig y Rmin/Rmax en el inventario.
    """
    if fc_global_hz <= 0:
        raise ValueError("fc_global_hz debe ser > 0")
    if orden % 2 != 0:
        raise ValueError("orden debe ser par")

    resistencias, capacitores = cargar_inventario_desde_yaml(path_yaml)
    cargar_tablas(path_csv_tablas)
    etapas_tabla = obtener_etapas(tipo_filtro, orden)

    resultados = []

    for e in etapas_tabla:
        fsf = e.fsf
        q = e.q
        f0_etapa = fc_global_hz * fsf

        best = buscar_mejor_combinacion_para_etapa(
            q=q,
            fsf=fsf,
            f0_hz=f0_etapa,
            resistencias=resistencias,
            capacitores=capacitores,
        )
        if best is None:
            resultados.append(
                {
                    "status": "invalid",
                    "reason": "No se encontró combinación factible",
                    "etapa": e.etapa,
                    "filtro": tipo_filtro,
                    "orden": orden,
                    "Q": q,
                    "fsf": fsf,
                    "f0_hz": f0_etapa,
                }
            )
        else:
            best["status"] = "ok"
            best["etapa"] = e.etapa
            best["filtro"] = tipo_filtro
            best["orden"] = orden
            best["err_Rmin_pct"] = 100.0 * (best["Rmin_real"] - best["Rmin_ideal"]) / best["Rmin_ideal"]
            best["err_Rmax_pct"] = 100.0 * (best["Rmax_real"] - best["Rmax_ideal"]) / best["Rmax_ideal"]
            resultados.append(best)

    return resultados


if __name__ == "__main__":
    fc = 1000.0
    orden = 4
    tipo = "Butterworth"

    res = disenar_filtro_mfb_con_busqueda(
        fc_global_hz=fc,
        orden=orden,
        tipo_filtro=tipo,
        path_yaml="data/valores.yaml",
        path_csv_tablas="data/filtros_pares.csv",
    )

    for r in res:
        print(f"\n=== Etapa {r['etapa']} ===")
        pprint(r)
