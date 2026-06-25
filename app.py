import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import matplotlib.dates as mdates
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from matplotlib.patches import Rectangle
import textwrap

st.set_page_config(page_title="Dashboard CSEN 2026", layout="wide")

st.title("Dashboard de Seguimiento de Cursos CSEN 2026")

# =========================
# 1. Leer Google Sheet
# =========================

sheet_id = "1yPX4RkH9UAxRE5iDhrL1LD1htuaNuUKK"
url_cursos = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=CURSOS"

df_cursos = pd.read_csv(url_cursos)
df_cursos = df_cursos.loc[:, ~df_cursos.columns.str.contains("^Unnamed")]
df_cursos = df_cursos.dropna(axis=1, how="all")

# =========================
# 2. Preparar datos
# =========================

df = df_cursos.copy()
df.columns = df.columns.str.strip().str.upper()

df["FECHA INICIO"] = pd.to_datetime(df["FECHA INICIO"], dayfirst=True, errors="coerce")
df["FECHA FINAL"] = pd.to_datetime(df["FECHA FINAL"], dayfirst=True, errors="coerce")
df["ESTADO"] = df["ESTADO"].astype(str).str.strip().str.upper()

df = df[df["ESTADO"] != "FINALIZADO"].copy()
df = df.dropna(subset=["FECHA INICIO", "FECHA FINAL"]).copy()
df = df.sort_values("FECHA INICIO").reset_index(drop=True)

df["DURACION"] = (df["FECHA FINAL"] - df["FECHA INICIO"]).dt.days + 1

colores = {
    "EJECUCION": "#2E8B57",
    "EJECUCIÓN": "#2E8B57",
    "PROGRAMADO": "#1E63D6"
}

df["COLOR"] = df["ESTADO"].map(colores).fillna("#777777")

# =========================
# 3. Indicadores
# =========================

total = len(df)
ejecucion = len(df[df["ESTADO"].isin(["EJECUCION", "EJECUCIÓN"])])
programado = len(df[df["ESTADO"] == "PROGRAMADO"])

c1, c2, c3 = st.columns(3)
c1.metric("Total de cursos activos", total)
c2.metric("En ejecución", ejecucion)
c3.metric("Programados", programado)

# =========================
# 4. Crear Gantt
# =========================

inicio = pd.Timestamp("2026-03-01")
fin = pd.Timestamp("2026-09-30")
n = len(df)

fig = plt.figure(figsize=(26, 10))
gs = fig.add_gridspec(1, 2, width_ratios=[1.35, 2.4], wspace=0.02)

ax_table = fig.add_subplot(gs[0, 0])
ax_gantt = fig.add_subplot(gs[0, 1])

fig.patch.set_facecolor("white")
ax_table.set_facecolor("white")
ax_gantt.set_facecolor("white")

# Panel izquierdo
ax_table.set_xlim(0, 1)
ax_table.set_ylim(-1, n)
ax_table.axis("off")

headers = ["N°", "CURSO", "LUGAR", "ESTADO", "RESP."]
x_cols = [0.02, 0.09, 0.55, 0.73, 0.88]

ax_table.add_patch(Rectangle((0, -1), 1, 0.8, facecolor="#082B63", edgecolor="none"))

for x, h in zip(x_cols, headers):
    ax_table.text(x, -0.55, h, color="white", fontsize=10, fontweight="bold", va="center")

for i, row in df.iterrows():
    y = i
    fondo = "#F6F9FD" if i % 2 == 0 else "#FFFFFF"

    ax_table.add_patch(
        Rectangle((0, y - 0.4), 1, 0.8, facecolor=fondo, edgecolor="#D8E0EA", linewidth=0.6)
    )

    curso = textwrap.fill(row["NOMBRE DEL CURSO"], width=34)
    lugar = textwrap.fill(str(row.get("LUGAR", "")), width=15)
    estado = row["ESTADO"]
    resp = textwrap.fill(str(row.get("RESPONSABLE", "")), width=12)

    ax_table.text(0.02, y, str(i + 1), fontsize=9, color="#243746", va="center")
    ax_table.text(0.09, y, curso, fontsize=8.5, color="#243746", va="center")
    ax_table.text(0.55, y, lugar, fontsize=8.5, color="#243746", va="center")

    ax_table.add_patch(
        Rectangle((0.72, y - 0.18), 0.13, 0.36, facecolor=row["COLOR"], edgecolor="none")
    )
    ax_table.text(
        0.785, y, estado, fontsize=7.5, color="white",
        va="center", ha="center", fontweight="bold"
    )

    ax_table.text(0.88, y, resp, fontsize=8.2, color="#243746", va="center")

