import math
from dataclasses import dataclass
from typing import Dict, Any


class DesignErrorSK(Exception):
    pass


def calc_m_sk(n_cap_ratio: float, q: float) -> float:
    """
    Sallen-Key:
    m = (n - 2*q^2 + sqrt(n^2 - 4*n*q^2)) / (2*q^2)
    con n = C_grande / C_chico.
    """
    if q == 0:
        raise DesignErrorSK("Q = 0 no es válido")
    if n_cap_ratio <= 1.0:
        raise DesignErrorSK(f"n debe ser > 1 para estabilidad: n={n_cap_ratio}")

    n = n_cap_ratio
    disc = n**2 - 4 * n * q**2
    if disc < 0:
        raise DesignErrorSK(
            f"Discriminante negativo en m_sk(n,q): n={n}, q={q}, disc={disc}"
        )

    denom = 2 * q**2
    if denom == 0:
        raise DesignErrorSK("Denominador cero en m_sk(n,q)")

    m_val = (n - 2 * q**2 + math.sqrt(disc)) / denom

    if m_val <= 1.0:
        raise DesignErrorSK(f"m (Sallen-Key) debe ser > 1 para estabilidad: m={m_val}")

    return m_val


def calc_m_sk_hp(n_cap_ratio: float, q: float) -> float:
    """
    Sallen-Key High-Pass (ganancia unitaria K = 1, C1 = C_chico, C2 = n * C_chico):
    Q = sqrt(m * n) / (n + 1)  =>  m = Q^2 * (n + 1)^2 / n
    """
    if q <= 0:
        raise DesignErrorSK("Q debe ser > 0")
    if n_cap_ratio <= 1.0:
        raise DesignErrorSK(f"n debe ser > 1 para estabilidad: n={n_cap_ratio}")

    n = n_cap_ratio
    m_val = (q**2 * (n + 1.0) ** 2) / n
    if m_val <= 1.0:
        raise DesignErrorSK(f"m_sk_hp debe ser > 1 para estabilidad: m={m_val}")
    return m_val


def calc_m_sk_bp(n_cap_ratio: float, q: float) -> float:
    """
    Sallen-Key Band-Pass (ganancia unitaria K = 1):
    Q = sqrt(m * n) / (m + n + 1)
    => m = (n - 2 * Q^2 * (n + 1) + sqrt(n^2 - 4 * n * Q^2 * (n + 1))) / (2 * Q^2)
    Si el discriminante con K=1 no alcanza para Q alto, usa la forma cuadrática estándar calc_m_sk(n, q).
    """
    if q <= 0:
        raise DesignErrorSK("Q debe ser > 0")
    if n_cap_ratio <= 1.0:
        raise DesignErrorSK(f"n debe ser > 1 para estabilidad: n={n_cap_ratio}")

    n = n_cap_ratio
    disc = n**2 - 4 * n * (q**2) * (n + 1.0)
    if disc >= 0:
        m_val = (n - 2 * (q**2) * (n + 1.0) + math.sqrt(disc)) / (2 * q**2)
        if m_val > 1.0:
            return m_val
    return calc_m_sk(n_cap_ratio, q)



def calc_rmin_sk(
    m: float,
    n_cap_ratio: float,
    c_small: float,
    fsf: float,
    f0_hz: float,
) -> float:
    """
    r_func_num(m, n, c, fsf, w0) pero:
    - n_cap_ratio = C_grande / C_chico
    - c_small = C_chico
    - fsf = factor de frecuencia efectiva (tabla TI)
    - f0_hz = frecuencia de etapa (Hz)
    """
    if m <= 1.0:
        raise DesignErrorSK(f"m debe ser > 1 para estabilidad: m={m}")
    if n_cap_ratio <= 1.0:
        raise DesignErrorSK(f"n_cap_ratio debe ser > 1 para estabilidad: n={n_cap_ratio}")
    if c_small <= 0:
        raise DesignErrorSK(f"C_chico no positivo: C={c_small}")
    if fsf <= 0:
        raise DesignErrorSK(f"fsf no positivo: fsf={fsf}")
    if f0_hz <= 0:
        raise DesignErrorSK(f"f0 no positivo: f0={f0_hz}")

    n = n_cap_ratio
    denom = 2 * c_small * fsf * math.sqrt(m * n) * math.pi * f0_hz
    if denom == 0:
        raise DesignErrorSK("Denominador cero en calc_rmin_sk")

    r_min = 1 / denom
    if r_min <= 0:
        raise DesignErrorSK(f"Rmin no positivo: Rmin={r_min}")

    return r_min


def disenar_etapa_sallen_key(
    c_small: float,
    n_cap_ratio: float,
    fsf: float,
    q: float,
    f0_hz: float,
    respuesta: str = "Low-Pass",
) -> Dict[str, Any]:
    """
    Diseña una etapa Sallen-Key usando tus fórmulas m_func_num y r_func_num.

    Parámetros:
        c_small     : C_chico
        n_cap_ratio : C_grande / C_chico
        fsf         : factor de frecuencia efectiva (tabla TI)
        q           : Q de la etapa
        f0_hz       : frecuencia de la etapa (Hz) = fc_global * fsf
        respuesta   : "Low-Pass", "High-Pass", "Band-Pass"

    Devuelve:
        dict con status, m, Rmin, Rmax, Csmall, Cbig, etc.
    """
    try:
        if respuesta == "High-Pass":
            m_val = calc_m_sk_hp(n_cap_ratio, q)
        elif respuesta == "Band-Pass":
            m_val = calc_m_sk_bp(n_cap_ratio, q)
        else:
            m_val = calc_m_sk(n_cap_ratio, q)

        r_min = calc_rmin_sk(
            m=m_val,
            n_cap_ratio=n_cap_ratio,
            c_small=c_small,
            fsf=fsf,
            f0_hz=f0_hz,
        )
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
    except DesignErrorSK as e:
        return {
            "status": "invalid",
            "reason": str(e),
            "Q": q,
            "f0_hz": f0_hz,
            "fsf": fsf,
            "n_cap_ratio": n_cap_ratio,
            "respuesta": respuesta,
        }
