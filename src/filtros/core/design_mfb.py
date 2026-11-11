import math
import csv
from collections import defaultdict
from dataclasses import dataclass


# =========================
# Excepciones y dataclasses
# =========================

class DesignError(Exception):
    pass


@dataclass
class EtapaTabla:
    """
    Datos de una etapa tomados de filtros_pares.csv.
    """
    filtro: str       # "Butterworth", "Bessel", "1-dB Chebyshev", "3-dB Chebyshev"
    orden: int        # 2, 4, 6, 8, 10
    etapa: int        # 1..(orden/2)
    fsf: float        # factor de frecuencia efectiva
    q: float          # Q de la etapa


# Estructura en memoria:
# tablas[filtro][orden] -> [EtapaTabla(...), ...]
tablas = defaultdict(lambda: defaultdict(list))


# =========================
# Carga de tablas TI
# =========================

def cargar_tablas(path_csv: str = "data/filtros_pares.csv"):
    """
    Carga el CSV de tablas TI en la estructura 'tablas'.
    Se puede llamar varias veces; si ya hay datos, no hace nada.
    """
    if tablas:  # ya cargado
        return

    with open(path_csv, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filtro = row["Filtro"].strip()
            orden = int(row["Orden"])
            etapa = int(row["Etapa"])
            fsf = float(row["FSF"])
            q = float(row["Q"])
            et = EtapaTabla(filtro, orden, etapa, fsf, q)
            tablas[filtro][orden].append(et)

    # ordenar etapas por número
    for filtro in tablas:
        for orden in tablas[filtro]:
            tablas[filtro][orden].sort(key=lambda e: e.etapa)


def obtener_etapas(filtro: str, orden: int):
    """
    Devuelve lista de EtapaTabla para un tipo de filtro y orden dados.
    Lanza KeyError si no existe.
    """
    return tablas[filtro][orden]


# =========================
# Fórmulas MFB (tus ecuaciones)
# =========================

def calc_m(n_cap_ratio: float, q: float) -> float:
    """
    n_cap_ratio = C_grande / C_chico
    q = Q de la etapa

    Calcula m = R_grande / R_chica de forma robusta.
    """
    if q == 0:
        raise DesignError("Q = 0 no es válido")
    if n_cap_ratio <= 1.0:
        raise DesignError(f"n debe ser > 1 para estabilidad: n={n_cap_ratio}")

    n = n_cap_ratio
    disc = n**2 - 8 * n * q**2  # discriminante

    if disc < 0:
        raise DesignError(
            f"Discriminante negativo en m(n,q): n={n}, q={q}, disc={disc}"
        )

    denom = 8 * q**2
    if denom == 0:
        raise DesignError("Denominador cero en m(n,q)")

    m_val = (n - 4 * q**2 + math.sqrt(disc)) / denom

    if m_val <= 1.0:
        raise DesignError(f"m debe ser > 1 para estabilidad: m={m_val}")

    return m_val


def calc_m_hp(n_cap_ratio: float, q: float) -> float:
    """
    MFB High-Pass (ganancia unitaria -K = -1, C1 = C2 = C_chico, C3 = n * C_chico):
    Q = sqrt(m * n) / (n + 2)  =>  m = Q^2 * (n + 2)^2 / n
    """
    if q <= 0:
        raise DesignError("Q debe ser > 0")
    if n_cap_ratio <= 1.0:
        raise DesignError(f"n debe ser > 1 para estabilidad: n={n_cap_ratio}")

    n = n_cap_ratio
    m_val = (q**2 * (n + 2.0) ** 2) / n
    if m_val <= 1.0:
        raise DesignError(f"m_hp debe ser > 1 para estabilidad: m={m_val}")
    return m_val


def calc_m_bp(n_cap_ratio: float, q: float) -> float:
    """
    MFB Band-Pass (ganancia central unitaria, parametrización m y n de TI):
    Usa la misma relación cuadrática m(n, q) que MFB Low-Pass.
    """
    return calc_m(n_cap_ratio, q)



def calc_r_min(
    c_small: float,
    fsf: float,
    m: float,
    n_cap_ratio: float,
    f0_hz: float,
) -> float:
    """
    c_small     = C_chico
    fsf         = factor de frecuencia efectiva de la etapa
    m           = R_grande / R_chica
    n_cap_ratio = C_grande / C_chico
    f0_hz       = frecuencia de la etapa (en Hz)
    """
    if c_small <= 0:
        raise DesignError(f"C_chico no positivo: C={c_small}")
    if fsf <= 0:
        raise DesignError(f"fsf no positivo: fsf={fsf}")
    if m <= 1.0:
        raise DesignError(f"m debe ser > 1 para estabilidad: m={m}")
    if n_cap_ratio <= 1.0:
        raise DesignError(f"n_cap_ratio debe ser > 1 para estabilidad: n={n_cap_ratio}")
    if f0_hz <= 0:
        raise DesignError(f"f0 no positivo: f0={f0_hz}")

    n = n_cap_ratio

    # Tu fórmula original, usando f0 (Hz), no frecuencia angular
    denom = 2 * c_small * fsf * math.sqrt(m * n) * math.pi * f0_hz
    if denom == 0:
        raise DesignError("Denominador cero en calc_r_min")

    r_min = 1 / denom
    if r_min <= 0:
        raise DesignError(f"Rmin no positivo: Rmin={r_min}")

    return r_min


def disenar_etapa_mfb(
    c_small: float,
    n_cap_ratio: float,
    fsf: float,
    q: float,
    f0_hz: float,
    respuesta: str = "Low-Pass",
):
    """
    Diseña una etapa MFB usando tus fórmulas m() y r().

    Parámetros:
        c_small     : C_chico
        n_cap_ratio : C_grande / C_chico
        fsf         : factor de frecuencia efectiva (de la tabla TI)
        q           : Q de la etapa
        f0_hz       : frecuencia de la etapa (Hz) = fc_global * fsf
        respuesta   : "Low-Pass", "High-Pass", "Band-Pass"

    Devuelve:
        dict con:
            status: "ok" o "invalid"
            (si ok): m, Rmin, Rmax, Csmall, Cbig, Q, f0_hz, fsf, n_cap_ratio
            (si invalid): reason
    """
    try:
        if respuesta == "High-Pass":
            m_val = calc_m_hp(n_cap_ratio, q)
        elif respuesta == "Band-Pass":
            m_val = calc_m_bp(n_cap_ratio, q)
        else:
            m_val = calc_m(n_cap_ratio, q)

        r_min = calc_r_min(c_small, fsf, m_val, n_cap_ratio, f0_hz)
        r_max = m_val * r_min
        c_big = n_cap_ratio * c_small

        return {
            "status": "ok",
            "m": m_val,
            "Rmin": r_min,
            "Rmax": r_max,
            "Csmall": c_small,
            "Cbig": c_big,
            "Q": q,
            "f0_hz": f0_hz,
            "fsf": fsf,
            "n_cap_ratio": n_cap_ratio,
            "respuesta": respuesta,
        }
    except DesignError as e:
        return {
            "status": "invalid",
            "reason": str(e),
            "Q": q,
            "f0_hz": f0_hz,
            "fsf": fsf,
            "n_cap_ratio": n_cap_ratio,
            "respuesta": respuesta,
        }


# =========================
# Diseño de filtro completo MFB
# =========================

def disenar_filtro_mfb(
    fc_global_hz: float,
    orden: int,
    tipo_filtro: str,   # "Butterworth", "Bessel", "1-dB Chebyshev", "3-dB Chebyshev"
    c_small: float,
    n_cap_ratio: float,
    path_csv: str = "data/filtros_pares.csv",
    respuesta: str = "Low-Pass",
):
    """
    Diseña TODAS las etapas MFB de un filtro dado.

    Parámetros:
        fc_global_hz : frecuencia de corte global (Hz)
        orden        : orden total del filtro (par: 2,4,6,8,10)
        tipo_filtro  : nombre como aparece en el CSV
        c_small      : C_chico que quieres usar (F)
        n_cap_ratio  : C_grande / C_chico
        path_csv     : ruta al archivo filtros_pares.csv
        respuesta    : "Low-Pass", "High-Pass", "Band-Pass"

    Devuelve:
        lista de dicts, uno por etapa.
        Cada dict contiene lo que devuelve disenar_etapa_mfb(...) más:
            - "etapa": número de etapa
            - "filtro": tipo_filtro
            - "orden": orden
    """
    if fc_global_hz <= 0:
        raise ValueError("fc_global_hz debe ser > 0")
    if orden % 2 != 0:
        raise ValueError("orden debe ser par")
    if c_small <= 0:
        raise ValueError("c_small debe ser > 0")
    if n_cap_ratio <= 1.0:
        raise ValueError("n_cap_ratio debe ser > 1")

    cargar_tablas(path_csv)

    etapas_tabla = obtener_etapas(tipo_filtro, orden)
    etapas_resultado = []

    for e in etapas_tabla:
        fsf = 1.0 / e.fsf if respuesta == "High-Pass" else e.fsf
        q = e.q
        f0_etapa = fc_global_hz * fsf

        etapa = disenar_etapa_mfb(
            c_small=c_small,
            n_cap_ratio=n_cap_ratio,
            fsf=fsf,
            q=q,
            f0_hz=f0_etapa,
            respuesta=respuesta,
        )

        etapa["etapa"] = e.etapa
        etapa["filtro"] = tipo_filtro
        etapa["orden"] = orden

        etapas_resultado.append(etapa)

    return etapas_resultado


# =========================
# Prueba rápida en consola
# =========================

if __name__ == "__main__":
    # Ejemplo: Butterworth, orden 4, fc = 1 kHz, C_chico = 10 nF, C_grande = 2 * C_chico
    fc = 1000.0          # Hz
    orden = 4
    tipo = "Butterworth"  # debe coincidir con la columna "Filtro" del CSV
    Csmall = 10e-9        # 10 nF
    nC = 15.0              # Cbig = 15 * Csmall

    res = disenar_filtro_mfb(
        fc_global_hz=fc,
        orden=orden,
        tipo_filtro=tipo,
        c_small=Csmall,
        n_cap_ratio=nC,
        path_csv="data/filtros_pares.csv",
    )

    for etapa in res:
        print(f"Etapa {etapa['etapa']}: {etapa}")
