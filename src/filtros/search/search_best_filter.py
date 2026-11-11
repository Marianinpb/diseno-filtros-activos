import math
import sys
from pathlib import Path
from pprint import pprint

_SRC_DIR = str(Path(__file__).resolve().parents[2])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from filtros.data.inventario_yaml import cargar_inventario_desde_yaml
from filtros.core.design_mfb import (
    cargar_tablas,
    obtener_etapas,
    calc_m,
    calc_m_hp,
    calc_m_bp,
    calc_r_min,
    DesignError,
)
from filtros.search.search_best_stage import mas_cercano, error_rel2  # o copia esas funciones aquí


def buscar_mejor_combinacion_para_etapa(
    q, fsf, f0_hz, resistencias, capacitores, respuesta: str = "Low-Pass"
):
    mejor = None
    mejor_error = math.inf

    for i, Csmall in enumerate(capacitores):
        for Cbig in capacitores[i + 1 :]:
            n = Cbig / Csmall  # Cbig > Csmall => n > 1
            if n <= 1.0:
                continue

            try:
                if respuesta == "High-Pass":
                    m_val = calc_m_hp(n, q)
                elif respuesta == "Band-Pass":
                    m_val = calc_m_bp(n, q)
                else:
                    m_val = calc_m(n, q)
            except DesignError:
                continue

            if m_val <= 1.0:
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
                    "respuesta": respuesta,
                }

    return mejor


def disenar_filtro_mfb_con_busqueda(
    fc_global_hz: float,
    orden: int,
    tipo_filtro: str,
    path_yaml: str = "data/valores.yaml",
    path_csv_tablas: str = "data/filtros_pares.csv",
    respuesta: str = "Low-Pass",
    fc2_hz: float | None = None,
):
    """
    Para cada etapa (según tablas TI) busca la mejor combinación
    de Csmall/Cbig y Rmin/Rmax en el inventario.
    Soporta:
      - "Low-Pass"
      - "High-Pass"
      - "Band-Pass" (etapas pasabanda centradas en fc_global_hz)
      - "Band-Pass (Cascada HP+LP)" (etapas HP en fc_global_hz + etapas LP en fc2_hz)
    """
    if fc_global_hz <= 0:
        raise ValueError("fc_global_hz debe ser > 0")
    if orden % 2 != 0:
        raise ValueError("orden debe ser par")

    if respuesta == "Band-Pass (Cascada HP+LP)":
        if fc2_hz is None or fc2_hz <= 0:
            raise ValueError("Para Band-Pass en cascada se requiere fc2_hz > 0")
        etapas_hp = disenar_filtro_mfb_con_busqueda(
            fc_global_hz=fc_global_hz,
            orden=orden,
            tipo_filtro=tipo_filtro,
            path_yaml=path_yaml,
            path_csv_tablas=path_csv_tablas,
            respuesta="High-Pass",
        )
        etapas_lp = disenar_filtro_mfb_con_busqueda(
            fc_global_hz=fc2_hz,
            orden=orden,
            tipo_filtro=tipo_filtro,
            path_yaml=path_yaml,
            path_csv_tablas=path_csv_tablas,
            respuesta="Low-Pass",
        )
        for e in etapas_hp:
            e["etapa"] = f"HP-{e['etapa']}"
        for e in etapas_lp:
            e["etapa"] = f"LP-{e['etapa']}"
        return etapas_hp + etapas_lp

    resistencias, capacitores = cargar_inventario_desde_yaml(path_yaml)
    cargar_tablas(path_csv_tablas)
    etapas_tabla = obtener_etapas(tipo_filtro, orden)

    resultados = []

    for e in etapas_tabla:
        fsf = 1.0 / e.fsf if respuesta == "High-Pass" else e.fsf
        q = e.q
        f0_etapa = fc_global_hz * fsf

        best = buscar_mejor_combinacion_para_etapa(
            q=q,
            fsf=fsf,
            f0_hz=f0_etapa,
            resistencias=resistencias,
            capacitores=capacitores,
            respuesta=respuesta,
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
                    "respuesta": respuesta,
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
