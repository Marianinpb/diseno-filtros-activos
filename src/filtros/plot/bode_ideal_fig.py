import io
import base64

import numpy as np
import matplotlib.pyplot as plt
from scipy import signal

from filtros.core.design_mfb import cargar_tablas, obtener_etapas


def generar_bode_ideal_bytes(
    fc_global_hz,
    tipo_filtro,
    orden,
    path_csv="data/filtros_pares.csv",
):
    """Returns base64-encoded PNG of the ideal Bode magnitude plot."""
    cargar_tablas(path_csv)
    etapas = obtener_etapas(tipo_filtro, orden)
    if not etapas:
        raise ValueError("No hay etapas para ese filtro/orden")

    num_total = np.array([1.0])
    den_total = np.array([1.0])

    for e in etapas:
        fsf = e.fsf
        Q = e.q
        f0_hz = fc_global_hz * fsf
        w0 = 2 * np.pi * f0_hz

        num_i = np.array([0.0, 0.0, w0**2])
        den_i = np.array([1.0, w0 / Q, w0**2])

        num_total = np.polymul(num_total, num_i)
        den_total = np.polymul(den_total, den_i)

    system = signal.TransferFunction(num_total, den_total)

    w0_c = 2 * np.pi * fc_global_hz
    w = np.logspace(np.log10(w0_c * 0.1), np.log10(w0_c * 10), 2000)
    w, mag, phase = signal.bode(system, w=w)
    f = w / (2 * np.pi)

    fig, ax = plt.subplots(facecolor="#0d1117")
    ax.set_facecolor("#0d1117")

    ax.semilogx(f, mag, color="#58a6ff", linewidth=1.5)
    ax.set_title(
        f"{tipo_filtro}, orden {orden}, fc={fc_global_hz} Hz (ideal)",
        color="#e6edf3",
    )
    ax.set_xlabel("Frecuencia (Hz)", color="#e6edf3")
    ax.set_ylabel("Magnitud (dB)", color="#e6edf3")
    ax.tick_params(colors="#8b949e")
    ax.grid(True, which="both", ls="--", alpha=0.3, color="#30363d")
    ax.axvline(fc_global_hz, color="#f85149", linestyle=":", linewidth=1.2, label="fc")
    ax.legend(facecolor="#161b22", edgecolor="#30363d", labelcolor="#e6edf3")
    fig.tight_layout()

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode()


def guardar_bode_filtro_ideal_png(
    fc_global_hz,
    tipo_filtro,
    orden,
    path_csv="data/filtros_pares.csv",
    filename="output/bode_ideal.png",
):
    cargar_tablas(path_csv)
    etapas = obtener_etapas(tipo_filtro, orden)
    if not etapas:
        raise ValueError("No hay etapas para ese filtro/orden")

    num_total = np.array([1.0])
    den_total = np.array([1.0])

    for e in etapas:
        fsf = e.fsf
        Q = e.q
        f0_hz = fc_global_hz * fsf
        w0 = 2 * np.pi * f0_hz

        num_i = np.array([0.0, 0.0, w0**2])
        den_i = np.array([1.0, w0 / Q, w0**2])

        num_total = np.polymul(num_total, num_i)
        den_total = np.polymul(den_total, den_i)

    system = signal.TransferFunction(num_total, den_total)

    w0_c = 2 * np.pi * fc_global_hz
    w = np.logspace(np.log10(w0_c * 0.1), np.log10(w0_c * 10), 2000)
    w, mag, phase = signal.bode(system, w=w)
    f = w / (2 * np.pi)

    fig, ax = plt.subplots()
    ax.semilogx(f, mag)
    ax.set_title(f"{tipo_filtro}, orden {orden}, fc={fc_global_hz} Hz (ideal)")
    ax.set_xlabel("Frecuencia (Hz)")
    ax.set_ylabel("Magnitud (dB)")
    ax.grid(True, which="both", ls="--", alpha=0.5)
    ax.axvline(fc_global_hz, color="red", linestyle=":", label="fc")
    ax.legend()
    fig.tight_layout()

    fig.savefig(filename, dpi=120)
    plt.close(fig)

    return filename
