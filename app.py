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
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        # Convertir fecha a objeto datetime para filtrar
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- LÓGICA DE FILTROS TEMPORALES ---
st.sidebar.title("Filtros")
rango = st.sidebar.selectbox("Periodo de tiempo", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"])

def filtrar_por_fecha(df, opcion):
    hoy = datetime.now()
    if opcion == "Este año":
        return df[df['Fecha'].dt.year == hoy.year]
    elif opcion == "Año pasado":
        return df[df['Fecha'].dt.year == hoy.year - 1]
    elif opcion == "Este mes":
        return df[(df['Fecha'].dt.year == hoy.year) & (df['Fecha'].dt.month == hoy.month)]
    elif opcion == "Mes pasado":
        primer_dia_mes_actual = hoy.replace(day=1)
        ultimo_dia_mes_pasado = primer_dia_mes_actual - timedelta(days=1)
        return df[(df['Fecha'].dt.year == ultimo_dia_mes_pasado.year) & (df['Fecha'].dt.month == ultimo_dia_mes_pasado.month)]
    return df

df_partidos_filt = filtrar_por_fecha(df_partidos, rango)

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ Cara a Cara", "📝 Cargar Partido", "👤 Jugadores"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.title(f"🏆 Ranking - {rango}")
    
    # IMPORTANTE: Si hay filtro, recalculamos puntos solo de esos partidos
    # Si es "Siempre", usamos los puntos acumulados de la hoja Jugadores
    if rango == "Siempre":
        df_rank = df_jugadores.sort_values(by="Puntos", ascending=False)
    else:
        # Lógica simplificada: aquí podrías calcular puntos dinámicos del df_partidos_filt
        st.info("Mostrando puntos totales acumulados (Próximamente: cálculo dinámico por fechas)")
        df_rank = df_jugadores.sort_values(by="Puntos", ascending=False)

    for i, row in df_rank.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([0.5, 1, 4, 1.5])
            c1.subheader(f"#{i+1}")
            
            # Fix de Imagen
            url = row["Foto"]
            foto_final = url if pd.notnull(url) and str(url).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            c2.image(foto_final, width=65)
            
            # Navegación a estadísticas
            if c3.button(f"**{row['Nombre']}**", key=f"btn_{row['Nombre']}"):
                st.session_state.ver_jugador = row['Nombre']
                st.rerun()
            
            c4.subheader(f"{int(row['Puntos'])} pts")
            st.divider()

    # Mostrar estadísticas personales si se selecciona un jugador
    if 'ver_jugador' in st.session_state:
        st.sidebar.divider()
        st.sidebar.write(f"📊 **Perfil: {st.session_state.ver_jugador}**")
        jug = df_jugadores[df_jugadores['Nombre'] == st.session_state.ver_jugador].iloc[0]
        st.sidebar.write(f"PG: {jug['PG']} | PP: {jug['PP']}")
        if st.sidebar.button("Cerrar Perfil"):
            del st.session_state.ver_jugador
            st.rerun()

# --- 2. H2H ---
elif menu == "⚔️ Cara a Cara":
    st.title(f"⚔️ H2H - {rango}")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    col1, col2 = st.columns(2)
    j1 = col1.selectbox("Jugador 1", nombres)
    j2 = col2.selectbox("Jugador 2", nombres, index=1)
    
    # Usamos el DF filtrado por fecha
    enf = df_partidos_filt[
        ((df_partidos_filt['Ganador1'] == j1) | (df_partidos_filt['Ganador2'] == j1) | (df_partidos_filt['Perdedor1'] == j1) | (df_partidos_filt['Perdedor2'] == j1)) &
        ((df_partidos_filt['Ganador1'] == j2) | (df_partidos_filt['Ganador2'] == j2) | (df_partidos_filt['Perdedor1'] == j2) | (df_partidos_filt['Perdedor2'] == j2))
    ]
    
    wins_j1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
    wins_j2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
    
    st.metric(label="Historial Directo", value=f"{j1} {wins_j1} - {wins_j2} {j2}")
    st.table(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']])

# --- (El resto de secciones: Cargar Partido y Gestionar Jugadores se mantienen igual) ---
# ... (Copia aquí el código de guardado que ya nos funcionaba) ...
