import streamlit as st
import pandas as pd

# 1. Configuración de página
st.set_page_config(page_title="Executive Dashboard V5", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #fcfcfc; }
    .stDataFrame td, .stDataFrame th { text-align: center !important; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga de datos
@st.cache_data
def load_data():
    df = pd.read_csv('2026-04-07 10_13am.csv')
    df['MES'] = pd.to_datetime(df['MES'])
    # Filtrar solo Marzo y Abril
    df = df[df['MES'].dt.month.isin([3, 4])].copy()
    df['Mes_Nombre'] = df['MES'].dt.month_name().replace({'March': 'Marzo', 'April': 'Abril'})
    df['SQUAD'] = df['SQUAD'].str.replace('_', ' ').str.title()
    df['BRAND_NAME'] = df['BRAND_NAME'].astype(str).str.strip()
    return df

df = load_data()

# --- BARRA LATERAL (FILTROS) ---
st.sidebar.header("🎯 Filtros de Control")
squad_filtro = st.sidebar.multiselect("👥 Seleccionar SQUAD", options=df['SQUAD'].unique(), default=df['SQUAD'].unique())

# Filtramos la base por SQUAD
df_f = df[df['SQUAD'].isin(squad_filtro)]

# Definición de Marcas Clave
marcas_clave_lista = [
    "Mcdonald's", "Grido", "Mostaza", "Rapanui", "Burger King", 
    "Kfc", "Mcdonald´s Turbo", "SushiPop", "Nicolo", "Dean & Dennys"
]

# --- FUNCION PARA CREAR TABLAS COMPARATIVAS LADO A LADO ---
def crear_tabla_comparativa(df_input, index_col):
    # Agrupar por el indice deseado y el mes
    resumen = df_input.groupby([index_col, 'Mes_Nombre']).agg({
        'ORDENES': 'sum',
        'SPEND_TOTAL': 'sum',
        'SPEND_RESTAURANTES': 'sum',
        'SPEND_REACTIVACION': 'sum'
    }).unstack(fill_value=0)
    
    # Reordenar niveles para que Marzo aparezca primero que Abril
    resumen = resumen.reorder_levels([1, 0], axis=1)
    
    # Seleccionar y ordenar columnas para que queden juntas (Ej: Ordenes Marzo | Ordenes Abril)
    cols_ordenadas = []
    metricas = ['ORDENES', 'SPEND_TOTAL', 'SPEND_RESTAURANTES', 'SPEND_REACTIVACION']
    for m in metricas:
        if 'Marzo' in resumen.columns.levels[0]: cols_ordenadas.append(('Marzo', m))
        if 'Abril' in resumen.columns.levels[0]: cols_ordenadas.append(('Abril', m))
    
    resumen = resumen[cols_ordenadas]
    return resumen

# ==========================================
# 1) ENCABEZADO (KPIs DE ABRIL)
# ==========================================
df_abr = df_f[df_f['Mes_Nombre'] == 'Abril']
df_mar = df_f[df_f['Mes_Nombre'] == 'Marzo']

ord_org_abr = df_abr[df_abr['TIPO'] == 'ORG']['ORDENES'].sum()
ord_inorg_abr = df_abr[df_abr['TIPO'] == 'INORG']['ORDENES'].sum()
spend_reac_abr = df_abr['SPEND_REACTIVACION'].sum()
total_mar = df_mar['ORDENES'].sum()
total_abr = df_abr['ORDENES'].sum()
crecimiento = ((total_abr - total_mar) / total_mar * 100) if total_mar > 0 else 0

st.title("📊 Reporte Ejecutivo: Comparativa Horizontal")
k1, k2, k3, k4 = st.columns(4)
k1.metric("🌱 Órd. Orgánicas (Abril)", f"{ord_org_abr:,.2f}")
k2.metric("💰 Órd. Inorgánicas (Abril)", f"{ord_inorg_abr:,.2f}")
k3.metric("💸 Spend Reactivación (Abril)", f"${spend_reac_abr:,.2f}")
k4.metric("% Crecimiento vs Marzo", f"{crecimiento:.2f}%", delta=f"{crecimiento:.2f}%")

st.divider()

# ==========================================
# 2) TABLA 1: RESUMEN MENSUAL (General)
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
# 3) TABLA DE DESEMPEÑO POR FREQ TIER (DEBAJO DE T1)
# ==========================================
st.subheader("🎯 Tabla 2: Desempeño por Freq Tier (Comparativa Lado a Lado)")
t_tier_comp = crear_tabla_comparativa(df_f, 'FREQ_TIER')
st.dataframe(t_tier_comp.style.format("{:,.2f}"), use_container_width=True)

st.divider()

# ==========================================
# 4) TABLA MARCAS CLAVE (HORIZONTAL)
# ==========================================
st.subheader("🏆 Tabla 3: Marcas Clave - Marzo vs Abril")
df_mc = df_f[df_f['BRAND_NAME'].isin(marcas_clave_lista)]
t_mc_comp = crear_tabla_comparativa(df_mc, 'BRAND_NAME')
st.dataframe(t_mc_comp.style.format("{:,.2f}"), use_container_width=True)

st.divider()

# ==========================================
# 5) ANÁLISIS DE DATOS
# ==========================================
st.subheader("🧐 Insights del Periodo")
col_a, col_b = st.columns(2)

with col_a:
    gasto_mc_abr = df_mc[df_mc['Mes_Nombre'] == 'Abril']['SPEND_TOTAL'].sum()
    total_mc_abr = df_mc[df_mc['Mes_Nombre'] == 'Abril']['ORDENES'].sum()
    st.info(f"""
    **Análisis de Marcas Clave (Abril):**
    * Volumen de órdenes: **{total_mc_abr:,.2f}**.
    * Inversión Total: **${gasto_mc_abr:,.2f}**.
    * CPO Promedio: **${(gasto_mc_abr/total_mc_abr if total_mc_abr > 0 else 0):.2f}**.
    """)

with col_b:
    st.warning(f"""
    **Análisis Global:**
    * El mix orgánico de Abril es del **{((ord_org_abr/total_abr)*100) if total_abr > 0 else 0:.2f}%**.
    * El crecimiento de órdenes totales Marzo ➔ Abril fue del **{crecimiento:.2f}%**.
    * Revisa la **Tabla 2** para identificar si el crecimiento viene de usuarios nuevos o frecuentes.
    """)
