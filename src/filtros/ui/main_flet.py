import sys
from pathlib import Path

# Asegurar que 'src/' esté en sys.path sin necesidad de configurar PYTHONPATH en Mac/Linux/Windows
_SRC_DIR = str(Path(__file__).resolve().parents[2])
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

import flet as ft

from filtros.search.search_best_filter import disenar_filtro_mfb_con_busqueda
from filtros.search.search_best_filter_sk import disenar_filtro_sallen_key_con_busqueda
from filtros.plot.bode_ideal_fig import generar_bode_ideal_bytes
from filtros.plot.diagrama_etapa import (
    generar_diagrama_etapa_bytes,
    guardar_diagrama_etapa,
)


TIPOS_FILTRO = [
    "Butterworth",
    "Bessel",
    "1-dB Chebyshev",
    "3-dB Chebyshev",
]

TOPOLOGIAS = ["MFB", "Sallen-Key"]

RESPUESTAS = [
    "Low-Pass",
    "High-Pass",
    "Band-Pass (Cascada HP+LP)",
]

ORDENES = ["2", "4", "6", "8", "10"]


def main(page: ft.Page):
    page.title = "Diseño de Filtros Activos"
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(color_scheme_seed="indigo")
    page.window.width = 1500
    page.window.height = 900
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # ── Title ──────────────────────────────────────────────────────
    title = ft.Text(
        "DISEÑO DE FILTROS ACTIVOS",
        size=26,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.INDIGO_200,
    )

    # ── Input controls ─────────────────────────────────────────────
    fc_input = ft.TextField(
        label="Frecuencia de corte (Hz)",
        value="1000",
        border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
    )

    fc2_input = ft.TextField(
        label="Frecuencia de corte superior fH (Hz)",
        value="5000",
        border_radius=8,
        keyboard_type=ft.KeyboardType.NUMBER,
        visible=False,
    )

    def on_respuesta_change(e):
        es_cascada = respuesta_dropdown.value == "Band-Pass (Cascada HP+LP)"
        fc2_input.visible = es_cascada
        if es_cascada:
            fc_input.label = "Frecuencia de corte inferior fL (Hz)"
        else:
            fc_input.label = "Frecuencia de corte (Hz)"
        page.update()

    respuesta_dropdown = ft.Dropdown(
        label="Respuesta del filtro",
        value="Low-Pass",
        border_radius=8,
        options=[ft.dropdown.Option(r) for r in RESPUESTAS],
        on_select=on_respuesta_change,
    )

    orden_dropdown = ft.Dropdown(
        label="Orden del filtro",
        value="4",
        border_radius=8,
        options=[ft.dropdown.Option(o) for o in ORDENES],
    )

    topologia_dropdown = ft.Dropdown(
        label="Topología",
        value="MFB",
        border_radius=8,
        options=[ft.dropdown.Option(t) for t in TOPOLOGIAS],
    )

    tipo_dropdown = ft.Dropdown(
        label="Tipo de filtro",
        value="Butterworth",
        border_radius=8,
        options=[ft.dropdown.Option(t) for t in TIPOS_FILTRO],
    )

    yaml_path = ft.TextField(
        label="Archivo inventario (YAML)",
        value="data/valores.yaml",
        border_radius=8,
    )

    tablas_path = ft.TextField(
        label="Archivo tablas TI (CSV)",
        value="data/filtros_pares.csv",
        border_radius=8,
    )

    # ── Status ─────────────────────────────────────────────────────
    status_icon = ft.Icon(
        ft.Icons.CHECK_CIRCLE,
        color=ft.Colors.GREEN_400,
        visible=False,
        size=18,
    )

    status_text = ft.Text("", size=12, selectable=True)

    # ── Results table ──────────────────────────────────────────────
    tabla = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Etapa")),
            ft.DataColumn(ft.Text("Q")),
            ft.DataColumn(ft.Text("fsf")),
            ft.DataColumn(ft.Text("f0 (Hz)")),
            ft.DataColumn(ft.Text("Csmall (F)")),
            ft.DataColumn(ft.Text("Cbig (F)")),
            ft.DataColumn(ft.Text("Rmin (ohm)")),
            ft.DataColumn(ft.Text("Rmax (ohm)")),
            ft.DataColumn(ft.Text("err Rmin (%)")),
            ft.DataColumn(ft.Text("err Rmax (%)")),
            ft.DataColumn(ft.Text("Estado")),
        ],
        rows=[],
        column_spacing=14,
        heading_text_style=ft.TextStyle(weight=ft.FontWeight.BOLD, size=12),
        data_text_style=ft.TextStyle(size=12),
    )

    # ── Bode plot images ───────────────────────────────────────────
    # 1x1 pixel transparent PNG data URI placeholder
    _BLANK_SRC = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

    ideal_image = ft.Image(
        src=_BLANK_SRC,
        fit=ft.BoxFit.CONTAIN,
        height=380,
        border_radius=10,
        visible=False,
    )

    # ── Stage schematics (large stage-by-stage viewer) ─────────────
    estado_actual = {
        "etapas_ok": [],
        "imagenes_b64": [],
        "topologia": "MFB",
        "respuesta": "Low-Pass",
        "idx": 0,
    }

    diagramas_placeholder = ft.Text(
        "Presiona Calcular para ver y descargar los diagramas etapa por etapa.",
        size=12,
        color=ft.Colors.GREY_400,
    )

    etapa_titulo_text = ft.Text(
        "",
        size=16,
        weight=ft.FontWeight.BOLD,
        color=ft.Colors.INDIGO_100,
        text_align=ft.TextAlign.CENTER,
    )

    diagrama_image = ft.Image(
        src=_BLANK_SRC,
        height=420,
        fit=ft.BoxFit.CONTAIN,
        border_radius=10,
        visible=False,
    )

    def _guardar_etapas_y_notificar(
        etapas_a_guardar: list[dict], topologia_actual: str, resumen_ok: str
    ) -> None:
        try:
            rutas_png = []
            for etapa_item in etapas_a_guardar:
                ruta_png = guardar_diagrama_etapa(
                    etapa_item, topologia_actual, output_dir="output", fmt="png"
                )
                guardar_diagrama_etapa(
                    etapa_item, topologia_actual, output_dir="output", fmt="svg"
                )
                rutas_png.append(ruta_png)
            ruta_dir = str(Path(rutas_png[0]).resolve().parent)
            msg = f"{resumen_ok} en: {ruta_dir}"
            status_text.value = msg
            status_text.color = ft.Colors.GREEN_400
            page.show_dialog(ft.SnackBar(content=ft.Text(msg)))
            page.update()
        except Exception as ex:
            msg = f"Error al guardar diagramas: {ex}"
            status_text.value = msg
            status_text.color = ft.Colors.RED_400
            page.show_dialog(ft.SnackBar(content=ft.Text(msg)))
            page.update()

    def actualizar_vista_etapa(do_update: bool = True) -> None:
        etapas = estado_actual["etapas_ok"]
        imagenes = estado_actual["imagenes_b64"]
        total = len(etapas)
        if total == 0:
            nav_row.visible = False
            diagrama_image.visible = False
            diagrama_image.src = _BLANK_SRC
            diagramas_placeholder.visible = True
            btn_guardar_actual.visible = False
            boton_descargar_todos.visible = False
            btn_prev_etapa.disabled = True
            btn_next_etapa.disabled = True
            etapa_titulo_text.value = ""
        else:
            idx = max(0, min(estado_actual["idx"], total - 1))
            estado_actual["idx"] = idx
            r = etapas[idx]
            resp_etapa = r.get("respuesta", estado_actual["respuesta"])
            topo = estado_actual["topologia"]
            etapa_titulo_text.value = (
                f"Etapa {r['etapa']} ({idx + 1} de {total} · {topo} - {resp_etapa}) — "
                f"f0 = {r['f0_hz']:.4g} Hz, Q = {r['Q']:.4g}"
            )
            diagrama_image.src = f"data:image/png;base64,{imagenes[idx]}"
            diagrama_image.visible = True
            nav_row.visible = True
            diagramas_placeholder.visible = False
            btn_guardar_actual.visible = True
            boton_descargar_todos.visible = True
            btn_prev_etapa.disabled = idx <= 0
            btn_next_etapa.disabled = idx >= total - 1

        if do_update:
            page.update()

    def on_prev_etapa(ev):
        if estado_actual["idx"] > 0:
            estado_actual["idx"] -= 1
            actualizar_vista_etapa()

    def on_next_etapa(ev):
        if estado_actual["idx"] < len(estado_actual["etapas_ok"]) - 1:
            estado_actual["idx"] += 1
            actualizar_vista_etapa()

    def on_guardar_actual_click(ev):
        etapas = estado_actual["etapas_ok"]
        if not etapas:
            page.show_dialog(ft.SnackBar(content=ft.Text("No hay etapa seleccionada.")))
            return
        r = etapas[estado_actual["idx"]]
        _guardar_etapas_y_notificar(
            [r],
            estado_actual["topologia"],
            f"Etapa {r['etapa']} guardada (PNG + SVG)",
        )

    def on_descargar_todos_click(ev):
        etapas = estado_actual["etapas_ok"]
        if not etapas:
            page.show_dialog(
                ft.SnackBar(content=ft.Text("No hay etapas válidas para guardar."))
            )
            return
        _guardar_etapas_y_notificar(
            etapas,
            estado_actual["topologia"],
            f"Guardados {len(etapas)} diagramas (PNG + SVG)",
        )

    btn_prev_etapa = ft.OutlinedButton(
        "◀ Etapa anterior",
        on_click=on_prev_etapa,
        disabled=True,
    )

    btn_next_etapa = ft.OutlinedButton(
        "Siguiente etapa ▶",
        on_click=on_next_etapa,
        disabled=True,
    )

    nav_row = ft.Row(
        [btn_prev_etapa, etapa_titulo_text, btn_next_etapa],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
        wrap=True,
        visible=False,
    )

    btn_guardar_actual = ft.FilledTonalButton(
        "Guardar esta etapa (PNG + SVG)",
        icon=ft.Icons.DOWNLOAD,
        on_click=on_guardar_actual_click,
        visible=False,
    )

    boton_descargar_todos = ft.OutlinedButton(
        "Descargar todas (PNG + SVG)",
        icon=ft.Icons.DOWNLOAD,
        on_click=on_descargar_todos_click,
        visible=False,
    )

    # ── on_calcular_click ──────────────────────────────────────────
    def on_calcular_click(e):
        # Reset UI
        tabla.rows.clear()
        estado_actual["etapas_ok"] = []
        estado_actual["imagenes_b64"] = []
        estado_actual["idx"] = 0
        actualizar_vista_etapa(do_update=False)
        status_text.value = ""
        status_icon.visible = False
        ideal_image.visible = False
        ideal_image.src = _BLANK_SRC
        page.update()

        # Validate fc
        try:
            fc = float(fc_input.value)
        except ValueError:
            status_text.value = "Error: frecuencia de corte no válida"
            status_text.color = ft.Colors.RED_400
            page.update()
            return

        # Validate orden
        try:
            orden = int(orden_dropdown.value)
        except (ValueError, TypeError):
            status_text.value = "Error: orden no válido"
            status_text.color = ft.Colors.RED_400
            page.update()
            return

        tipo = tipo_dropdown.value
        topologia = topologia_dropdown.value
        respuesta = respuesta_dropdown.value or "Low-Pass"
        path_yaml = yaml_path.value.strip()
        path_csv = tablas_path.value.strip()

        fc2 = None
        if respuesta == "Band-Pass (Cascada HP+LP)":
            try:
                fc2 = float(fc2_input.value)
                if fc2 <= 0:
                    raise ValueError()
            except ValueError:
                status_text.value = "Error: frecuencia superior fH no válida"
                status_text.color = ft.Colors.RED_400
                page.update()
                return

        # Run search
        try:
            if topologia == "MFB":
                resultados = disenar_filtro_mfb_con_busqueda(
                    fc_global_hz=fc,
                    orden=orden,
                    tipo_filtro=tipo,
                    path_yaml=path_yaml,
                    path_csv_tablas=path_csv,
                    respuesta=respuesta,
                    fc2_hz=fc2,
                )
            else:
                resultados = disenar_filtro_sallen_key_con_busqueda(
                    fc_global_hz=fc,
                    orden=orden,
                    tipo_filtro=tipo,
                    path_yaml=path_yaml,
                    path_csv_tablas=path_csv,
                    respuesta=respuesta,
                    fc2_hz=fc2,
                )
        except Exception as ex:
            status_text.value = f"Error en cálculo: {ex}"
            status_text.color = ft.Colors.RED_400
            page.update()
            return

        # Populate table
        for r in resultados:
            if r["status"] != "ok":
                estado = r.get("reason", "invalid")
                fila = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(r["etapa"]))),
                        ft.DataCell(ft.Text(f"{r.get('Q', '')}")),
                        ft.DataCell(ft.Text(f"{r.get('fsf', '')}")),
                        ft.DataCell(ft.Text(f"{r.get('f0_hz', '')}")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text("")),
                        ft.DataCell(ft.Text(estado, color=ft.Colors.RED_400)),
                    ]
                )
            else:
                fila = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(str(r["etapa"]))),
                        ft.DataCell(ft.Text(f"{r['Q']:.4g}")),
                        ft.DataCell(ft.Text(f"{r['fsf']:.4g}")),
                        ft.DataCell(ft.Text(f"{r['f0_hz']:.4g}")),
                        ft.DataCell(ft.Text(f"{r['Csmall']:.3e}")),
                        ft.DataCell(ft.Text(f"{r['Cbig']:.3e}")),
                        ft.DataCell(ft.Text(f"{r['Rmin_real']:.4g}")),
                        ft.DataCell(ft.Text(f"{r['Rmax_real']:.4g}")),
                        ft.DataCell(ft.Text(f"{r['err_Rmin_pct']:.2f}")),
                        ft.DataCell(ft.Text(f"{r['err_Rmax_pct']:.2f}")),
                        ft.DataCell(ft.Text("ok", color=ft.Colors.GREEN_400)),
                    ]
                )
            tabla.rows.append(fila)

        etapas_ok = []
        imagenes_b64 = []
        for r in resultados:
            if r["status"] != "ok":
                continue
            try:
                diag_b64 = generar_diagrama_etapa_bytes(r, topologia)
                etapas_ok.append(r)
                imagenes_b64.append(diag_b64)
            except Exception as ex:
                status_text.value = f"Etapa {r['etapa']} diagrama: {ex}"

        estado_actual["etapas_ok"] = etapas_ok
        estado_actual["imagenes_b64"] = imagenes_b64
        estado_actual["topologia"] = topologia
        estado_actual["respuesta"] = respuesta
        estado_actual["idx"] = 0
        actualizar_vista_etapa(do_update=False)

        # Generate Ideal Bode plot
        try:
            ideal_bytes = generar_bode_ideal_bytes(
                fc, tipo, orden, path_csv, respuesta=respuesta, fc2_hz=fc2
            )
            ideal_image.src = f"data:image/png;base64,{ideal_bytes}"
            ideal_image.visible = True
        except Exception as ex:
            ideal_image.visible = False
            status_text.value = f"Ideal Bode: {ex}"

        # Status summary
        ok_count = sum(1 for r in resultados if r["status"] == "ok")
        status_text.value = (
            f"Calculado: {ok_count}/{len(resultados)} etapas {topologia} ({respuesta}) "
            f"para {tipo}, orden {orden}, fc={fc} Hz"
        )
        status_text.color = (
            ft.Colors.GREEN_400 if ok_count == len(resultados) else ft.Colors.ORANGE_400
        )
        status_icon.visible = True
        page.update()

    boton_calcular = ft.FilledButton(
        "Calcular",
        icon=ft.Icons.CALCULATE,
        on_click=on_calcular_click,
        style=ft.ButtonStyle(
            padding=ft.Padding.symmetric(horizontal=24, vertical=12),
        ),
    )

    # ── Layout components ──────────────────────────────────────────

    # --- Parameters card (left, fixed width) ---
    params_card = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Text("PARÁMETROS", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_200),
                    ft.Divider(height=1),
                    respuesta_dropdown,
                    fc_input,
                    fc2_input,
                    orden_dropdown,
                    topologia_dropdown,
                    tipo_dropdown,
                    yaml_path,
                    tablas_path,
                    boton_calcular,
                    ft.Divider(height=1),
                    ft.Row([status_icon, status_text], spacing=8),
                ],
                spacing=12,
            ),
        ),
        elevation=4,
    )

    # --- Results card (top-right) ---
    results_card = ft.Card(
        content=ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Text("RESULTADOS", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_200),
                    ft.Divider(height=1),
                    ft.Row(
                        [tabla],
                        scroll=ft.ScrollMode.AUTO,
                    ),
                ],
                spacing=12,
            ),
        ),
        elevation=4,
    )

    # --- Stage diagram card (middle-right, large stage-by-stage view) ---
    diagramas_card = ft.Card(
        content=ft.Container(
            padding=16,
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Text(
                                "DIAGRAMA DE ETAPA",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.INDIGO_200,
                            ),
                            ft.Row(
                                [btn_guardar_actual, boton_descargar_todos],
                                spacing=8,
                                wrap=True,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        wrap=True,
                    ),
                    ft.Divider(height=1),
                    diagramas_placeholder,
                    nav_row,
                    ft.Container(
                        content=diagrama_image,
                        alignment=ft.Alignment.CENTER,
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ),
        elevation=4,
    )

    # --- Bode plot card (bottom-right) ---
    bode_card = ft.Card(
        content=ft.Container(
            padding=16,
            content=ft.Column(
                [
                    ft.Text("BODE - MAGNITUD IDEAL", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_200),
                    ft.Divider(height=1),
                    ft.Container(
                        content=ideal_image,
                        alignment=ft.Alignment.CENTER,
                    ),
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
            ),
        ),
        elevation=4,
    )

    # Right panel: full-width stacked cards with vertical scroll
    right_panel = ft.Column(
        [
            results_card,
            diagramas_card,
            bode_card,
        ],
        spacing=16,
        expand=True,
        scroll=ft.ScrollMode.AUTO,
    )

    # ── Main layout ────────────────────────────────────────────────
    page.add(
        title,
        ft.Row(
            [
                ft.Container(content=params_card, width=320),
                right_panel,
            ],
            spacing=16,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START,
        ),
    )


if __name__ == "__main__":
    ft.run(main)
