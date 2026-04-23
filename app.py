import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración de la página web
st.set_page_config(page_title="Dashboard de Órdenes", page_icon="📊", layout="wide")
st.title("📊 Dashboard de Gasto y Órdenes Orgánicas")
st.markdown("Seguimiento de desempeño e inversión publicitaria por marca.")

# 2. Cargar los datos
@st.cache_data
def load_data():
    # Carga tu archivo CSV exacto
    df = pd.read_csv('2026-04-07 10_13am.csv')
    df['MES'] = pd.to_datetime(df['MES'])
    # Filtrar solo marzo y abril
    df = df[df['MES'].dt.month.isin([3, 4])]
    df['Nombre_Mes'] = df['MES'].dt.strftime('%B') 
    return df

try:
    df = load_data()
except FileNotFoundError:
    st.error("No se encontró el archivo CSV. Asegúrate de que se llame '2026-04-07 10_13am.csv'.")
    st.stop()

# 3. BARRA LATERAL (Filtros Interactivos)
st.sidebar.header("Filtros del Dashboard")
meses_disponibles = ["Todos"] + list(df['Nombre_Mes'].unique())
mes_seleccionado = st.sidebar.selectbox("📅 Selecciona el Mes", meses_disponibles)

marcas_disponibles = ["Todas"] + list(df['BRAND_NAME'].dropna().unique())
marca_seleccionada = st.sidebar.selectbox("🍔 Selecciona la Marca", marcas_disponibles)

# Lógica para aplicar los filtros a los datos
df_filtrado = df.copy()
if mes_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['Nombre_Mes'] == mes_seleccionado]
if marca_seleccionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['BRAND_NAME'] == marca_seleccionada]

# 4. TARJETAS DE RESUMEN (KPIs)
st.markdown("### 📈 Resumen General")
col1, col2, col3 = st.columns(3)

gasto_total = df_filtrado['SPEND_TOTAL'].sum()
ordenes_organicas = df_filtrado[df_filtrado['TIPO'] == 'ORG']['ORDENES'].sum()
ordenes_totales = df_filtrado['ORDENES'].sum()

col1.metric("💸 Gasto Total", f"${gasto_total:,.2f}")
col2.metric("🌱 Órdenes Orgánicas", f"{ordenes_organicas:,}")

if ordenes_totales > 0:
    cpo = gasto_total / ordenes_totales
    col3.metric("🎯 Costo Promedio por Orden (CPO)", f"${cpo:,.2f}")
else:
    col3.metric("🎯 Costo Promedio por Orden (CPO)", "$0.00")

st.divider()

# 5. GRÁFICOS INTERACTIVOS
colA, colB = st.columns(2)

with colA:
    st.markdown("#### 🔥 Dónde estoy gastando más (Top 10)")
    gasto_marca = df_filtrado.groupby('BRAND_NAME')['SPEND_TOTAL'].sum().reset_index().sort_values(by='SPEND_TOTAL', ascending=False).head(10)
    fig_gasto = px.bar(gasto_marca, x='SPEND_TOTAL', y='BRAND_NAME', orientation='h', labels={'SPEND_TOTAL': 'Gasto Total ($)', 'BRAND_NAME': 'Marca'}, color_discrete_sequence=['#ef553b'])
    fig_gasto.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_gasto, use_container_width=True)

with colB:
    st.markdown("#### 🌿 Dónde entran más orgánicas (Top 10)")
    df_org = df_filtrado[df_filtrado['TIPO'] == 'ORG']
    org_marca = df_org.groupby('BRAND_NAME')['ORDENES'].sum().reset_index().sort_values(by='ORDENES', ascending=False).head(10)
    fig_org = px.bar(org_marca, x='ORDENES', y='BRAND_NAME', orientation='h', labels={'ORDENES': 'Órdenes', 'BRAND_NAME': 'Marca'}, color_discrete_sequence=['#00cc96'])
    fig_org.update_layout(yaxis={'categoryorder':'total ascending'})
    st.plotly_chart(fig_org, use_container_width=True)
