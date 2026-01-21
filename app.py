import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS FIJO (DISEÑO DE TARJETAS Y SOMBRAS) ---
st.markdown("""
    <style>
    /* Estética de Tarjeta para Ranking y Bloques de Carga */
    .st-emotion-cache-12w0qpk, div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0px 10px 25px rgba(0,0,0,0.15) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        border: 1px solid #eee !important;
        margin-bottom: 20px !important;
    }
    
    /* Tarjeta específica del Ranking */
    .ranking-card {
        text-align: center;
    }

    .ranking-card img {
        width: 130px;
        height: 130px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #007bff;
        margin: 0 auto 10px auto;
        display: block;
    }

    .ranking-name {
        font-size: 22px;
        font-weight: bold;
        color: #333;
    }

    .ranking-points {
        font-size: 18px;
        color: #007bff;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        return jugadores, partidos
    except:
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FICHA TÉCNICA (ORDEN FIJO Y SIN ERRORES) ---
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
            
            if st.button(f"Ver Ficha", key=f"btn_{row['Nombre']}", use_container_width=True):
                mostrar_perfil(row['Nombre'], df_jugadores)

# --- 2. H2H (TÍTULOS CORREGIDOS) ---
elif menu == "⚔️ H2H":
    st.title("⚔️ Cara a Cara")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=1)

    mask = (
        ((df_partidos['Ganador1'] == j1) | (df_partidos['Ganador2'] == j1) | (df_partidos['Perdedor1'] == j1) | (df_partidos['Perdedor2'] == j1)) &
        ((df_partidos['Ganador1'] == j2) | (df_partidos['Ganador2'] == j2) | (df_partidos['Perdedor1'] == j2) | (df_partidos['Perdedor2'] == j2))
    )
    enfrentamientos = df_partidos[mask].copy()
    
    # Renombrar columnas para la visualización
    enfrentamientos['Ganadores'] = enfrentamientos['Ganador1'] + " / " + enfrentamientos['Ganador2']
    enfrentamientos['Perdedores'] = enfrentamientos['Perdedor1'] + " / " + enfrentamientos['Perdedor2']
    
    st.dataframe(enfrentamientos[["Fecha", "Ganadores", "Perdedores", "Resultado"]], hide_index=True, use_container_width=True)

# --- 3. CARGAR PARTIDO (CON TARJETAS SOMBREADAS) ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("form_registro"):
        with st.container(border=True):
            st.subheader("👥 Pareja 1")
            p1j1 = st.selectbox("Jugador A", nombres)
            p1j2 = st.selectbox("Jugador B", nombres)

        with st.container(border=True):
            st.subheader("👥 Pareja 2")
            p2j1 = st.selectbox("Jugador C", nombres)
            p2j2 = st.selectbox("Jugador D", nombres)

        for i in [1, 2, 3]:
            with st.container(border=True):
                st.subheader(f"🔢 SET {i}")
                c1, c2 = st.columns(2)
                if i==1: s1p1, s1p2 = c1.number_input("P1", 0, 7, key="s1p1"), c2.number_input("P2", 0, 7, key="s1p2")
                if i==2: s2p1, s2p2 = c1.number_input("P1", 0, 7, key="s2p1"), c2.number_input("P2", 0, 7, key="s2p2")
                if i==3: s3p1, s3p2 = c1.number_input("P1", 0, 7, key="s3p1"), c2.number_input("P2", 0, 7, key="s3p2")

        if st.form_submit_button("💾 GUARDAR PARTIDO", use_container_width=True):
            # Lógica de validación (7-5/7-6 y no 3er set si 2-0)
            ganador_s1 = "P1" if s1p1 > s1p2 else "P2"
            ganador_s2 = "P1" if s2p1 > s2p2 else "P2"
            
            if ganador_s1 == ganador_s2 and (s3p1 > 0 or s3p2 > 0):
                st.error("⚠️ No se carga 3er set si ganaron 2-0.")
            else:
                sets_p1 = (1 if s1p1 > s1p2 else 0) + (1 if s2p1 > s2p2 else 0) + (1 if s3p1 > s3p2 else 0)
                ganadores = [p1j1, p1j2] if sets_p1 >= 2 else [p2j1, p2j2]
                perdedores = [p2j1, p2j2] if sets_p1 >= 2 else [p1j1, p1j2]
                res = f"{s1p1}-{s1p2}, {s2p1}-{s2p2}" + (f", {s3p1}-{s3p2}" if (s3p1+s3p2)>0 else "")
                
                nueva_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "Ganador1": ganadores[0], "Ganador2": ganadores[1], "Perdedor1": perdedores[0], "Perdedor2": perdedores[1], "Resultado": res}])
                df_total = pd.concat([df_partidos, nueva_fila], ignore_index=True)
                conn.update(worksheet="Partidos", data=df_total)
                st.success("✅ ¡Guardado!")

# --- 4. BUSCAR JUGADOR ---
elif menu == "🔍 Buscar Jugador":
    st.title("🔍 Buscar Jugador")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    seleccion = st.selectbox("Escribe el nombre del jugador", [""] + nombres)
    if seleccion:
        mostrar_perfil(seleccion, df_jugadores)
