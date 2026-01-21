import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS FIJO E INAMOVIBLE (SOMBRAS Y TARJETAS) ---
st.markdown("""
    <style>
    /* Forzar sombras reales en todos los contenedores con borde */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0px 10px 30px rgba(0,0,0,0.2) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        border: 1px solid #f0f0f0 !important;
        margin-bottom: 25px !important;
    }
    
    /* Estilo de la tarjeta de Ranking */
    .ranking-card {
        text-align: center;
    }
    .ranking-card img {
        width: 140px;
        height: 140px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #007bff;
        margin: 0 auto 15px auto;
        display: block;
    }
    .ranking-name {
        font-size: 24px;
        font-weight: bold;
        color: #333;
    }
    .ranking-points {
        font-size: 20px;
        color: #007bff;
        font-weight: bold;
        margin-top: 5px;
    }
    /* Estilo para los títulos de filtros */
    .filtro-resaltado {
        font-size: 19px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        return jugadores, partidos
    except:
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FUNCIÓN FILTRADO ---
def filtrar_por_fecha(df, opcion):
    hoy = datetime.now()
    if df.empty: return df
    if opcion == "Este año": return df[df['Fecha'].dt.year == hoy.year]
    elif opcion == "Año pasado": return df[df['Fecha'].dt.year == hoy.year - 1]
    elif opcion == "Este mes": return df[(df['Fecha'].dt.year == hoy.year) & (df['Fecha'].dt.month == hoy.month)]
    elif opcion == "Mes pasado":
        mes_pasado = (hoy.replace(day=1) - timedelta(days=1))
        return df[(df['Fecha'].dt.year == mes_pasado.year) & (df['Fecha'].dt.month == mes_pasado.month)]
    return df

# --- FICHA TÉCNICA ---
@st.dialog("📊 Ficha Técnica")
def mostrar_perfil(nombre_jugador, df_jugadores):
    df_temp = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    posicion = df_temp[df_temp['Nombre'] == nombre_jugador].index[0] + 1
    datos = df_temp[df_temp['Nombre'] == nombre_jugador].iloc[0]
    st.markdown(f"<h2 style='text-align: center;'>👤 {nombre_jugador}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>🏆 Posición: #{posicion}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #007bff;'>⭐ Puntos: {int(datos['Puntos'])}</h3>", unsafe_allow_html=True)
    st.divider()
    st.write(f"✅ **Ganados:** {int(datos['PG'])}")
    st.write(f"❌ **Perdidos:** {int(datos['PP_perd'])}")
    st.write(f"🎾 **Sets ganados:** {int(datos['SG'])}")
    st.write(f"🎾 **Sets perdidos:** {int(datos['SP'])}")
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"📈 **Efectividad: {efect:.1f}%**")
        st.progress(efect / 100)

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
            st.markdown(f"""
                <div class="ranking-card">
                    <div style="color: #888; font-weight: bold;">PUESTO #{i+1}</div>
                    <img src="{img_url}">
                    <div class="ranking-name">{row['Nombre']}</div>
                    <div class="ranking-points">{int(row['Puntos'])} PUNTOS</div>
                </div>
            """, unsafe_allow_html=True)
            if st.button("Ver Ficha", key=f"btn_{row['Nombre']}", use_container_width=True):
                mostrar_perfil(row['Nombre'], df_jugadores)

# --- 2. H2H ---
elif menu == "⚔️ H2H":
    st.markdown('<p class="filtro-resaltado">Periodo</p>', unsafe_allow_html=True)
    rango_h2h = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("⚔️ Cara a Cara")
    
    df_p_filt = filtrar_por_fecha(df_partidos, rango_h2h)
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=1)

    mask = (
        ((df_p_filt['Ganador1'] == j1) | (df_p_filt['Ganador2'] == j1) | (df_p_filt['Perdedor1'] == j1) | (df_p_filt['Perdedor2'] == j1)) &
        ((df_p_filt['Ganador1'] == j2) | (df_p_filt['Ganador2'] == j2) | (df_p_filt['Perdedor1'] == j2) | (df_p_filt['Perdedor2'] == j2))
    )
    enf = df_p_filt[mask].copy()
    
    v1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
    v2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
    
    st.markdown("### HISTORIAL:")
    st.markdown(f"## {j1} {v1} — {v2} {j2}") # Salto de línea implícito por el encabezado H2
    
    enf['Ganadores'] = enf['Ganador1'] + " / " + enf['Ganador2']
    enf['Perdedores'] = enf['Perdedor1'] + " / " + enf['Perdedor2']
    enf['Fecha_str'] = enf['Fecha'].dt.strftime('%d/%m/%Y')
    
    st.dataframe(enf[["Fecha_str", "Ganadores", "Perdedores", "Resultado"]], hide_index=True, use_container_width=True)

# --- 3. CARGAR PARTIDO ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    with st.form("f_reg"):
        with st.container(border=True):
            st.subheader("👥 Pareja 1")
            p1j1, p1j2 = st.selectbox("Jugador A", nombres), st.selectbox("Jugador B", nombres)
        with st.container(border=True):
            st.subheader("👥 Pareja 2")
            p2j1, p2j2 = st.selectbox("Jugador C", nombres), st.selectbox("Jugador D", nombres)
        for i in [1, 2, 3]:
            with st.container(border=True):
                st.subheader(f"🔢 SET {i}")
                c1, c2 = st.columns(2)
                if i==1: s1p1, s1p2 = c1.number_input("P1", 0, 7, key="s1p1"), c2.number_input("P2", 0, 7, key="s1p2")
                if i==2: s2p1, s2p2 = c1.number_input("P1", 0, 7, key="s2p1"), c2.number_input("P2", 0, 7, key="s2p2")
                if i==3: s3p1, s3p2 = c1.number_input("P1", 0, 7, key="s3p1"), c2.number_input("P2", 0, 7, key="s3p2")
        if st.form_submit_button("💾 GUARDAR PARTIDO", use_container_width=True):
            #
