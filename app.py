import streamlit as st
import pandas as pd
import numpy as np

# 1. Configuración de página
st.set_page_config(page_title="Executive Dashboard", page_icon="📊", layout="wide")
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .main { background-color: #fcfcfc; }
    .stDataFrame td, .stDataFrame th { text-align: center !important; font-size: 13px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Carga de datos
@st.cache_data
def load_data():
    df = pd.read_csv('2026-04-07 10_13am.csv')
    df['MES'] = pd.to_datetime(df['MES'])
    df = df[df['MES'].dt.month.isin([3, 4])].copy()
    df['Mes_Nombre'] = df['MES'].dt.month_name().replace({'March': 'Marzo', 'April': 'Abril'})
    df['SQUAD'] = df['SQUAD'].astype(str).str.replace('_', ' ').str.title()
    df['BRAND_NAME'] = df['BRAND_NAME'].astype(str).str.strip()
    return df

df = load_data()

# --- BARRA LATERAL ---
st.sidebar.header("🎯 Filtros de Control")
squads_disponibles = df['SQUAD'].unique()
squad_filtro = st.sidebar.multiselect("👥 Seleccionar SQUAD", options=squads_disponibles, default=squads_disponibles)
df_f = df[df['SQUAD'].isin(squad_filtro)]

marcas_clave_lista = ["Mcdonald's", "Grido", "Mostaza", "Rapanui", "Burger King", "Kfc", "Mcdonald´s Turbo", "SushiPop", "Nicolo", "Dean & Dennys"]

# --- FUNCIÓN: COMPARATIVA + VARIACIÓN ---
def crear_tabla_con_crecimiento(df_input, index_col):
    resumen = df_input.groupby([index_col, 'Mes_Nombre']).agg({
        'ORDENES': 'sum',
        'SPEND_TOTAL': 'sum',
        'SPEND_RESTAURANTES': 'sum',
        'SPEND_REACTIVACION': 'sum'
    }).unstack(fill_value=0)
    
    if 'Marzo' in resumen.columns.levels[1] and 'Abril' in resumen.columns.levels[1]:
        metricas = ['ORDENES', 'SPEND_TOTAL', 'SPEND_RESTAURANTES', 'SPEND_REACTIVACION']
        for m in metricas:
            marzo_val = resumen[(m, 'Marzo')]
            abril_val = resumen[(m, 'Abril')]
            resumen[(m, 'Var %')] = ((abril_val - marzo_val) / marzo_val * 100).replace([np.inf, -np.inf], 0).fillna(0)
            
        cols_finales = []
        for m in metricas:
            cols_finales.extend([(m, 'Marzo'), (m, 'Abril'), (m, 'Var %')])
        resumen = resumen[cols_finales]
    return resumen

# --- FUNCIÓN DE ESTILO (LIMPIA SIN FONDO) ---
def aplicar_estilos(tabla_df):
    # Formatear: añadir "%" a la variación y "$ o normal" al resto
    formatos = {}
    cols_var = []
    for col in tabla_df.columns:
        if 'Var %' in col[1]:
            formatos[col] = "{:,.2f}%"
            cols_var.append(col)
        else:
            formatos[col] = "{:,.2f}"
            
    styler = tabla_df.style.format(formatos)
    
    # Colorear solo el texto (Rojo si cae, Verde si sube)
    def color_texto(val):
        if isinstance(val, (int, float)):
            if val < 0: return 'color: #d32f2f' # Rojo
            elif val > 0: return 'color: #388e3c' # Verde
        return ''

    # Compatibilidad Streamlit
    funcion_map = getattr(styler, "map", getattr(styler, "applymap", None))
    
    if cols_var and funcion_map:
        styler = funcion_map(color_texto, subset=cols_var)
            
    return styler

# ==========================================
# 1) ENCABEZADO
# ==========================================
df_abr = df_f[df_f['Mes_Nombre'] == 'Abril']
df_mar = df_f[df_f['Mes_Nombre'] == 'Marzo']

total_mar = df_mar['ORDENES'].sum() if not df_mar.empty else 0
total_abr = df_abr['ORDENES'].sum() if not df_abr.empty else 0
crecimiento = ((total_abr - total_mar) / total_mar * 100) if total_mar > 0 else 0

st.title("📊 Análisis de Crecimiento: Marzo vs Abril")
k1, k2, k3, k4 = st.columns(4)
k1.metric("🌱 Órd. Orgánicas (Abril)", f"{df_abr[df_abr['TIPO'] == 'ORG']['ORDENES'].sum():,.0f}")
k2.metric("💰 Órd. Inorgánicas (Abril)", f"{df_abr[df_abr['TIPO'] == 'INORG']['ORDENES'].sum():,.0f}")
k3.metric("💸 Spend Reactivación (Abril)", f"${df_abr['SPEND_REACTIVACION'].sum():,.2f}")
k4.metric("% Crecimiento Total", f"{crecimiento:.2f}%", delta=f"{crecimiento:.2f}%")

st.divider()

# ==========================================
# 2) TABLA 1: RESUMEN MENSUAL
# ==========================================
st.subheader("📋 Tabla 1: Totales por Mes")
t1 = df_f.groupby('Mes_Nombre').agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum'}).reindex(['Marzo', 'Abril']).fillna(0)
st.table(t1.style.format("{:,.2f}"))

# ==========================================
# 3) TABLA DE FREQ TIER CON CRECIMIENTO
# ==========================================
st.subheader("🎯 Tabla 2: Desempeño por Freq Tier con Variación %")
t_tier = crear_tabla_con_crecimiento(df_f, 'FREQ_TIER')
st.dataframe(aplicar_estilos(t_tier), use_container_width=True)

st.divider()

# ==========================================
# 4) TABLA MARCAS CLAVE CON CRECIMIENTO
# ==========================================
st.subheader("🏆 Tabla 3: Marcas Clave - Comparativa de Crecimiento")
df_mc = df_f[df_f['BRAND_NAME'].isin(marcas_clave_lista)]
t_mc = crear_tabla_con_crecimiento(df_mc, 'BRAND_NAME')
st.dataframe(aplicar_estilos(t_mc), use_container_width=True)

st.divider()

# ==========================================
# 5) ANÁLISIS DINÁMICO
# ==========================================
st.subheader("🧐 Insights del Análisis")
col_a, col_b = st.columns(2)

with col_a:
    st.info("""
    **Interpretación de Variación:**
    * Las columnas de **Var %** muestran el cambio directo de Abril respecto a Marzo.
    * Los valores en **verde** indican crecimiento positivo en volumen o gasto.
    * Los valores en **rojo** indican una caída en la métrica.
    """)

with col_b:
    try:
        max_crec_marca = t_mc.xs('Var %', level=1, axis=1)['ORDENES'].idxmax()
        val_crec_marca = t_mc.xs('Var %', level=1, axis=1)['ORDENES'].max()
        st.warning(f"""
        **Dato Destacado:**
        * La marca con mayor crecimiento porcentual en órdenes es **{max_crec_marca}** con un **{val_crec_marca:.2f}%**.
        * Revisa si el gasto (Spend Total) creció en la misma proporción para evaluar la eficiencia.
        """)
    except:
        st.warning("Selecciona SQUADs con datos en ambos meses para visualizar el ganador en crecimiento.")
