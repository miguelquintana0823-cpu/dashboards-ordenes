import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración y Estilo
st.set_page_config(page_title="Executive Dashboard", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #fcfcfc; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga de datos
@st.cache_data
def load_data():
    df = pd.read_csv('2026-04-07 10_13am.csv')
    df['MES'] = pd.to_datetime(df['MES'])
    # Nos enfocamos solo en Marzo y Abril
    df = df[df['MES'].dt.month.isin([3, 4])].copy()
    df['Mes_Nombre'] = df['MES'].dt.month_name().replace({'March': 'Marzo', 'April': 'Abril'})
    return df

df = load_data()

# --- CÁLCULOS PARA EL ENCABEZADO (KPIs) ---
df_marzo = df[df['Mes_Nombre'] == 'Marzo']
df_abril = df[df['Mes_Nombre'] == 'Abril']

# Métricas Abril
org_abril = df_abril[df_abril['TIPO'] == 'ORG']['ORDENES'].sum()
inorg_abril = df_abril[df_abril['TIPO'] == 'INORG']['ORDENES'].sum()
spend_react_abril = df_abril['SPEND_REACTIVACION'].sum()

# Crecimiento vs Marzo (Órdenes Totales)
total_marzo = df_marzo['ORDENES'].sum()
total_abril = df_abril['ORDENES'].sum()
crecimiento = ((total_abril - total_marzo) / total_marzo * 100) if total_marzo > 0 else 0

# ==========================================
# 1) ENCABEZADO (KPIs de Abril)
# ==========================================
st.title("📊 Reporte Ejecutivo: Rendimiento Marzo vs Abril")
kpi1, kpi2, kpi3, kpi4 = st.columns(4)

kpi1.metric("🌱 Órd. Orgánicas (Abril)", f"{org_abril:,}")
kpi2.metric("💰 Órd. Inorgánicas (Abril)", f"{inorg_abril:,}")
kpi3.metric("💸 Spend Reactivación (Abril)", f"${spend_react_abril:,.0f}")
kpi4.metric("% Crecimiento vs Marzo", f"{crecimiento:.1f}%", delta=f"{crecimiento:.1f}%")

st.divider()

# ==========================================
# 2) TABLA 1: DIFERENCIACIÓN POR MESES
# ==========================================
st.subheader("📋 Tabla 1: Resumen General por Mes")
tabla1 = df.groupby('Mes_Nombre').agg({
    'ORDENES': 'sum',
    'SPEND_TOTAL': 'sum',
    'SPEND_RESTAURANTES': 'sum',
    'SPEND_REACTIVACION': 'sum'
}).reindex(['Marzo', 'Abril'])

st.table(tabla1.style.format("${:,.2f}", subset=['SPEND_TOTAL', 'SPEND_RESTAURANTES', 'SPEND_REACTIVACION']).format("{:,.0f}", subset=['ORDENES']))

# ==========================================
# 3) TABLA 2: GASTO COMBINADO (RESTAURANTES + REACTIVACIÓN)
# ==========================================
st.subheader("💵 Tabla 2: Análisis de Inversión Combinada")
# Creamos una columna de gasto operativo combinado
df['GASTO_COMBINADO'] = df['SPEND_RESTAURANTES'] + df['SPEND_REACTIVACION']
tabla2 = df.groupby('Mes_Nombre').agg({
    'SPEND_RESTAURANTES': 'sum',
    'SPEND_REACTIVACION': 'sum',
    'GASTO_COMBINADO': 'sum'
}).reindex(['Marzo', 'Abril'])

st.dataframe(tabla2.style.highlight_max(axis=0, color='#e1f5fe'), use_container_width=True)

# ==========================================
# 4) TABLA 3: ANÁLISIS POR FREQ TIER
# ==========================================
st.subheader("🎯 Tabla 3: Desempeño por Freq Tier")
tabla3 = df_abril.groupby('FREQ_TIER').agg({
    'ORDENES': 'sum',
    'SPEND_TOTAL': 'sum'
}).sort_values(by='ORDENES', ascending=False)

st.dataframe(tabla3, use_container_width=True)

st.divider()

# ==========================================
# 5) ANÁLISIS DE LO QUE SE VE (INSIGHTS)
# ==========================================
st.subheader("🧐 Análisis y Observaciones")

# Lógica básica para generar insights automáticos
gasto_marzo = df_marzo['SPEND_TOTAL'].sum()
gasto_abril = df_abril['SPEND_TOTAL'].sum()
mejor_tier = tabla3.index[0]

col_an1, col_an2 = st.columns(2)

with col_an1:
    st.info(f"""
    **Eficiencia de Órdenes:**
    * El mix de órdenes en Abril es de **{(org_abril/total_abril*100):.1f}% orgánico**. 
    * El crecimiento de órdenes del **{crecimiento:.1f}%** sugiere que la estrategia está {'funcionando' if crecimiento > 0 else 'necesitando ajustes'}.
    * La mayor concentración de pedidos se encuentra en el **{mejor_tier}**, lo que indica dónde está tu cliente más fiel.
    """)

with col_an2:
    tendencia_gasto = "aumentó" if gasto_abril > gasto_marzo else "disminuyó"
    st.warning(f"""
    **Análisis de Gasto:**
    * La inversión total **{tendencia_gasto}** de ${gasto_marzo:,.0f} en Marzo a ${gasto_abril:,.0f} en Abril.
    * El gasto combinado (Restaurantes + Reactivación) representa el **{(tabla2.loc['Abril', 'GASTO_COMBINADO'] / gasto_abril * 100):.1f}%** de la inversión de Abril.
    * El CPO (Costo por orden) de Abril se sitúa en **${(gasto_abril/total_abril):.2f}**.
    """)
