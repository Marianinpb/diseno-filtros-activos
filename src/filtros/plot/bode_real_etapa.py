import numpy as np
import matplotlib.pyplot as plt
from scipy import signal


def bode_etapa_real(Rmax, Rmin, Csmall, Cbig, label="Etapa real"):
    """
    Usa tu H(s) real:
    H(s) = (-R2/R1) / (s^2 R2 R3 C1 C2 + s(R3 C1 + R2 C1 + R2 R3 C1 / R1) + 1)
    con R1=R2=Rmax, R3=Rmin, C1=Csmall, C2=Cbig.
    """
    R1 = Rmax
    R2 = Rmax
    R3 = Rmin
    C1 = Csmall
    C2 = Cbig

    # Numerador y denominador en s
    num = [-R2 / R1]  # [-1]
    a2 = R2 * R3 * C1 * C2
    a1 = R3 * C1 + R2 * C1 + (R2 * R3 * C1 / R1)
    a0 = 1.0
    den = [a2, a1, a0]

    system = signal.TransferFunction(num, den)

    # Barrido de frecuencia amplio (decidimos banda)
    fmin = 1.0
    fmax = 1e6
    w = np.logspace(np.log10(2*np.pi*fmin), np.log10(2*np.pi*fmax), 2000)
    w, mag, phase = signal.bode(system, w=w)
    f = w / (2*np.pi)

    plt.figure()
    plt.semilogx(f, mag)
    plt.title(f"Magnitud Bode real - {label}")
    plt.xlabel("Frecuencia (Hz)")
    plt.ylabel("Magnitud (dB)")
    plt.grid(True, which="both", ls="--", alpha=0.5)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    # Ejemplo: usa una etapa calculada por tu app (pon aquí números reales)
    Rmax = 1.5e+5
    Rmin = 6.2e+4
    Csmall = 4.7e-10
    Cbig = 2.2e-9

    bode_etapa_real(Rmax, Rmin, Csmall, Cbig, label="Ejemplo etapa MFB")
