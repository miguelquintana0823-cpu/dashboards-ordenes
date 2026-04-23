import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Dashboard Integral de Operaciones", page_icon="📊", layout="wide")

# 2. CARGA DE DATOS (DOS FUENTES)
@st.cache_data
def load_data_principal():
    df = pd.read_csv('2026-04-07 10_13am.csv')
    df['MES'] = pd.to_datetime(df['MES'])
    df = df[df['MES'].dt.month.isin([3, 4])].copy()
    df['Mes_Nombre'] = df['MES'].dt.month_name().replace({'March': 'Marzo', 'April': 'Abril'})
    df['SQUAD'] = df['SQUAD'].astype(str).str.replace('_', ' ').str.title()
    df['BRAND_NAME'] = df['BRAND_NAME'].astype(str).str.strip()
    return df

@st.cache_data
def load_data_targets():
    try:
        # AQUI CONECTAMOS TU NUEVO ARCHIVO
        df_t = pd.read_csv('ORDENES_TARGET_ZONAS_AR.csv') 
        df_t.columns = [c.strip().upper() for c in df_t.columns]
        return df_t
    except:
        return pd.DataFrame()

df1 = load_data_principal()
df2 = load_data_targets()

# --- FUNCIONES DE FORMATEO ---
def aplicar_estilos(tabla_df):
    formatos = {col: "{:,.2f}%" if "Var %" in str(col) or "Cumplimiento" in str(col) else "{:,.2f}" for col in tabla_df.columns}
    styler = tabla_df.style.format(formatos)
    def color_variacion(val):
        if isinstance(val, (int, float)):
            return 'color: #d32f2f' if val < 0 else 'color: #388e3c' if val > 0 else ''
        return ''
    
    f_map = getattr(styler, "map", getattr(styler, "applymap", None))
    cols_var = [c for c in tabla_df.columns if "Var %" in str(c) or "Cumplimiento" in str(c)]
    if cols_var and f_map:
        styler = f_map(color_variacion, subset=cols_var)
    return styler

def crear_tabla_con_crecimiento(df_input, index_col):
    resumen = df_input.groupby([index_col, 'Mes_Nombre']).agg({
        'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum'
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

# ==========================================
# ESTRUCTURA DE PESTAÑAS
# ==========================================
tab1, tab2 = st.tabs(["📉 Desempeño Marzo-Abril", "🎯 Targets por Zona"])

# ------------------------------------------
# PESTAÑA 1: LÓGICA ORIGINAL (MARZO-ABRIL)
# ------------------------------------------
with tab1:
    squad_f1 = st.multiselect("Filtrar Squad (Pestaña 1)", options=df1['SQUAD'].unique(), default=df1['SQUAD'].unique(), key="f1")
    df1_f = df1[df1['SQUAD'].isin(squad_f1)]
    
    df_abr = df1_f[df1_f['Mes_Nombre'] == 'Abril']
    df_mar = df1_f[df1_f['Mes_Nombre'] == 'Marzo']

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

    st.subheader("📋 Tabla 1: Totales por Mes")
    t1 = df1_f.groupby('Mes_Nombre').agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum'}).reindex(['Marzo', 'Abril']).fillna(0)
    st.table(t1.style.format("{:,.2f}"))

    st.subheader("🎯 Tabla 2: Desempeño por Freq Tier")
    t_tier = crear_tabla_con_crecimiento(df1_f, 'FREQ_TIER')
    st.dataframe(aplicar_estilos(t_tier), use_container_width=True)

    st.divider()

    st.subheader("🏆 Tabla 3: Marcas Clave")
    marcas_clave_lista = ["Mcdonald's", "Grido", "Mostaza", "Rapanui", "Burger King", "Kfc", "Mcdonald´s Turbo", "SushiPop", "Nicolo", "Dean & Dennys"]
    df_mc = df1_f[df1_f['BRAND_NAME'].isin(marcas_clave_lista)]
    t_mc = crear_tabla_con_crecimiento(df_mc, 'BRAND_NAME')
    st.dataframe(aplicar_estilos(t_mc), use_container_width=True)

# ------------------------------------------
# PESTAÑA 2: NUEVA DATA DE TARGETS
# ------------------------------------------
with tab2:
    st.title("🎯 Control de Objetivos por Zona")
    
    if df2.empty:
        st.warning("⚠️ No se pudo leer la data. Asegúrate de haber subido 'ORDENES_TARGET_ZONAS_AR.csv' a tu repositorio de GitHub.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            squad_list = df2['SQUAD'].unique() if 'SQUAD' in df2.columns else []
            sel_squad = st.multiselect("Seleccionar Squad", options=squad_list, default=squad_list, key="f2_squad")
        with col_f2:
            zona_list = df2['ZONA'].unique() if 'ZONA' in df2.columns else []
            sel_zona = st.multiselect("Seleccionar Zona", options=zona_list, default=zona_list, key="f2_zona")
        
        df2_f = df2.copy()
        if sel_squad and 'SQUAD' in df2_f.columns: df2_f = df2_f[df2_f['SQUAD'].isin(sel_squad)]
        if sel_zona and 'ZONA' in df2_f.columns: df2_f = df2_f[df2_f['ZONA'].isin(sel_zona)]

        # Ajusta "TARGET" y "ORDENES" a los nombres reales de las columnas en tu CSV si es necesario
        col_ordenes = 'ORDENES' if 'ORDENES' in df2_f.columns else None
        col_target = 'TARGET' if 'TARGET' in df2_f.columns else None

        if col_ordenes and col_target:
            total_real = df2_f[col_ordenes].sum()
            total_target = df2_f[col_target].sum()
            cumplimiento = (total_real / total_target * 100) if total_target > 0 else 0
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Órdenes Reales", f"{total_real:,.0f}")
            m2.metric("Target Objetivo", f"{total_target:,.0f}")
            m3.metric("% Cumplimiento", f"{cumplimiento:.2f}%", delta=f"{cumplimiento-100:.2f}% vs Target")

            st.divider()

            st.subheader("📋 Detalle de Ejecución por Zona")
            tabla_target = df2_f.groupby(['ZONA', 'SQUAD']).sum(numeric_only=True)
            tabla_target['% Cumplimiento'] = (tabla_target[col_ordenes] / tabla_target[col_target] * 100)
            
            st.dataframe(aplicar_estilos(tabla_target), use_container_width=True)

            st.subheader("📊 Real vs Target por Zona")
            fig_target = px.bar(
                df2_f.groupby('ZONA').sum(numeric_only=True).reset_index(),
                x='ZONA', y=[col_ordenes, col_target],
                barmode='group',
                title="Comparativa Órdenes vs Objetivo",
                color_discrete_map={col_ordenes: '#10B981', col_target: '#CBD5E1'}
            )
            st.plotly_chart(fig_target, use_container_width=True)
        else:
            st.info("Mostrando datos brutos. Para calcular el % de cumplimiento, asegúrate de que tu archivo tenga columnas llamadas 'ORDENES' y 'TARGET'.")
            st.dataframe(df2_f, use_container_width=True)
