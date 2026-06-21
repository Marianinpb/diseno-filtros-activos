# Diseño de Filtros Activos

Aplicación interactiva para el diseño de **filtros activos analógicos** — MFB (*Multiple Feedback*) y Sallen-Key — con optimización automática por inventario real de componentes y visualización de gráficas Bode.

## Características

- **Dos topologías**: MFB y Sallen-Key (ganancia unitaria)
- **Cuatro tipos de filtro**: Butterworth, Bessel, Chebyshev 1-dB y 3-dB
- **Órdenes pares**: 2, 4, 6, 8 y 10
- **Optimización por inventario**: búsqueda exhaustiva de la mejor combinación de resistencias y capacitores reales (desde archivo YAML)
- **Gráfica Bode**: magnitud ideal calculada desde las tablas TI, renderizada en tiempo real
- **Interfaz oscura moderna**: construida con [Flet](https://flet.dev), tema dark con paleta indigo

## Instalación

```powershell
# Clonar el repositorio
git clone https://github.com/Marianinpb/diseno-filtros-activos.git
cd diseno-filtros-activos

# Crear entorno virtual (Python 3.10+)
python -m venv .venv
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Uso

**Opción 1 — Doble clic (Windows)**

Ejecutar `run.bat`

**Opción 2 — Línea de comandos**

```powershell
$env:PYTHONPATH = "src"
python src/filtros/ui/main_flet.py
```

**Parámetros de entrada:**

| Parámetro | Descripción | Ejemplo |
|-----------|-------------|---------|
| Frecuencia de corte | Hz | `1000` |
| Orden del filtro | Par: 2-10 | `4` |
| Topología | MFB o Sallen-Key | `MFB` |
| Tipo de filtro | Butterworth, Bessel, Chebyshev | `Butterworth` |
| Archivo inventario | YAML con resistencias y capacitores | `data/valores.yaml` |
| Archivo tablas TI | CSV con coeficientes FSF y Q | `data/filtros_pares.csv` |

## Estructura del proyecto

```
diseno-filtros-activos/
├── src/
│   └── filtros/                  # Paquete principal
│       ├── core/                 # Motores de diseño
│       │   ├── design_mfb.py     #   Diseño MFB
│       │   └── design_sallen_key.py  # Diseño Sallen-Key
│       ├── data/                 # Manejo de inventario
│       │   ├── inventario_yaml.py    # Parser YAML
│       │   └── inventory_match.py    # Match ideal→real
│       ├── search/               # Búsqueda y optimización
│       │   ├── search_best_stage.py      # Búsqueda por etapa
│       │   ├── search_best_filter.py     # Búsqueda filtro MFB
│       │   └── search_best_filter_sk.py  # Búsqueda filtro Sallen-Key
│       ├── plot/                 # Gráficas Bode
│       │   ├── bode_ideal_fig.py     # Bode ideal (tablas TI)
│       │   ├── bode_real_etapa.py    # Bode etapa individual
│       │   ├── bode_real_filtro.py   # Bode filtro MFB real
│       │   └── bode_real_sk.py       # Bode filtro Sallen-Key real
│       └── ui/                   # Interfaz gráfica
│           └── main_flet.py      # Aplicación Flet
├── scripts/                      # Scripts de entrada
│   ├── run_design_with_inventory.py  # Diseño + inventario (CLI)
│   └── test_diseno_mfb.py           # Tests de validación
├── data/                         # Archivos de datos
│   ├── filtros_pares.csv         # Tablas TI (FSF, Q)
│   └── valores.yaml              # Inventario de componentes
├── output/                       # Salidas generadas
│   └── bode_ideal.png            # Ejemplo de gráfica Bode
├── requirements.txt              # Dependencias Python
├── run.bat                       # Launcher Windows
└── README.md
```

## Cómo funciona

### 1. Diseño ideal (tablas TI)

El diseño parte de las **tablas de coeficientes normalizados** (`data/filtros_pares.csv`) que contienen los factores FSF (*Frequency Scaling Factor*) y Q para cada etapa, según tipo y orden del filtro.

Para una frecuencia de corte `fc` global:
- Cada etapa `i` tiene su propia frecuencia efectiva: `f0_i = fc × FSF_i`
- Los valores ideales de resistencias y capacitores se calculan con las fórmulas de diseño de cada topología

### 2. Búsqueda por inventario

El módulo `search/` realiza una **búsqueda exhaustiva** sobre todas las combinaciones de capacitores disponibles en el inventario YAML. Para cada par (Csmall, Cbig):

1. Calcula los valores ideales de Rmin y Rmax
2. Encuentra los valores reales más cercanos en el inventario de resistencias
3. Minimiza el error relativo combinado

### 3. Gráfica Bode

La gráfica de magnitud Bode se genera calculando la función de transferencia total como el producto de las funciones de transferencia de cada etapa:

```
H_total(s) = ∏ H_i(s)

MFB:  H_i(s) = -1 / (s²·R₂R₃C₁C₂ + s·(R₃C₁ + R₂C₁ + R₂R₃C₁/R₁) + 1)
S-K:  H_i(s) =  1 / (s²·R₁R₂C₁C₂ + s·C₁·(R₁+R₂) + 1)
```

## Dependencias principales

| Paquete | Uso |
|---------|-----|
| `flet` | Interfaz gráfica de escritorio |
| `numpy` | Cálculo numérico, polinomios |
| `scipy` | Funciones de transferencia, `signal.bode` |
| `matplotlib` | Renderizado de gráficas Bode |
| `pyyaml` | Lectura del inventario de componentes |

## Licencia

MIT — ver [LICENSE](LICENSE)
