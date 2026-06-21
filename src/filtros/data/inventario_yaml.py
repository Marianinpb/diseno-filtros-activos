import yaml
import re

UNITS_R = {
    "": 1.0,
    "K": 1e3,
    "MEG": 1e6,
}

UNITS_C = {
    "p": 1e-12,
    "n": 1e-9,
    "u": 1e-6,
}

def parse_resistor(value_str: str) -> float:
    """
    Convierte strings como '1', '1.1', '1K', '4.7MEG' a ohms (float).
    """
    s = str(value_str).strip().upper()

    # MEG primero (porque contiene 'M' y 'EG')
    if s.endswith("MEG"):
        number = s[:-3]
        unit = "MEG"
    elif s.endswith("K"):
        number = s[:-1]
        unit = "K"
    else:
        number = s
        unit = ""

    number = number.replace(",", ".")  # por si acaso
    val = float(number)
    return val * UNITS_R[unit]


def parse_capacitor(value_str: str) -> float:
    """
    Convierte strings como '1p', '4.7n', '10u' a farads (float).
    """
    s = str(value_str).strip()

    match = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)\s*([pnuPNU])", s)
    if not match:
        raise ValueError(f"Formato de capacitor no reconocido: {value_str}")

    number_str, unit_char = match.groups()
    val = float(number_str.replace(",", "."))
    unit_char = unit_char.lower()

    factor = UNITS_C[unit_char]
    return val * factor


def cargar_inventario_desde_yaml(path_yaml: str = "data/valores.yaml"):
    """
    Lee valores.yaml y devuelve:
        resistencias_ohm: lista de floats en ohms
        capacitores_f:    lista de floats en farads
    """
    with open(path_yaml, "r") as f:
        data = yaml.safe_load(f)

    res_raw = data.get("resistencias", [])
    cap_raw = data.get("capacitores", [])

    resistencias_ohm = [parse_resistor(x) for x in res_raw]
    capacitores_f = [parse_capacitor(x) for x in cap_raw]

    resistencias_ohm = sorted(set(resistencias_ohm))
    capacitores_f = sorted(set(capacitores_f))

    return resistencias_ohm, capacitores_f


if __name__ == "__main__":
    rs, cs = cargar_inventario_desde_yaml("data/valores.yaml")
    print("Resistencias (ohm):", rs[:20], "...")
    print("Capacitores (F):", cs)
