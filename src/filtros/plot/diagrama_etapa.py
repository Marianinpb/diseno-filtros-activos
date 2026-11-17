import base64
from pathlib import Path

import matplotlib.pyplot as plt
import schemdraw
import schemdraw.elements as elm


def formatear_resistencia_latex(ohms: float) -> str:
    """Formatea un valor de resistencia en ohms usando mathtext compatible con Matplotlib."""
    if ohms >= 1e6:
        return f"${ohms / 1e6:.4g}\\,\\mathrm{{M}}\\Omega$"
    if ohms >= 1e3:
        return f"${ohms / 1e3:.4g}\\,\\mathrm{{k}}\\Omega$"
    return f"${ohms:.4g}\\,\\Omega$"


def formatear_capacitor_latex(farads: float) -> str:
    """Formatea un valor de capacitancia en farads usando mathtext compatible con Matplotlib."""
    if farads >= 1e-6:
        return f"${farads * 1e6:.4g}\\,\\mu\\mathrm{{F}}$"
    if farads >= 1e-9:
        return f"${farads * 1e9:.4g}\\,\\mathrm{{nF}}$"
    if farads >= 1e-12:
        return f"${farads * 1e12:.4g}\\,\\mathrm{{pF}}$"
    return f"${farads:.3e}\\,\\mathrm{{F}}$"


def _dibujar_base_sallen_key(d: schemdraw.Drawing) -> None:
    """Conexiones, op-amp, tierra y nodos compartidos para etapas Sallen-Key."""
    conexiones = [
        ((15, 7.5), (18, 7.5)),
        ((4.5, 9), (3, 9)),
        ((9, 9), (7.5, 9)),
        ((15, 7.5), (15, 4.5)),
        ((15, 4.5), (9, 4.5)),
        ((9, 4.5), (9, 6)),
        ((7.5, 0), (7.5, 1.5)),
        ((7.5, 4.5), (7.5, 9)),
        ((10.5, 13.5), (4.5, 13.5)),
        ((4.5, 13.5), (4.5, 9)),
        ((13.5, 13.5), (15, 13.5)),
        ((15, 13.5), (15, 7.5)),
    ]
    for p1, p2 in conexiones:
        d += elm.Line().at(p1).to(p2)

    d += elm.Dot(open=True).at((0, 9)).label(r"$V_{\mathrm{in}}$", loc="left")
    oa1 = d.add(elm.Opamp(leads=True).at((12, 7.5)).theta(0))
    oa1.label("$U_1$", loc="center")
    d += elm.Line().at(oa1.in1).to((9, 9))
    d += elm.Line().at(oa1.in2).to((9, 6))
    d += elm.Line().at(oa1.out).to((15, 7.5))
    d += elm.Ground().at((7.5, 0))
    d += elm.Dot(open=True).at((18, 7.5)).label(r"$V_{\mathrm{out}}$", loc="right")

    for nodo in ((4.5, 9), (7.5, 9), (15, 7.5)):
        d += elm.Dot().at(nodo)


def _dibujar_base_mfb(d: schemdraw.Drawing) -> None:
    """Conexiones, op-amp, tierras y nodos compartidos para etapas MFB."""
    conexiones = [
        ((15, 7.5), (18, 7.5)),
        ((4.5, 9), (3, 9)),
        ((9, 9), (7.5, 9)),
        ((9, 4.5), (9, 6)),
        ((4.5, 13.5), (4.5, 9)),
        ((13.5, 13.5), (15, 13.5)),
        ((15, 13.5), (15, 7.5)),
        ((12, 13.5), (13.5, 13.5)),
        ((12, 13.5), (9, 13.5)),
        ((6, 13.5), (4.5, 13.5)),
        ((9, 12), (9, 13.5)),
        ((4.5, 9), (4.5, 7.5)),
        ((4.5, 4.5), (4.5, 0)),
    ]
    for p1, p2 in conexiones:
        d += elm.Line().at(p1).to(p2)

    d += elm.Dot(open=True).at((0, 9)).label(r"$V_{\mathrm{in}}$", loc="left")
    oa1 = d.add(elm.Opamp(leads=True).at((12, 7.5)).theta(0))
    oa1.label("$U_1$", loc="center")
    d += elm.Line().at(oa1.in1).to((9, 9))
    d += elm.Line().at(oa1.in2).to((9, 6))
    d += elm.Line().at(oa1.out).to((15, 7.5))
    d += elm.Ground().at((4.5, 0))
    d += elm.Ground().at((9, 4.5))
    d += elm.Dot(open=True).at((18, 7.5)).label(r"$V_{\mathrm{out}}$", loc="right")

    for nodo in ((4.5, 9), (9, 9), (15, 7.5), (9, 13.5)):
        d += elm.Dot().at(nodo)


