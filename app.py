import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Executive Dashboard V4", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #fcfcfc; }
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
    
    # LIMPIEZA CLAVE: Quitar espacios invisibles al principio o final de la marca
    df['BRAND_NAME'] = df['BRAND_NAME'].astype(str).str.strip()
    
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🎯 Filtros de Control")
squad_filtro = st.sidebar.multiselect("👥 Seleccionar SQUAD", options=df['SQUAD'].unique(), default=df['SQUAD'].unique())

# Filtramos la base por SQUAD
df_f = df[df['SQUAD'].isin(squad_filtro)]

# Definimos las Marcas Clave solicitadas (con el nombre exacto limpio)
marcas_clave_lista = [
    "Mcdonald's", "Grido", "Mostaza", "Rapanui", "Burger King", 
    "Kfc", "Mcdonald´s Turbo", "SushiPop", "Nicolo", "Dean & Dennys"
]

# KPIs de Encabezado (Abril vs Marzo)
df_abr = df_f[df_f['Mes_Nombre'] == 'Abril']
df_mar = df_f[df_f['Mes_Nombre'] == 'Marzo']

ord_org_abr = df_abr[df_abr['TIPO'] == 'ORG']['ORDENES'].sum()
ord_inorg_abr = df_abr[df_abr['TIPO'] == 'INORG']['ORDENES'].sum()
spend_reac_abr = df_abr['SPEND_REACTIVACION'].sum()
total_mar = df_mar['ORDENES'].sum()
total_abr = df_abr['ORDENES'].sum()
crecimiento = ((total_abr - total_mar) / total_mar * 100) if total_mar > 0 else 0

# ==========================================
# 1) ENCABEZADO
# ==========================================
st.title("📊 Reporte Ejecutivo: Análisis Mensual")
st.caption(f"Filtros: SQUADs ({', '.join(squad_filtro)})")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🌱 Órd. Orgánicas (Abril)", f"{ord_org_abr:,.2f}")
k2.metric("💰 Órd. Inorgánicas (Abril)", f"{ord_inorg_abr:,.2f}")
k3.metric("💸 Spend Reactivación (Abril)", f"${spend_reac_abr:,.2f}")
k4.metric("% Crecimiento vs Marzo", f"{crecimiento:.2f}%", delta=f"{crecimiento:.2f}%")

st.divider()

# ==========================================
# 2) TABLA 1: RESUMEN MENSUAL
# ==========================================
st.subheader("📋 Tabla 1: Resumen General por Mes")
t1 = df_f.groupby('Mes_Nombre').agg({
    'ORDENES': 'sum', 
    'SPEND_TOTAL': 'sum', 
    'SPEND_RESTAURANTES': 'sum', 
    'SPEND_REACTIVACION': 'sum'
}).reindex(['Marzo', 'Abril'])
st.table(t1.style.format("{:,.2f}"))

# ==========================================
# 3) TABLA MARCAS CLAVE (TOP SELECTION)
# ==========================================
st.subheader("🏆 Comparativo: Marcas Clave (Marzo vs Abril)")
st.write("Análisis exclusivo de las 10 marcas principales definidas para seguimiento.")

df_mc = df_f[df_f['BRAND_NAME'].isin(marcas_clave_lista)]
t_mc = df_mc.groupby(['BRAND_NAME', 'Mes_Nombre']).agg({
    'ORDENES': 'sum', 
    'SPEND_REACTIVACION': 'sum', 
    'SPEND_RESTAURANTES': 'sum',
    'SPEND_TOTAL': 'sum'
}).sort_index()

st.dataframe(t_mc.style.format("{:,.2f}"), use_container_width=True)

# ==========================================
# 4) TABLA FINAL: MES + TIERS
# ==========================================
st.subheader("🎯 Tabla de Desempeño por Freq Tier")
st.write("Desglose del rendimiento y gasto según la frecuencia de usuarios en ambos meses.")

t_final = df_f.groupby(['Mes_Nombre', 'FREQ_TIER']).agg({
    'ORDENES': 'sum', 
    'SPEND_TOTAL': 'sum', 
    'SPEND_RESTAURANTES': 'sum', 
    'SPEND_REACTIVACION': 'sum'
}).sort_index(level=[0, 1], ascending=[False, True])

st.dataframe(t_final.style.format("{:,.2f}"), use_container_width=True)

st.divider()

# ==========================================
# 5) ANÁLISIS DE LO QUE SE VE
# ==========================================
st.subheader("🧐 Insights y Análisis")
col_a, col_b = st.columns(2)

with col_a:
    total_mc_abr = df_mc[df_mc['Mes_Nombre'] == 'Abril']['ORDENES'].sum()
    gasto_mc_abr = df_mc[df_mc['Mes_Nombre'] == 'Abril']['SPEND_TOTAL'].sum()
    cpo_mc = (gasto_mc_abr / total_mc_abr) if total_mc_abr > 0 else 0
    
    st.info(f"""
    **Foco en Marcas Clave:**
    * Las marcas seleccionadas en el Top 10 sumaron **{total_mc_abr:,.2f}** órdenes en Abril.
    * La inversión publicitaria en este grupo durante Abril fue de **${gasto_mc_abr:,.2f}**.
    * Esto nos da un CPO promedio de **${cpo_mc:.2f}** exclusivo para estas cuentas clave.
    """)

with col_b:
    if not df_abr.empty:
        top_tier_abr = df_abr.groupby('FREQ_TIER')['ORDENES'].sum().idxmax()
    else:
        top_tier_abr = "N/A"
        
    st.warning(f"""
    **Análisis Global (Abril):**
    * El segmento poblacional con mayor volumen de pedidos sigue siendo el **{top_tier_abr}**.
    * Del total de órdenes generadas en Abril, el **{((ord_org_abr/total_abr)*100) if total_abr > 0 else 0:.2f}%** ingresaron por canales orgánicos.
    * El crecimiento general mes a mes muestra una variación del **{crecimiento:.2f}%** en órdenes frente a Marzo.
    """)