ax_table.invert_yaxis()

# Panel derecho
ax_gantt.set_xlim(inicio, fin)
ax_gantt.set_ylim(-1, n)

for idx, mes in enumerate(pd.date_range(inicio, fin, freq="MS")):
    siguiente = mes + pd.offsets.MonthBegin(1)
    color_fondo = "#F6F9FD" if idx % 2 == 0 else "#FFFFFF"
    ax_gantt.axvspan(mes, siguiente, color=color_fondo, zorder=0)

for d in pd.date_range(inicio, fin, freq="7D"):
    ax_gantt.axvline(d, color="#D7E0EC", linewidth=0.7, zorder=1)

for i in range(n):
    ax_gantt.axhline(i + 0.5, color="#D8E0EA", linewidth=0.6, zorder=1)

for i, row in df.iterrows():
    altura = 0.80 if row["DURACION"] > 7 else 1.00

    ax_gantt.barh(
        i,
        row["DURACION"],
        left=row["FECHA INICIO"],
        height=altura,
        color=row["COLOR"],
        edgecolor="white",
        linewidth=1.5,
        zorder=3
    )

    fecha_texto = f'{row["FECHA INICIO"].strftime("%d/%m")} - {row["FECHA FINAL"].strftime("%d/%m")}'
    centro = row["FECHA INICIO"] + (row["FECHA FINAL"] - row["FECHA INICIO"]) / 2

    ax_gantt.text(
        centro,
        i - 0.48,
        fecha_texto,
        ha="center",
        va="center",
        fontsize=9,
        fontweight="bold",
        color="#082B63",
        zorder=4
    )

ax_gantt.invert_yaxis()
ax_gantt.xaxis.set_major_locator(mdates.MonthLocator())
ax_gantt.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))

ax_gantt.tick_params(
    axis="x",
    labelsize=11,
    colors="#082B63",
    top=True,
    labeltop=True,
    bottom=False,
    labelbottom=False
)

ax_gantt.set_yticks([])

for spine in ax_gantt.spines.values():
    spine.set_visible(False)

fig.suptitle(
    "CRONOGRAMA DE CURSOS ORDINARIOS 2026",
    fontsize=26,
    fontweight="bold",
    color="#082B63",
    y=0.98
)

fig.text(
    0.5,
    0.93,
    "Periodo: marzo – septiembre 2026",
    ha="center",
    fontsize=14,
    color="#082B63",
    fontweight="bold"
)

resumen = (
    f"Total de cursos: {total}    |    "
    f"En ejecución: {ejecucion}    |    "
    f"Programados: {programado}    |    "
    f"Actualizado: 24 de junio de 2026"
)

fig.text(
    0.5,
    0.035,
    resumen,
    ha="center",
    fontsize=13,
    color="#082B63",
    fontweight="bold",
    bbox=dict(
        boxstyle="round,pad=0.7",
        facecolor="#EEF4FB",
        edgecolor="#C6D6EA"
    )
)

legend_items = [
    Rectangle((0, 0), 1, 1, color="#2E8B57", label="EJECUCIÓN"),
    Rectangle((0, 0), 1, 1, color="#1E63D6", label="PROGRAMADO")
]

fig.legend(
    handles=legend_items,
    loc="lower center",
    bbox_to_anchor=(0.5, 0.075),
    ncol=2,
    frameon=False,
    fontsize=12
)

plt.tight_layout(rect=[0.02, 0.12, 0.98, 0.90])

#st.pyplot(fig)
st.subheader("Cronograma interactivo avanzado")

import plotly.graph_objects as go
from plotly.subplots import make_subplots

