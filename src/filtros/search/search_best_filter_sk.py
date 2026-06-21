import math
from pprint import pprint

from filtros.data.inventario_yaml import cargar_inventario_desde_yaml
from filtros.core.design_mfb import cargar_tablas, obtener_etapas  # reutilizamos tablas TI
from filtros.core.design_sallen_key import disenar_etapa_sallen_key, DesignErrorSK
from filtros.search.search_best_stage import mas_cercano, error_rel2


def buscar_mejor_combinacion_para_etapa_sk(q, fsf, f0_hz, resistencias, capacitores):
    """
    Busca entre todas las combinaciones factibles de Csmall/Cbig (del inventario)
    y las Rmin/Rmax resultantes para Sallen-Key, la que minimiza un error simple
    vs los valores ideales de Rmin/Rmax que da disenar_etapa_sallen_key.
    """
    mejor = None
    mejor_error = math.inf

    for i, Csmall in enumerate(capacitores):
        for Cbig in capacitores[i:]:
            n = Cbig / Csmall  # Cbig >= Csmall

            # 1) Diseñar etapa ideal Sallen-Key con este par de capacitores
            etapa_ideal = disenar_etapa_sallen_key(
                c_small=Csmall,
                n_cap_ratio=n,
                fsf=fsf,
                q=q,
                f0_hz=f0_hz,
            )
            if etapa_ideal["status"] != "ok":
                continue

            Rmin_id = etapa_ideal["Rmin"]
            Rmax_id = etapa_ideal["Rmax"]

            # 2) Buscar resistencias reales más cercanas
            Rmin_real = mas_cercano(resistencias, Rmin_id)
            Rmax_real = mas_cercano(resistencias, Rmax_id)

            # 3) Error simple (suma de cuadrados relativos)
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
                    "m": etapa_ideal["m"],
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


def disenar_filtro_sallen_key_con_busqueda(
    fc_global_hz: float,
    orden: int,
    tipo_filtro: str,   # "Butterworth", "Bessel", "1-dB Chebyshev", "3-dB Chebyshev"
    path_yaml: str = "data/valores.yaml",
    path_csv_tablas: str = "data/filtros_pares.csv",
):
    """
    Para cada etapa Sallen-Key (según tablas TI) busca la mejor combinación
    de Csmall/Cbig y Rmin/Rmax en el inventario YAML.

    Devuelve lista de dicts por etapa (igual estilo que MFB).
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

        best = buscar_mejor_combinacion_para_etapa_sk(
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
                    "reason": "No se encontró combinación factible (Sallen-Key)",
                    "etapa": e.etapa,
                    "filtro": tipo_filtro,
                    "orden": orden,
                    "Q": q,
                    "fsf": fsf,
                    "f0_hz": f0_etapa,
                }
            )
        else:
            # añadir errores en porcentaje
            def rel_err_pct(real, ideal):
                if ideal == 0:
                    return math.nan
                return 100.0 * (real - ideal) / ideal

            best["status"] = "ok"
            best["etapa"] = e.etapa
            best["filtro"] = tipo_filtro
            best["orden"] = orden
            best["err_Rmin_pct"] = rel_err_pct(best["Rmin_real"], best["Rmin_ideal"])
            best["err_Rmax_pct"] = rel_err_pct(best["Rmax_real"], best["Rmax_ideal"])

            resultados.append(best)

    return resultados


if __name__ == "__main__":
    # Prueba rápida: Butterworth orden 4, 1 kHz
    fc = 1000.0
    orden = 4
    tipo = "Butterworth"

    res = disenar_filtro_sallen_key_con_busqueda(
        fc_global_hz=fc,
        orden=orden,
        tipo_filtro=tipo,
        path_yaml="data/valores.yaml",
        path_csv_tablas="data/filtros_pares.csv",
    )

    for r in res:
        print(f"\n=== Etapa {r['etapa']} ===")
        pprint(r)
