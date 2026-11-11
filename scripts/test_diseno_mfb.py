import sys
from pathlib import Path
from pprint import pprint

_SRC_DIR = str(Path(__file__).resolve().parents[1] / "src")
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from filtros.core.design_mfb import disenar_filtro_mfb
from filtros.data.inventario_yaml import cargar_inventario_desde_yaml
from filtros.data.inventory_match import aproximar_etapa_ideal_con_inventario


def test_etapas_ideales():
    print("=== Test 1: etapas ideales MFB (sin inventario) ===")
    fc = 1000.0          # Hz
    orden = 4
    tipo = "Butterworth"  # exactamente como en filtros_pares.csv
    Csmall = 10e-9        # 10 nF
    nC = 15.0             # Cbig = 15 * Csmall

    etapas = disenar_filtro_mfb(
        fc_global_hz=fc,
        orden=orden,
        tipo_filtro=tipo,
        c_small=Csmall,
        n_cap_ratio=nC,
        path_csv="data/filtros_pares.csv",
    )

    for e in etapas:
        print(f"\nEtapa {e['etapa']} (ideal):")
        pprint(e)


def test_inventario_yaml():
    print("\n=== Test 2: cargar inventario desde valores.yaml ===")
    rs, cs = cargar_inventario_desde_yaml("data/valores.yaml")
    print(f"Total resistencias: {len(rs)}")
    print("Primeras 15 resistencias (ohm):", rs[:15])
    print(f"Total capacitores: {len(cs)}")
    print("Todos los capacitores (F):", cs)


def test_match_con_inventario():
    print("\n=== Test 3: diseño + aproximación con inventario ===")
    fc = 1000.0          # Hz
    orden = 4
    tipo = "Butterworth"
    Csmall = 10e-9       # 10 nF
    nC = 15.0

    etapas_ideales = disenar_filtro_mfb(
        fc_global_hz=fc,
        orden=orden,
        tipo_filtro=tipo,
        c_small=Csmall,
        n_cap_ratio=nC,
        path_csv="data/filtros_pares.csv",
    )

    rs, cs = cargar_inventario_desde_yaml("data/valores.yaml")

    for etapa in etapas_ideales:
        print(f"\n--- Etapa {etapa['etapa']} ---")
        print("Ideal:")
        pprint(etapa)

        aprox = aproximar_etapa_ideal_con_inventario(etapa, rs, cs)
        print("Aproximada con inventario:")
        pprint(aprox)


if __name__ == "__main__":
    test_etapas_ideales()
    test_inventario_yaml()
    test_match_con_inventario()
