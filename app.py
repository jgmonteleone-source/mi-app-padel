import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        # Cargamos los datos de las dos pestañas
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        
        # Convertimos la columna Fecha a formato fecha real de Python
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        
        # Limpiamos nombres y fotos de espacios invisibles
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        jugadores['Foto'] = jugadores['Foto'].astype(str).str.strip()
        
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error al conectar con la base de datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- LÓGICA DE FILTROS TEMPORALES ---
st.sidebar.title("🏸 Padel Pro v2")
rango = st.sidebar.selectbox("Periodo del Ranking", ["Siempre", "Este año", "Año pasado", "Este mes"])

def filtrar_por_fecha(df, opcion):
    hoy = datetime.now()
    if df.empty: return df
    if opcion == "Este año":
        return df[df['Fecha'].dt.year == hoy.year]
    elif opcion == "Año pasado":
        return df[df['Fecha'].dt.year == hoy.year - 1]
    elif opcion == "Este mes":
        return df[(df['Fecha'].dt.year == hoy.year) & (df['Fecha'].dt.month == hoy.month)]
    return df

df_partidos_filt = filtrar_por_fecha(df_partidos, rango)

# --- MENÚ PRINCIPAL ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (Cara a Cara)", "📝 Cargar Partido", "👤 Gestionar Jugadores"])

# --- 1. SECCIÓN RANKING ---
if menu == "🏆 Ranking":
    st.title(f"🏆 Ranking - {rango}")
    
    if not df_jugadores.empty:
        # Ordenamos por puntos (asegurando que sean números)
        df_jugadores["Puntos"] = pd.to_numeric(df_jugadores["Puntos"], errors='coerce').fillna(0)
        df_rank =
