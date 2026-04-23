import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración y Estilo
st.set_page_config(page_title="Executive Dashboard V2", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #fcfcfc; }
    /* Mejorar legibilidad de tablas */
    .stDataFrame td, .stDataFrame th { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga de datos
@st.cache_data
def load_data():
    df = pd.read_csv('2026-04-07 10_13am.csv')
    df['MES'] = pd.to_datetime(df['MES'])
    df = df[df['MES'].dt.month.isin([3, 4])].copy()
    df['Mes_Nombre'] = df['MES'].dt.month_name().replace({'March': 'Marzo', 'April': 'Abril'})
    df['SQUAD'] = df['SQUAD'].str.replace('_', ' ').str.title()
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🎯 Filtros de Control")
squad_filtro = st.sidebar.multiselect("👥 Seleccionar SQUAD", options=df['SQUAD'].unique(), default=df['SQUAD'].unique())
marca_filtro = st.sidebar.multiselect("🍔 Filtrar Marcas", options=df['BRAND_NAME'].unique())

# Aplicar filtros a la base principal
df_filtrado = df[df['SQUAD'].isin(squad_filtro)]
if marca_filtro:
    df_filtrado = df_filtrado[df_filtrado['BRAND_NAME'].isin(marca_filtro)]

# Separación por meses para KPIs
df_marzo = df_filtrado[df_filtrado['Mes_Nombre'] == 'Marzo']
df_abril = df_filtrado[df_filtrado['Mes_Nombre'] == 'Abril']

# --- CÁLCULOS ENCABEZADO ---
org_abril = df_abril[df_abril['TIPO'] == 'ORG']['ORDENES'].sum()
inorg_abril = df_abril[df_abril['TIPO'] == 'INORG']['ORDENES'].sum()
spend_react_abril = df_abril['SPEND_REACTIVACION'].sum()

total_marzo = df_marzo['ORDENES'].sum()
total_abril = df_abril['ORDENES'].sum()
crecimiento = ((total_abril - total_marzo) / total_marzo * 100) if total_marzo > 0 else 0

# ==========================================
# 1) ENCABEZADO (KPIs DE ABRIL)
# ==========================================
st.title("📊 Reporte Ejecutivo: Rendimiento Marzo vs Abril")
st.caption(f"Filtros aplicados: SQUADs ({len(squad_filtro)}) | Marcas ({len(marca_filtro) if marca_filtro else 'Todas'})")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🌱 Órd. Orgánicas (Abril)", f"{org_abril:,.2f}")
k2.metric("💰 Órd. Inorgánicas (Abril)", f"{inorg_abril:,.2f}")
k3.metric("💸 Spend Reactivación (Abril)", f"${spend_react_abril:,.2f}")
k4.metric("% Crecimiento vs Marzo", f"{crecimiento:.2f}%", delta=f"{crecimiento:.2f}%")

st.divider()

# ==========================================
# 2) TABLA 1: RESUMEN MENSUAL
# ==========================================
st.subheader("📋 Tabla 1: Comparativa Mensual")
tabla1 = df_filtrado.groupby('Mes_Nombre').agg({
    'ORDENES': 'sum',
    'SPEND_TOTAL': 'sum',
    'SPEND_RESTAURANTES': 'sum',
    'SPEND_REACTIVACION': 'sum'
}).reindex(['Marzo', 'Abril'])

st.table(tabla1.style.format("{:,.2f}"))

# ==========================================
# 3) TABLA 2: GASTO COMBINADO (COLORES CORREGIDOS)
# ==========================================
st.subheader("💵 Tabla 2: Análisis de Inversión Combinada")
df_filtrado['GASTO_COMBINADO'] = df_filtrado['SPEND_RESTAURANTES'] + df_filtrado['SPEND_REACTIVACION']
tabla2 = df_filtrado.groupby('Mes_Nombre').agg({
    'SPEND_RESTAURANTES': 'sum',
    'SPEND_REACTIVACION': 'sum',
    'GASTO_COMBINADO': 'sum'
}).reindex(['Marzo', 'Abril'])

# Usamos un color de fondo más oscuro con texto negro para que se lea perfecto
st.dataframe(
    tabla2.style.format("{:,.2f}")
    .background_gradient(cmap='Blues', axis=0)
    .set_properties(**{'color': 'black', 'font-weight': 'bold'}),
    use_container_width=True
)

# ==========================================
# 4) TABLA TOP 10 BRANDS: MARZO VS ABRIL
# ==========================================
st.subheader("🏆 Tabla Detallada: Top 10 Marcas (Marzo vs Abril)")
top_10_names = df_filtrado.groupby('BRAND_NAME')['ORDENES'].sum().nlargest(10).index
df_top10 = df_filtrado[df_filtrado['BRAND_NAME'].isin(top_10_names)]

# Agrupamos por marca y mes para ver todas las métricas
tabla_top10 = df_top10.groupby(['BRAND_NAME', 'Mes_Nombre']).agg({
    'ORDENES': 'sum',
    'SPEND_REACTIVACION': 'sum',
    'SPEND_RESTAURANTES': 'sum',
    'SPEND_TOTAL': 'sum'
}).sort_index(level=0)

st.dataframe(tabla_top10.style.format("{:,.2f}"), use_container_width=True)

# ==========================================
# 5) TABLA 3: FREQ TIER
# ==========================================
col_left, col_right = st.columns([1, 1])
with col_left:
    st.subheader("🎯 Desempeño por Freq Tier")
    tabla3 = df_filtrado.groupby('FREQ_TIER').agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum'}).sort_values('ORDENES', ascending=False)
    st.dataframe(tabla3.style.format("{:,.2f}"), use_container_width=True)

# ==========================================
# 6) ANÁLISIS DE DATOS
# ==========================================
with col_right:
    st.subheader("🧐 Insights del Periodo")
    gasto_abr = df_abril['SPEND_TOTAL'].sum()
    cpo_abr = (gasto_abr / total_abril) if total_abril > 0 else 0
    
    st.info(f"""
    **Análisis Ejecutivo de Abril:**
    * **Costo por Orden (CPO):** El CPO promedio de este mes cerró en **${cpo_abr:.2f}**.
    * **Mix de Órdenes:** De cada 100 pedidos, **{((org_abril/total_abril)*100) if total_abril > 0 else 0:.2f}** son orgánicos.
    * **Inversión Operativa:** El gasto combinado (Restaurantes + Reactivación) en Abril suma **${tabla2.loc['Abril', 'GASTO_COMBINADO']:,.2f}**.
    * **Tendencia:** El crecimiento de órdenes del **{crecimiento:.2f}%** indica {'un aumento en la tracción' if crecimiento > 0 else 'una contracción'} comparado con el mes anterior.
    """)