df_go = df.copy()
df_go = df_go.sort_values("FECHA INICIO").reset_index(drop=True)

df_go["FECHA TEXTO"] = (
    df_go["FECHA INICIO"].dt.strftime("%d/%m")
    + " - "
    + df_go["FECHA FINAL"].dt.strftime("%d/%m")
)

fig_go = make_subplots(
    rows=1,
    cols=2,
    column_widths=[0.42, 0.58],
    specs=[[{"type": "table"}, {"type": "bar"}]],
    horizontal_spacing=0.02
)

fig_go.add_trace(
    go.Table(
        header=dict(
            values=["N°", "CURSO", "LUGAR", "ESTADO", "RESP."],
            fill_color="#082B63",
            font=dict(color="white", size=13),
            align="left",
            height=34
        ),
        cells=dict(
            values=[
                list(range(1, len(df_go) + 1)),
                df_go["NOMBRE DEL CURSO"],
                df_go["LUGAR"],
                df_go["ESTADO"],
                df_go["RESPONSABLE"]
            ],
            fill_color=[
                ["#FFFFFF" if i % 2 else "#F6F9FD" for i in range(len(df_go))]
            ],
            font=dict(color="#082B63", size=12),
            align="left",
            height=38
        )
    ),
    row=1,
    col=1
)

for i, row in df_go.iterrows():

    color = "#2E8B57" if row["ESTADO"] in ["EJECUCION", "EJECUCIÓN"] else "#1E63D6"

    fig_go.add_trace(
        go.Scatter(
            x=[row["FECHA INICIO"], row["FECHA FINAL"]],
            y=[row["NOMBRE DEL CURSO"], row["NOMBRE DEL CURSO"]],
            mode="lines+text",
            line=dict(
                color=color,
                width=22
            ),
            text=["", row["FECHA TEXTO"]],
            textposition="middle right",
            name=row["ESTADO"],
            hovertemplate=(
                "<b>" + row["NOMBRE DEL CURSO"] + "</b><br>"
                "Lugar: " + str(row["LUGAR"]) + "<br>"
                "Responsable: " + str(row["RESPONSABLE"]) + "<br>"
                "Inicio: " + row["FECHA INICIO"].strftime("%d/%m/%Y") + "<br>"
                "Fin: " + row["FECHA FINAL"].strftime("%d/%m/%Y") + "<extra></extra>"
            ),
            showlegend=False
        ),
        row=1,
        col=2
    )
fig_go.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="lines",
        line=dict(color="#2E8B57", width=12),
        name="EJECUCIÓN"
    )
)

fig_go.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="lines",
        line=dict(color="#1E63D6", width=12),
        name="PROGRAMADO"
    )
)


fig_go.update_yaxes(
    autorange="reversed",
    showticklabels=False,
    row=1,
    col=2
)

fig_go.update_xaxes(
    type="date",
    side="top",
    tickformat="%b %Y",
    dtick="M1",
    showgrid=True,
    gridcolor="#D8E0EA",
    range=["2026-03-01", "2026-09-30"],
    row=1,
    col=2
)

fig_go.update_layout(
    title=dict(
        text="Cronograma de Cursos Ordinarios 2026",
        x=0.01,
        xanchor="left",
        font=dict(size=24, color="#082B63")
    ),
    height=720,
    barmode="overlay",
    bargap=0.45,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(color="#082B63"),
    margin=dict(l=20, r=40, t=90, b=60),
    legend=dict(
        orientation="h",
        y=-0.08,
        x=0.45
    )
)

st.plotly_chart(fig_go, use_container_width=True)

st.caption("Actualizado: 24 de junio de 2026")



st.subheader("Matriz de cursos")
columnas_visibles = [
    "NOMBRE DEL CURSO",
    "LUGAR",
    "ESTADO",
    "FECHA INICIO",
    "FECHA FINAL",
    "RESPONSABLE",
    "ACCIONES",
    "COORDINADOR"
]

columnas_visibles = [c for c in columnas_visibles if c in df_cursos.columns]

st.dataframe(df_cursos[columnas_visibles], use_container_width=True)