def construir_drawing_etapa(
    etapa_dict: dict,
    topologia: str,
    dark: bool = False,
) -> schemdraw.Drawing:
    """Construye el diagrama schemdraw de una etapa con los valores reales calculados."""
    resp = etapa_dict.get("respuesta", "Low-Pass")
    if topologia not in ("Sallen-Key", "MFB"):
        raise ValueError(f"Topología no soportada para diagrama: {topologia}")
    if resp not in ("Low-Pass", "High-Pass"):
        raise ValueError(f"Respuesta no soportada para diagrama: {resp}")

    r_min = formatear_resistencia_latex(etapa_dict["Rmin_real"])
    r_max = formatear_resistencia_latex(etapa_dict["Rmax_real"])
    c_small = formatear_capacitor_latex(etapa_dict["Csmall"])
    c_big = formatear_capacitor_latex(etapa_dict["Cbig"])

    elm.style(elm.STYLE_IEEE)
    d = schemdraw.Drawing(show=False)
    if dark:
        d.config(unit=3.0, fontsize=18, lw=2.2, color="#e6edf3", bgcolor="#0d1117")
    else:
        d.config(unit=3.0, fontsize=18, lw=2.2, color="black", bgcolor="white")

    if topologia == "Sallen-Key" and resp == "High-Pass":
        _dibujar_base_sallen_key(d)
        d += elm.Resistor().at((7.5, 4.5)).to((7.5, 1.5)).label("$R_1$", loc="top").label(r_max, loc="bottom")
        d += elm.Resistor().at((10.5, 13.5)).to((13.5, 13.5)).label("$R_2$", loc="top").label(r_min, loc="bottom")
        d += elm.Capacitor().at((4.5, 9)).to((7.5, 9)).label("$C_1$", loc="top").label(c_big, loc="bottom")
        d += elm.Capacitor().at((0, 9)).to((3, 9)).label("$C_2$", loc="top").label(c_small, loc="bottom")

    elif topologia == "Sallen-Key" and resp == "Low-Pass":
        _dibujar_base_sallen_key(d)
        d += elm.Resistor().at((3, 9)).to((0, 9)).label("$R_1$", loc="top").label(r_min, loc="bottom")
        d += elm.Resistor().at((4.5, 9)).to((7.5, 9)).label("$R_2$", loc="top").label(r_max, loc="bottom")
        d += elm.Capacitor().at((10.5, 13.5)).to((13.5, 13.5)).label("$C_1$", loc="top").label(c_big, loc="bottom")
        d += elm.Capacitor().at((7.5, 4.5)).to((7.5, 1.5)).label("$C_2$", loc="top").label(c_small, loc="bottom")

    elif topologia == "MFB" and resp == "High-Pass":
        _dibujar_base_mfb(d)
        d += elm.Resistor().at((4.5, 4.5)).to((4.5, 7.5)).label("$R_1$", loc="top").label(r_min, loc="bottom")
        d += elm.Resistor().at((9, 12)).to((9, 9)).label("$R_2$", loc="top").label(r_max, loc="bottom")
        d += elm.Capacitor().at((4.5, 9)).to((7.5, 9)).label("$C_1$", loc="top").label(c_big, loc="bottom")
        d += elm.Capacitor().at((3, 9)).to((0, 9)).label("$C_2$", loc="top").label(c_small, loc="bottom")
        d += elm.Capacitor().at((6, 13.5)).to((9, 13.5)).label("$C_3$", loc="top").label(c_small, loc="bottom")

    elif topologia == "MFB" and resp == "Low-Pass":
        _dibujar_base_mfb(d)
        d += elm.Resistor().at((4.5, 9)).to((7.5, 9)).label("$R_1$", loc="top").label(r_max, loc="bottom")
        d += elm.Resistor().at((3, 9)).to((0, 9)).label("$R_2$", loc="top").label(r_min, loc="bottom")
        d += elm.Resistor().at((6, 13.5)).to((9, 13.5)).label("$R_3$", loc="top").label(r_min, loc="bottom")
        d += elm.Capacitor().at((9, 12)).to((9, 9)).label("$C_1$", loc="top").label(c_small, loc="bottom")
        d += elm.Capacitor().at((4.5, 4.5)).to((4.5, 7.5)).label("$C_2$", loc="top").label(c_big, loc="bottom")

    return d


def generar_diagrama_etapa_bytes(etapa_dict: dict, topologia: str) -> str:
    """Devuelve el PNG en base64 del diagrama de una etapa para mostrar en la UI."""
    d = construir_drawing_etapa(etapa_dict, topologia, dark=True)
    try:
        img_bytes = d.get_imagedata("png")
        return base64.b64encode(img_bytes).decode()
    finally:
        if d.fig is not None and hasattr(d.fig, "fig"):
            plt.close(d.fig.fig)


def guardar_diagrama_etapa(
    etapa_dict: dict,
    topologia: str,
    output_dir: str = "output",
    fmt: str = "png",
) -> str:
    """Guarda el diagrama de una etapa en modo claro en output/ y devuelve su ruta."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    topo_clean = topologia.lower().replace("-", "_").replace(" ", "_")
    etapa_clean = str(etapa_dict.get("etapa", "1")).replace(" ", "_")
    ext = fmt.lower().lstrip(".")
    file_path = out_path / f"diagrama_{topo_clean}_etapa_{etapa_clean}.{ext}"

    d = construir_drawing_etapa(etapa_dict, topologia, dark=False)
    try:
        if ext == "png":
            d.save(str(file_path), transparent=False, dpi=300)
        else:
            d.save(str(file_path), transparent=False)
        return str(file_path)
    finally:
        if d.fig is not None and hasattr(d.fig, "fig"):
            plt.close(d.fig.fig)
