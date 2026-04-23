import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Configuración general
st.set_page_config(page_title="Dashboard SQUADs", page_icon="🚀", layout="wide")

st.title("🚀 Dashboard de Desempeño: SQUADs y Marcas")
st.markdown("Seguimiento de Órdenes y Gastos (Marzo vs Abril)")

# 2. Carga y preparación de datos
@st.cache_data
def load_data():
    df = pd.read_csv('2026-04-07 10_13am.csv')
    df['MES'] = pd.to_datetime(df['MES'])
    # Filtrar por marzo y abril
    df = df[df['MES'].dt.month.isin([3, 4])]
    df['Mes_Nombre'] = df['MES'].dt.month_name().replace({'March': 'Marzo', 'April': 'Abril'})
    # Limpiar nombres de SQUAD si es necesario
    df['SQUAD'] = df['SQUAD'].replace({'EARLY_REACTIVATION': 'Early Reactivation', 'RESURECTION': 'Resurrection'})
    return df

try:
    df = load_data()
except:
    st.error("No se encontró el archivo '2026-04-07 10_13am.csv'.")
    st.stop()

# 3. Filtros Laterales
st.sidebar.header("Filtros Globales")
mes_filtro = st.sidebar.selectbox("📅 Mes", ["Ambos (Marzo y Abril)", "Marzo", "Abril"])

# Filtrar data general según el mes seleccionado
df_view = df.copy()
if mes_filtro != "Ambos (Marzo y Abril)":
    df_view = df_view[df_view['Mes_Nombre'] == mes_filtro]

st.markdown("---")

# ==========================================
# REQUERIMIENTO 1: Desglose por SQUAD y TIPO
# ==========================================
st.subheader("1️⃣ Desempeño por SQUAD (Orgánico vs Inorgánico)")
st.write("Resumen de órdenes y gastos desglosados por tipo de campaña.")

# Agrupar los datos solicitados
resumen_squad = df_view.groupby(['SQUAD', 'TIPO'])[['ORDENES', 'SPEND_REACTIVACION', 'SPEND_RESTAURANTES', 'SPEND_TOTAL']].sum().reset_index()

# Renombrar columnas para que se vean bonitas en la pantalla
resumen_squad.columns = ['SQUAD', 'Tipo', 'Total Órdenes', 'Spend Reactivación', 'Spend Restaurantes', 'Spend Total']

# Mostrar como tabla con formato de moneda y números enteros
st.dataframe(
    resumen_squad.style.format({
        'Total Órdenes': '{:,.0f}',
        'Spend Reactivación': '${:,.2f}',
        'Spend Restaurantes': '${:,.2f}',
        'Spend Total': '${:,.2f}'
    }), 
    use_container_width=True,
    hide_index=True
)


st.markdown("---")

# ==========================================
# REQUERIMIENTO 2: Top 10 Marcas (Marzo vs Abril)
# ==========================================
st.subheader("2️⃣ Top 10 Marcas con Más Pedidos (Evolución Marzo vs Abril)")
st.write("Comparativa mensual de las 10 marcas que generan mayor volumen de órdenes.")

# Paso A: Encontrar cuáles son el Top 10 de marcas basándonos en el total de órdenes de la vista actual
top_10_marcas = df_view.groupby('BRAND_NAME')['ORDENES'].sum().nlargest(10).index

# Paso B: Filtrar la base original (para asegurar tener ambos meses en la comparativa) solo para esas 10 marcas
df_top10 = df[df['BRAND_NAME'].isin(top_10_marcas)]

# Paso C: Agrupar por Marca y Mes para el gráfico
grafico_data = df_top10.groupby(['BRAND_NAME', 'Mes_Nombre'])['ORDENES'].sum().reset_index()

# Crear el gráfico de barras agrupadas (barmode='group')
fig_top10 = px.bar(
    grafico_data, 
    x='BRAND_NAME', 
    y='ORDENES', 
    color='Mes_Nombre', 
    barmode='group', # Esto pone la barra de marzo junto a la de abril
    labels={'BRAND_NAME': 'Marca', 'ORDENES': 'Cantidad de Órdenes', 'Mes_Nombre': 'Mes'},
    color_discrete_map={'Marzo': '#1E3A8A', 'Abril': '#10B981'}, # Azul para marzo, Verde para abril
    text_auto='.2s'
)

# Ordenar el gráfico de mayor a menor según el total de la marca
fig_top10.update_layout(xaxis={'categoryorder': 'total descending'}, plot_bgcolor='rgba(0,0,0,0)')

# Mostrar el gráfico
st.plotly_chart(fig_top10, use_container_width=True)
