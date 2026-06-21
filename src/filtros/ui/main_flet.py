import flet as ft

from filtros.search.search_best_filter import disenar_filtro_mfb_con_busqueda
from filtros.search.search_best_filter_sk import disenar_filtro_sallen_key_con_busqueda
from filtros.plot.bode_ideal_fig import generar_bode_ideal_bytes


TIPOS_FILTRO = [
    "Butterworth",
    "Bessel",
    "1-dB Chebyshev",
    "3-dB Chebyshev",
]

TOPOLOGIAS = ["MFB", "Sallen-Key"]

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
        fit="contain",
        border_radius=10,
        visible=False,
    )

    # ── on_calcular_click ──────────────────────────────────────────
    def on_calcular_click(e):
        # Reset UI
        tabla.rows.clear()
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
        path_yaml = yaml_path.value.strip()
        path_csv = tablas_path.value.strip()

        # Run search
        try:
            if topologia == "MFB":
                resultados = disenar_filtro_mfb_con_busqueda(
                    fc_global_hz=fc,
                    orden=orden,
                    tipo_filtro=tipo,
                    path_yaml=path_yaml,
                    path_csv_tablas=path_csv,
                )
            else:
                resultados = disenar_filtro_sallen_key_con_busqueda(
                    fc_global_hz=fc,
                    orden=orden,
                    tipo_filtro=tipo,
                    path_yaml=path_yaml,
                    path_csv_tablas=path_csv,
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

        # Generate Ideal Bode plot
        try:
            ideal_bytes = generar_bode_ideal_bytes(fc, tipo, orden, path_csv)
            ideal_image.src = f"data:image/png;base64,{ideal_bytes}"
            ideal_image.visible = True
        except Exception as ex:
            ideal_image.visible = False
            status_text.value = f"Ideal Bode: {ex}"

        # Status summary
        ok_count = sum(1 for r in resultados if r["status"] == "ok")
        status_text.value = (
            f"Calculado: {ok_count}/{len(resultados)} etapas {topologia} "
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
                    fc_input,
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
                        expand=True,
                    ),
                ],
                spacing=12,
                expand=True,
            ),
        ),
        elevation=4,
        expand=True,
    )

    # --- Bode plot card (bottom-right, single ideal plot) ---
    bode_card = ft.Card(
        content=ft.Container(
            padding=16,
            content=ft.Column(
                [
                    ft.Text("BODE - MAGNITUD IDEAL", size=16, weight=ft.FontWeight.BOLD, color=ft.Colors.INDIGO_200),
                    ft.Divider(height=1),
                    ideal_image,
                ],
                spacing=12,
                expand=True,
            ),
        ),
        elevation=4,
        expand=True,
    )

    # Right panel: results on top, Bode plots below
    right_panel = ft.Column(
        [
            ft.Container(content=results_card, expand=2),
            ft.Container(content=bode_card, expand=3),
        ],
        spacing=16,
        expand=True,
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
        ),
    )


if __name__ == "__main__":
    ft.run(main)
