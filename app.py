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
        # Limpiar nombres de columnas
        df_t.columns = [c.strip().upper() for c in df_t.columns]
        # Limpiar datos de texto
        for col in ['SQUAD', 'ZONA']:
            if col in df_t.columns:
                df_t[col] = df_t[col].astype(str).str.strip()
        return df_t
    except:
        return pd.DataFrame()

df1 = load_data_principal()
df2 = load_data_targets()

# --- FUNCIONES DE ESTILO ---
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
# PESTAÑA 1 (Sin cambios sustanciales)
# ------------------------------------------
with tab1:
    # (Mantiene la lógica que ya teníamos configurada)
    st.title("📊 Análisis de Crecimiento: Marzo vs Abril")
    # ... código de Pestaña 1 ...

# ------------------------------------------
# PESTAÑA 2: TARGETS POR ZONA (ACTUALIZADA)
# ------------------------------------------
with tab2:
    st.title("🎯 Control de Objetivos y Targets")
    
    if df2.empty:
        st.warning("⚠️ Sube 'ORDENES_TARGET_ZONAS_AR.csv' a GitHub.")
    else:
        # 1) Filtros desplegables con búsqueda (st.multiselect ya incluye buscador)
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            sel_squad = st.multiselect("🔍 Buscar y Seleccionar Squad", options=sorted(df2['SQUAD'].unique()), default=df2['SQUAD'].unique(), key="f2_squad_search")
        with col_f2:
            sel_zona = st.multiselect("🔍 Buscar y Seleccionar Zona", options=sorted(df2['ZONA'].unique()), default=df2['ZONA'].unique(), key="f2_zona_search")
        
        # Aplicar filtros
        df2_f = df2[(df2['SQUAD'].isin(sel_squad)) & (df2['ZONA'].isin(sel_zona))].copy()

        # 2) Cálculos solicitados
        # Cumplimiento = Ordenes Totales / Target Acum
        if 'ORDENES_TOTALES' in df2_f.columns and 'TARGET_ACUM' in df2_f.columns:
            df2_f['CUMPLIMIENTO'] = (df2_f['ORDENES_TOTALES'] / df2_f['TARGET_ACUM'] * 100)
        
        # Agrupar para la tabla final
        columnas_interes = ['PESO_PCT', 'ORDENES_TOTALES', 'TARGET_ACUM', 'CUMPLIMIENTO', 'PCT_VS_TARGET', 'SPEND_LOCAL', 'CPO_REACTIVACION', 'CPO_RESTAURANTES', 'CPO_TOTAL']
        # Nos aseguramos de que solo sume las que existen
        cols_presentes = [c for c in columnas_interes if c in df2_f.columns]
        tabla_final_t2 = df2_f.groupby(['ZONA', 'SQUAD'])[cols_presentes].sum()

        # 3) Formateo y Semáforo
        def estilo_targets(styler):
            # Formatos específicos
            for col in tabla_final_t2.columns:
                if any(x in col for x in ['PCT', 'CUMPLIMIENTO', 'TARGET']):
                    styler.format({col: "{:,.2f}%"}) # Agregar % sin multiplicar por 100
                if any(x in col for x in ['SPEND', 'CPO']):
                    styler.format({col: "${:,.2f}"}) # Agregar $
            
            # Semáforo de Cumplimiento
            if 'CUMPLIMIENTO' in tabla_final_t2.columns:
                def semaforo(val):
                    if val < 80: return 'background-color: #ffcccc; color: #990000' # Rojo (Crítico)
                    if val < 95: return 'background-color: #fff4cc; color: #996600' # Amarillo (En proceso)
                    return 'background-color: #ccffcc; color: #006600' # Verde (Logrado)
                
                f_map = getattr(styler, "map", getattr(styler, "applymap", None))
                if f_map: styler = f_map(semaforo, subset=['CUMPLIMIENTO'])
            
            return styler

        st.subheader("📋 Detalle de Metas por Zona")
        st.dataframe(estilo_targets(tabla_final_t2.style), use_container_width=True)

        # 4) Gráfico Comparativo
        if 'ORDENES_TOTALES' in df2_f.columns and 'TARGET_ACUM' in df2_f.columns:
            st.subheader("📊 Órdenes Reales vs Target Acumulado")
            fig_t = px.bar(
                df2_f.groupby('ZONA')[['ORDENES_TOTALES', 'TARGET_ACUM']].sum().reset_index(),
                x='ZONA', y=['ORDENES_TOTALES', 'TARGET_ACUM'],
                barmode='group',
                color_discrete_map={'ORDENES_TOTALES': '#10B981', 'TARGET_ACUM': '#94A3B8'}
            )
            st.plotly_chart(fig_t, use_container_width=True)
