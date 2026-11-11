import io
import base64

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


def transfer_func_etapa_sk(Rmax, Rmin, Csmall, Cbig, respuesta="Low-Pass", m=None):
    """Sallen-Key unity-gain transfer function."""
    if respuesta == "High-Pass":
        C1 = Csmall
        C2 = Cbig
        if m is not None and m < 1.0:
            R1, R2 = Rmax, Rmin
        else:
            R1, R2 = Rmin, Rmax
        a2 = R1 * R2 * C1 * C2
        a1 = R1 * (C1 + C2)
        a0 = 1.0
        num = [a2, 0.0, 0.0]
        den = [a2, a1, a0]
        return signal.TransferFunction(num, den)
    elif respuesta == "Band-Pass":
        R1 = Rmax
        R2 = Rmin
        C1 = Csmall
        C2 = Cbig
        a2 = R1 * R2 * C1 * C2
        a1 = C1 * (R1 + R2)
        a0 = 1.0
        num = [0.0, a1, 0.0]
        den = [a2, a1, a0]
        return signal.TransferFunction(num, den)

    R1 = Rmax
    R2 = Rmin
    C1 = Csmall
    C2 = Cbig

    num = [1.0]
    a2 = R1 * R2 * C1 * C2
    a1 = C1 * (R1 + R2)
    a0 = 1.0
    den = [a2, a1, a0]

    return signal.TransferFunction(num, den)


def generar_bode_sk_real_bytes(etapas, fc_global_hz, tipo_filtro, orden):
    """Returns base64-encoded PNG of the real Sallen-Key Bode magnitude plot.

    Args:
        etapas: list of result dicts from disenar_filtro_sallen_key_con_busqueda
                (keys: Rmin_real, Rmax_real, Csmall, Cbig, status)
        fc_global_hz: global cutoff frequency in Hz
        tipo_filtro: filter type string (e.g. "Butterworth")
        orden: filter order
    """
    num_total = np.array([1.0])
    den_total = np.array([1.0])

    for e in etapas:
        if e["status"] != "ok":
            continue

        Rmin = e["Rmin_real"]
        Rmax = e["Rmax_real"]
        Csmall = e["Csmall"]
        Cbig = e["Cbig"]
        resp_e = e.get("respuesta", "Low-Pass")

        sys_i = transfer_func_etapa_sk(Rmax, Rmin, Csmall, Cbig, respuesta=resp_e, m=e.get("m"))
        num_total = np.polymul(num_total, np.array(sys_i.num))
        den_total = np.polymul(den_total, np.array(sys_i.den))

    system = signal.TransferFunction(num_total, den_total)

    w0_c = 2 * np.pi * fc_global_hz
    w = np.logspace(np.log10(w0_c * 0.1), np.log10(w0_c * 10), 2000)
    w, mag, phase = signal.bode(system, w=w)
    f = w / (2 * np.pi)

    fig, ax = plt.subplots()
    ax.semilogx(f, mag)
    ax.set_title(
        f"Filtro Sallen-Key REAL - {tipo_filtro}, orden {orden}, fc={fc_global_hz} Hz"
    )
    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_ylabel("Magnitud (dB)")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.axvline(fc_global_hz, color="red", linestyle=":", label="fc")
    ax.legend()
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()
