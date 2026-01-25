import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS FIJO E INAMOVIBLE ---
st.markdown("""
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0px 10px 30px rgba(0,0,0,0.2) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        border: 1px solid #f0f0f0 !important;
        margin-bottom: 25px !important;
    }
    .ranking-card { text-align: center; }
    .ranking-card img {
        width: 140px; height: 140px; border-radius: 50%;
        object-fit: cover; border: 4px solid #007bff;
        margin: 0 auto 15px auto; display: block;
    }
    .ranking-name { font-size: 24px; font-weight: bold; color: #333; }
    .ranking-points { font-size: 20px; color: #007bff; font-weight: bold; margin-top: 5px; }
    .filtro-resaltado { font-size: 19px; font-weight: bold; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        cols_numericas = ['Puntos', 'PG', 'PP_perd', 'SG', 'SP']
        for col in cols_numericas:
            if col in jugadores.columns:
                jugadores[col] = pd.to_numeric(jugadores[col], errors='coerce').fillna(0)
        
        partidos = conn.read(worksheet="Partidos", ttl=0)
        if partidos.empty:
            partidos = pd.DataFrame(columns=["Fecha", "Ganador1", "Ganador2", "Perdedor1", "Perdedor2", "Resultado"])
        else:
            partidos = partidos.dropna(subset=["Fecha"])
            partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        return jugadores, partidos
    except:
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FUNCIONES DE APOYO ---
def filtrar_por_fecha(df, opcion):
    hoy = datetime.now()
    if df.empty or 'Fecha' not in df.columns: return df
    if opcion == "Este año": return df[df['Fecha'].dt.year == hoy.year]
    elif opcion == "Año pasado": return df[df['Fecha'].dt.year == hoy.year - 1]
    elif opcion == "Este mes": return df[(df['Fecha'].dt.year == hoy.year) & (df['Fecha'].dt.month == hoy.month)]
    elif opcion == "Mes pasado":
        mes_pasado = (hoy.replace(day=1) - timedelta(days=1))
        return df[(df['Fecha'].dt.year == mes_pasado.year) & (df['Fecha'].dt.month == mes_pasado.month)]
    return df

def mostrar_perfil_en_pantalla(nombre_jugador, df_jugadores):
    """Muestra la ficha técnica directamente en la interfaz principal"""
    df_temp = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    posicion = df_temp[df_temp['Nombre'] == nombre_jugador].index[0] + 1
    datos = df_temp[df_temp['Nombre'] == nombre_jugador].iloc[0]
    
    col1, col2 = st.columns([1, 2])
    with col1:
        img_url = datos['Foto'] if str(datos['Foto']).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        st.image(img_url, width=200)
    
    with col2:
        st.markdown(f"## {nombre_jugador}")
        st.markdown(f"🏆 **Posición en Ranking:** #{posicion}")
        st.markdown(f"⭐ **Puntos Totales:** {int(datos['Puntos'])}")
    
    st.divider()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ganados", int(datos['PG']))
    c2.metric("Perdidos", int(datos['PP_perd']))
    c3.metric("Sets G", int(datos['SG']))
    c4.metric("Sets P", int(datos['SP']))
    
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"**Efectividad de Victoria:** {efect:.1f}%")
        st.progress(efect / 100)

@st.dialog("📊 Ficha Técnica")
def mostrar_perfil_dialogo(nombre_jugador, df_jugadores):
    mostrar_perfil_en_pantalla(nombre_jugador, df_jugadores)

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H", "📝 Cargar partido", "🔍 Buscar Jugador"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.markdown('<p class="filtro-resaltado">Periodo</p>', unsafe_allow_html=True)
    rango = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("🏆 Ranking")
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    for i, row in df_rank.iterrows():
        with st.container(border=True):
            img_url = row['Foto'] if str(row['Foto']).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            st.markdown(f"""<div class="ranking-card"><div style="color: #888; font-weight: bold;">PUESTO #{i+1}</div><img src="{img_url}"><div class="ranking-name">{row['Nombre']}</div><div class="ranking-points">{int(row['Puntos'])} PUNTOS</div></div>""", unsafe_allow_html=True)
            if st.button("Ver Ficha Completa", key=f"btn_{row['Nombre']}", use_container_width=True):
                mostrar_perfil_dialogo(row['Nombre'], df_jugadores)

# --- 4. BUSCAR JUGADOR (CORREGIDO Y MEJORADO) ---
elif menu == "🔍 Buscar Jugador":
    st.title("🔍 Perfil de Jugador")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    sel = st.selectbox("Busca un jugador para ver sus estadísticas:", [""] + nombres)
    
    if sel != "":
        with st.container(border=True):
            mostrar_perfil_en_pantalla(sel, df_jugadores)
            
            # Extra: Mostrar últimos partidos de este jugador
            st.subheader("🎾 Últimos Partidos")
            mask_jugador = (df_partidos['Ganador1'] == sel) | (df_partidos['Ganador2'] == sel) | \
                           (df_partidos['Perdedor1'] == sel) | (df_partidos['Perdedor2'] == sel)
            ultimos = df_partidos[mask_jugador].tail(5)
            if not ultimos.empty:
                st.dataframe(ultimos, hide_index=True, use_container_width=True)
            else:
                st.info("No hay partidos registrados para este jugador.")

# (El resto de las secciones H2H y Cargar Partido se mantienen igual para no tocar el código que ya funciona)
elif menu == "⚔️ H2H":
    # ... (tu código original de H2H)
    st.title("⚔️ Cara a Cara")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=1)
    # [Lógica H2H que ya tenías...]
    df_p_filt = filtrar_por_fecha(df_partidos, "Siempre")
    mask = (((df_p_filt['Ganador1'] == j1) | (df_p_filt['Ganador2'] == j1) | (df_p_filt['Perdedor1'] == j1) | (df_p_filt['Perdedor2'] == j1)) & ((df_p_filt['Ganador1'] == j2) | (df_p_filt['Ganador2'] == j2) | (df_p_filt['Perdedor1'] == j2) | (df_p_filt['Perdedor2'] == j2)))
    enf = df_p_filt[mask].copy()
    st.write(f"Enfrentamientos encontrados: {len(enf)}")
    if not enf.empty:
        st.dataframe(enf, use_container_width=True)

elif menu == "📝 Cargar partido":
    # ... (tu código original de Cargar partido)
    st.title("📝 Registrar Partido")
    # [Toda tu lógica de formulario y guardado blindado...]
