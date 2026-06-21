# archivo: run_design_with_inventory.py

from filtros.core.design_mfb import disenar_filtro_mfb
from filtros.data.inventario_yaml import cargar_inventario_desde_yaml
from filtros.data.inventory_match import aproximar_etapa_ideal_con_inventario

def disenar_filtro_con_inventario_yaml(
    fc_global_hz,
    orden,
    tipo_filtro,
    c_small,
    n_cap_ratio,
    path_yaml="data/valores.yaml",
    path_csv_tablas="data/filtros_pares.csv",
):
    etapas_ideales = disenar_filtro_mfb(
        fc_global_hz=fc_global_hz,
        orden=orden,
        tipo_filtro=tipo_filtro,
        c_small=c_small,
        n_cap_ratio=n_cap_ratio,
        path_csv=path_csv_tablas,
    )

    resistencias, capacitores = cargar_inventario_desde_yaml(path_yaml)

    resultados = []
    for etapa in etapas_ideales:
        aproximada = aproximar_etapa_ideal_con_inventario(
            etapa, resistencias, capacitores
        )
        aproximada["etapa"] = etapa["etapa"]
        aproximada["filtro"] = etapa["filtro"]
        aproximada["orden"] = etapa["orden"]
        resultados.append(aproximada)

    return resultados
