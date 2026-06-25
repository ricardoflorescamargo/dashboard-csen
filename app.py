import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Dashboard CSEN 2026", layout="wide")
st.markdown(
    """
    <div style="background-color:#082B63; padding:22px; border-radius:12px; margin-bottom:20px;">
        <h1 style="color:white; margin:0;">Dashboard de Seguimiento de Cursos CSEN 2026</h1>
        <p style="color:#D8E0EA; margin:6px 0 0 0; font-size:18px;">
            Cronograma, estado y seguimiento académico de cursos
        </p>
        <p style="color:#D8E0EA; margin:6px 0 0 0; font-size:14px;">
            Actualizado: 24 de junio de 2026
        </p>
    </div>
    """,
    unsafe_allow_html=True
)

#st.image("logo.png", width=120)

# =========================
# Leer Google Sheet
# =========================

sheet_id = "1yPX4RkH9UAxRE5iDhrL1LD1htuaNuUKK"
url_cursos = f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet=CURSOS"

df_cursos = pd.read_csv(url_cursos)

# Limpiar columnas vacías
df_cursos = df_cursos.loc[:, ~df_cursos.columns.str.contains("^Unnamed")]
df_cursos = df_cursos.dropna(axis=1, how="all")

# Normalizar columnas
df_cursos.columns = df_cursos.columns.str.strip().str.upper()

# =========================
# Preparar datos
# =========================

df = df_cursos.copy()

df["FECHA INICIO"] = pd.to_datetime(df["FECHA INICIO"], dayfirst=True, errors="coerce")
df["FECHA FINAL"] = pd.to_datetime(df["FECHA FINAL"], dayfirst=True, errors="coerce")
df["ESTADO"] = df["ESTADO"].astype(str).str.strip().str.upper()

# Quitar registros sin fecha
df = df.dropna(subset=["FECHA INICIO", "FECHA FINAL"]).copy()

# Duración
df["DURACIÓN"] = (df["FECHA FINAL"] - df["FECHA INICIO"]).dt.days + 1

# Texto de fecha
df["PERIODO"] = (
    df["FECHA INICIO"].dt.strftime("%d/%m")
    + " - "
    + df["FECHA FINAL"].dt.strftime("%d/%m")
)

# =========================
# Filtros
# =========================

st.subheader("Filtro")

estado_opciones = ["TODOS"] + sorted(df["ESTADO"].dropna().unique())

estado_sel = st.selectbox(
    "Estado del curso",
    options=estado_opciones
)

if estado_sel == "TODOS":
    df_filtrado = df.copy()
else:
    df_filtrado = df[df["ESTADO"] == estado_sel].copy()

# =========================
# Indicadores
# =========================

total = len(df_filtrado)
ejecucion = len(df_filtrado[df_filtrado["ESTADO"].isin(["EJECUCION", "EJECUCIÓN"])])
programado = len(df_filtrado[df_filtrado["ESTADO"] == "PROGRAMADO"])
finalizado = len(df_filtrado[df_filtrado["ESTADO"] == "FINALIZADO"])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total de cursos", total)
c2.metric("En ejecución", ejecucion)
c3.metric("Programados", programado)
c4.metric("Finalizados", finalizado)

# =========================
# Gantt interactivo
# =========================

st.subheader("Cronograma Interactivo")

fig = px.timeline(
    df_filtrado.sort_values("FECHA INICIO"),
    x_start="FECHA INICIO",
    x_end="FECHA FINAL",
    y="NOMBRE DEL CURSO",
    color="ESTADO",
    text="PERIODO",
    hover_data=[
        "LUGAR",
        "RESPONSABLE",
        "COORDINADOR",
        "ACCIONES",
        "DURACIÓN"
    ],
    color_discrete_map={
        "EJECUCION": "#2E8B57",
        "EJECUCIÓN": "#2E8B57",
        "PROGRAMADO": "#1E63D6",
        "FINALIZADO": "#7A7D82"
    }
)

fig.update_yaxes(
    autorange="reversed",
    title="",
    tickfont=dict(size=12, color="#082B63"),
    automargin=True
)

fig.update_xaxes(
    side="top",
    showgrid=True,
    gridcolor="#D8E0EA",
    tickformat="%b %Y",
    dtick="M1",
    title=""
)

fig.update_traces(
    textposition="outside",
    textfont=dict(size=11, color="#082B63"),
    marker_line_color="white",
    marker_line_width=1.2,
    width=0.45
)

fig.update_layout(
    height=800,
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(size=12, color="#082B63"),
    margin=dict(l=420, r=40, t=80, b=60),
    legend_title_text="Estado",
    title=dict(
        text="Cronograma de Cursos CSEN 2026",
        x=0.01,
        xanchor="left",
        font=dict(size=22, color="#082B63")
    )
)

st.plotly_chart(fig, use_container_width=True)

# =========================
# Tabla
# =========================

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

st.dataframe(
    df_cursos[columnas_visibles],
    use_container_width=True,
    hide_index=True
)
