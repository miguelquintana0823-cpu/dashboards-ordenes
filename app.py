import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Executive Dashboard V3", page_icon="📊", layout="wide")

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

# Filtramos la base por SQUAD
df_f = df[df['SQUAD'].isin(squad_filtro)]

# Definimos las Marcas Clave solicitadas
marcas_clave_lista = [
    "Mcdonald's", "Grido", "Mostaza", "Rapanui", "Burger King", 
    "Kfc", "Mcdonald´s Turbo", "SushiPop", "Nicolo", "Dean & Dennys"
]

# KPIs de Encabezado (Abril)
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
st.title("📊 Reporte Ejecutivo: Análisis de Marcas y Tiers")
st.caption(f"Filtros: SQUADs ({', '.join(squad_filtro)})")

k1, k2, k3, k4 = st.columns(4)
k1.metric("🌱 Órd. Orgánicas (Abril)", f"{ord_org_abr:,.2f}")
k2.metric("💰 Órd. Inorgánicas (Abril)", f"{ord_inorg_abr:,.2f}")
k3.metric("💸 Spend Reactivación (Abril)", f"${spend_reac_abr:,.2f}")
k4.metric("% Crecimiento vs Marzo", f"{crecimiento:.2f}%", delta=f"{crecimiento:.2f}%")

st.divider()

# ==========================================
# 2) TABLAS DE INVERSIÓN (1 y 2)
# ==========================================
c1, c2 = st.columns(2)

with c1:
    st.subheader("📋 Tabla 1: Resumen Mensual")
    t1 = df_f.groupby('Mes_Nombre').agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum'}).reindex(['Marzo', 'Abril'])
    st.table(t1.style.format("{:,.2f}"))

with c2:
    st.subheader("💵 Tabla 2: Gasto Combinado")
    df_f['GASTO_COMBINADO'] = df_f['SPEND_RESTAURANTES'] + df_f['SPEND_REACTIVACION']
    t2 = df_f.groupby('Mes_Nombre').agg({'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum', 'GASTO_COMBINADO': 'sum'}).reindex(['Marzo', 'Abril'])
    st.dataframe(t2.style.format("{:,.2f}").background_gradient(cmap='Blues'), use_container_width=True)

# ==========================================
# 3) TABLA MARCAS CLAVE (TOP SELECTION)
# ==========================================
st.subheader("🏆 Comparativo: Marcas Clave (Marzo vs Abril)")
df_mc = df_f[df_f['BRAND_NAME'].isin(marcas_clave_lista)]
t_mc = df_mc.groupby(['BRAND_NAME', 'Mes_Nombre']).agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_REACTIVACION': 'sum', 'SPEND_RESTAURANTES': 'sum'}).sort_index()
st.dataframe(t_mc.style.format("{:,.2f}"), use_container_width=True)

# ==========================================
# 4) TABLA FINAL: MES + TIERS
# ==========================================
st.subheader("🎯 Tabla Final: Desempeño por Mes y Freq Tier")
t_final = df_f.groupby(['Mes_Nombre', 'FREQ_TIER']).agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum'}).sort_index(level=0, ascending=False)
st.dataframe(t_final.style.format("{:,.2f}"), use_container_width=True)

st.divider()

# ==========================================
# 5) ANÁLISIS DE LO QUE SE VE
# ==========================================
st.subheader("🧐 Insights y Análisis")
col_a, col_b = st.columns(2)

with col_a:
    # Análisis de Marcas Clave
    total_mc_abr = df_mc[df_mc['Mes_Nombre'] == 'Abril']['ORDENES'].sum()
    st.info(f"""
    **Análisis de Marcas Clave:**
    * Las marcas seleccionadas sumaron **{total_mc_abr:,.2f}** órdenes en Abril.
    * El gasto total invertido en este grupo durante Abril fue de **${df_mc[df_mc['Mes_Nombre'] == 'Abril']['SPEND_TOTAL'].sum():,.2f}**.
    * Esto representa un CPO promedio de **${(df_mc[df_mc['Mes_Nombre'] == 'Abril']['SPEND_TOTAL'].sum() / total_mc_abr if total_mc_abr > 0 else 0):.2f}** para el grupo élite.
    """)

with col_b:
    # Análisis de Tiers
    top_tier_abr = df_abr.groupby('FREQ_TIER')['ORDENES'].sum().idxmax()
    st.warning(f"""
    **Análisis de Tiers (Abril):**
    * El segmento con mayor volumen de pedidos es el **{top_tier_abr}**.
    * El mix orgánico total de la operación es del **{((ord_org_abr/total_abr)*100) if total_abr > 0 else 0:.2f}%**.
    * Se observa que el gasto combinado operativo en Abril (Rest + React) es de **${t2.loc['Abril', 'GASTO_COMBINADO']:,.2f}**, un valor que impacta directamente en la rentabilidad de los Tiers.
    """)
