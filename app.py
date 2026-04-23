import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Configuración de página
st.set_page_config(page_title="Dashboard Operativo", page_icon="📊", layout="wide")

# 2. CARGA DE DATOS
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
        df_t = pd.read_csv('ORDENES_TARGET_ZONAS_AR.csv') 
        df_t.columns = [c.strip().upper() for c in df_t.columns]
        
        # Limpieza de caracteres especiales para cálculos ($ y %)
        for col in df_t.columns:
            if col not in ['SQUAD', 'ZONA', 'BRAND_NAME']:
                if df_t[col].dtype == object:
                    df_t[col] = df_t[col].astype(str).str.replace(r'[\$,%]', '', regex=True)
                    df_t[col] = pd.to_numeric(df_t[col], errors='coerce')
        
        for col in ['SQUAD', 'ZONA']:
            if col in df_t.columns:
                df_t[col] = df_t[col].astype(str).str.strip()
        return df_t
    except:
        return pd.DataFrame()

df1 = load_data_principal()
df2 = load_data_targets()

# --- FUNCIONES DE ESTILO PESTAÑA 1 ---
def aplicar_estilos_p1(tabla_df):
    formatos = {col: "{:,.2f}%" if "Var %" in str(col) else "{:,.2f}" for col in tabla_df.columns}
    styler = tabla_df.style.format(formatos)
    def color_variacion(val):
        if isinstance(val, (int, float)):
            return 'color: #d32f2f' if val < 0 else 'color: #388e3c' if val > 0 else ''
        return ''
    f_map = getattr(styler, "map", getattr(styler, "applymap", None))
    if f_map: styler = f_map(color_variacion, subset=[c for c in tabla_df.columns if "Var %" in str(c)])
    return styler

# ==========================================
# ESTRUCTURA DE PESTAÑAS
# ==========================================
tab1, tab2 = st.tabs(["📉 Desempeño Marzo-Abril", "🎯 Targets por Zona"])

# ------------------------------------------
# PESTAÑA 1: MARZO - ABRIL
# ------------------------------------------
with tab1:
    st.title("📊 Análisis de Crecimiento: Marzo vs Abril")
    squad_f1 = st.multiselect("Filtrar Squad (Pestaña 1)", options=df1['SQUAD'].unique(), default=df1['SQUAD'].unique(), key="f1")
    df1_f = df1[df1['SQUAD'].isin(squad_f1)]
    
    df_abr = df1_f[df1_f['Mes_Nombre'] == 'Abril']
    df_mar = df1_f[df1_f['Mes_Nombre'] == 'Marzo']

    total_mar = df_mar['ORDENES'].sum() if not df_mar.empty else 0
    total_abr = df_abr['ORDENES'].sum() if not df_abr.empty else 0
    crecimiento = ((total_abr - total_mar) / total_mar * 100) if total_mar > 0 else 0

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("🌱 Órd. Orgánicas (Abril)", f"{df_abr[df_abr['TIPO'] == 'ORG']['ORDENES'].sum():,.0f}")
    k2.metric("💰 Órd. Inorgánicas (Abril)", f"{df_abr[df_abr['TIPO'] == 'INORG']['ORDENES'].sum():,.0f}")
    k3.metric("💸 Spend Reactivación (Abril)", f"${df_abr['SPEND_REACTIVACION'].sum():,.2f}")
    k4.metric("% Crecimiento Total", f"{crecimiento:.2f}%", delta=f"{crecimiento:.2f}%")

    st.divider()
    st.subheader("📋 Tabla 1: Totales por Mes")
    t1 = df1_f.groupby('Mes_Nombre').agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum'}).reindex(['Marzo', 'Abril']).fillna(0)
    st.table(t1.style.format("{:,.2f}"))

    def crear_t(df_i, idx):
        res = df_i.groupby([idx, 'Mes_Nombre']).agg({'ORDENES': 'sum', 'SPEND_TOTAL': 'sum', 'SPEND_RESTAURANTES': 'sum', 'SPEND_REACTIVACION': 'sum'}).unstack(fill_value=0)
        if 'Marzo' in res.columns.levels[1] and 'Abril' in res.columns.levels[1]:
            for m in ['ORDENES', 'SPEND_TOTAL', 'SPEND_RESTAURANTES', 'SPEND_REACTIVACION']:
                res[(m, 'Var %')] = ((res[(m, 'Abril')] - res[(m, 'Marzo')]) / res[(m, 'Marzo')] * 100).replace([np.inf, -np.inf], 0).fillna(0)
            cols = []
            for m in ['ORDENES', 'SPEND_TOTAL', 'SPEND_RESTAURANTES', 'SPEND_REACTIVACION']:
                cols.extend([(m, 'Marzo'), (m, 'Abril'), (m, 'Var %')])
            res = res[cols]
        return res

    st.subheader("🎯 Tabla 2: Desempeño por Freq Tier")
    st.dataframe(aplicar_estilos_p1(crear_t(df1_f, 'FREQ_TIER')), use_container_width=True)
    st.subheader("🏆 Tabla 3: Marcas Clave")
    marcas_clave_lista = ["Mcdonald's", "Grido", "Mostaza", "Rapanui", "Burger King", "Kfc", "Mcdonald´s Turbo", "SushiPop", "Nicolo", "Dean & Dennys"]
    df_mc = df1_f[df1_f['BRAND_NAME'].isin(marcas_clave_lista)]
    st.dataframe(aplicar_estilos_p1(crear_t(df_mc, 'BRAND_NAME')), use_container_width=True)

# ------------------------------------------
# PESTAÑA 2: TARGETS POR ZONA (CON CONVERSIÓN)
# ------------------------------------------
with tab2:
    st.title("🎯 Control de Objetivos y Conversión por Zona")
    
    if df2.empty:
        st.warning("⚠️ Asegúrate de haber subido 'ORDENES_TARGET_ZONAS_AR.csv'.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            sel_squad = st.multiselect("🔍 Buscar Squad", options=sorted(df2['SQUAD'].dropna().unique()), default=df2['SQUAD'].dropna().unique(), key="f2_sq")
        with col_f2:
            sel_zona = st.multiselect("🔍 Buscar Zona", options=sorted(df2['ZONA'].dropna().unique()), default=df2['ZONA'].dropna().unique(), key="f2_zn")
        
        df2_f = df2[(df2['SQUAD'].isin(sel_squad)) & (df2['ZONA'].isin(sel_zona))].copy()

        # Agrupamos las métricas
        cols_numericas = df2_f.select_dtypes(include=[np.number]).columns.tolist()
        tabla_final_t2 = df2_f.groupby(['ZONA', 'SQUAD'])[cols_numericas].sum()

        # 1. Cálculo de CUMPLIMIENTO (Órdenes vs Target)
        if 'ORDENES_TOTALES' in tabla_final_t2.columns and 'TARGET_ACUM' in tabla_final_t2.columns:
            tabla_final_t2['CUMPLIMIENTO'] = (tabla_final_t2['ORDENES_TOTALES'] / tabla_final_t2['TARGET_ACUM'].replace(0, np.nan)) * 100

        # 2. Cálculo de CONVERSIÓN (Órdenes vs Base Usuarios)
        if 'ORDENES_TOTALES' in tabla_final_t2.columns and 'BASE_USUARIOS' in tabla_final_t2.columns:
            tabla_final_t2['CONVERSION'] = (tabla_final_t2['ORDENES_TOTALES'] / tabla_final_t2['BASE_USUARIOS'].replace(0, np.nan)) * 100

        # Columnas a mostrar (incluimos BASE_USUARIOS y CONVERSION)
        columnas_deseadas = ['PESO_PCT', 'BASE_USUARIOS', 'ORDENES_TOTALES', 'TARGET_ACUM', 'CUMPLIMIENTO', 'CONVERSION', 'SPEND_LOCAL', 'CPO_REACTIVACION', 'CPO_RESTAURANTES', 'CPO_INORGANICO']
        cols_finales = [c for c in columnas_deseadas if c in tabla_final_t2.columns]
        tabla_final_t2 = tabla_final_t2[cols_finales]

        def estilo_targets_pro(tabla):
            formatos = {}
            for col in tabla.columns:
                if any(x in col for x in ['PCT', 'CUMPLIMIENTO', 'CONVERSION']):
                    formatos[col] = "{:,.2f}%"
                elif any(x in col for x in ['SPEND', 'CPO']):
                    formatos[col] = "${:,.2f}"
                elif any(x in col for x in ['BASE_USUARIOS', 'ORDENES_TOTALES', 'TARGET_ACUM']):
                    formatos[col] = "{:,.0f}"
                else:
                    formatos[col] = "{:,.2f}"
            return tabla.style.format(formatos)

        st.subheader("📋 Detalle de Metas y Conversión por Zona")
        st.dataframe(estilo_targets_pro(tabla_final_t2), use_container_width=True)

        # Gráfico complementario de Conversión
        if 'CONVERSION' in tabla_final_t2.columns:
            st.subheader("📊 Ranking de Conversión por Zona (%)")
            conv_zona = tabla_final_t2.groupby('ZONA')['CONVERSION'].mean().reset_index().sort_values('CONVERSION', ascending=False)
            fig_conv = px.bar(conv_zona, x='ZONA', y='CONVERSION', text_auto='.2f', color_discrete_sequence=['#636EFA'])
            st.plotly_chart(fig_conv, use_container_width=True)
