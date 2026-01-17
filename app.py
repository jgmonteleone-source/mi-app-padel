import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Busca automáticamente la sección [connections.gsheets] de los Secrets
        jugadores = conn.read(worksheet="Jugadores", ttl="0")
        partidos = conn.read(worksheet="Partidos", ttl="0")
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error de conexión: {e}")
        return pd.DataFrame(columns=["Nombre", "Foto", "Puntos", "PP", "PG", "PP_perd", "SG", "SP", "GG", "GP"]), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["🏆 Ranking", "⚔️ Cara a Cara (H2H)", "📝 Cargar Partido", "👤 Gestionar Jugadores"])

if menu == "🏆 Ranking":
    st.title("🏆 Clasificación General")
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False)
    for i, row in df_rank.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([0.5, 1, 4, 1.5])
            c1.subheader(f"#{i+1}")
            c2.image(row["Foto"], width=60)
            if c3.button(f"**{row['Nombre']}**", key=f"btn_{row['Nombre']}"):
                st.session_state.ver_jugador = row['Nombre']
            c4.subheader(f"{row['Puntos']} pts")
            st.divider()

elif menu == "⚔️ Cara a Cara (H2H)":
    st.title("⚔️ Cara a Cara (H2H)")
    nombres_lista = df_jugadores["Nombre"].tolist()
    col1, col2 = st.columns(2)
    j_a = col1.selectbox("Jugador A", nombres_lista)
    j_b = col2.selectbox("Jugador B", nombres_lista, index=min(1, len(nombres_lista)-1))
    if j_a != j_b:
        enf = df_partidos[
            ((df_partidos['Ganador1'] == j_a) | (df_partidos['Ganador2'] == j_a) | (df_partidos['Perdedor1'] == j_a) | (df_partidos['Perdedor2'] == j_a)) &
            ((df_partidos['Ganador1'] == j_b) | (df_partidos['Ganador2'] == j_b) | (df_partidos['Perdedor1'] == j_b) | (df_partidos['Perdedor2'] == j_b))
        ]
        v_a = len(enf[(enf['Ganador1'] == j_a) | (enf['Ganador2'] == j_a)])
        v_b = len(enf[(enf['Ganador1'] == j_b) | (enf['Ganador2'] == j_b)])
        st.header(f"Historial Directo: {j_a} {v_a} - {v_b} {j_b}")
        st.dataframe(enf, use_container_width=True)

elif menu == "📝 Cargar Partido":
    st.title("📝 Registrar Nuevo Partido")
    nombres_lista = sorted(df_jugadores["Nombre"].tolist())
    with st.form("form_partido"):
        h_c1, h_c2, h_s1, h_s2, h_s3 = st.columns([2, 2, 0.8, 0.8, 0.8])
        r1_c1, r1_c2, r1_s1, r1_s2, r1_s3 = st.columns([2, 2, 0.8, 0.8, 0.8])
        p1j1 = r1_c1.selectbox("P1J1", nombres_lista, key="p1j1", label_visibility="collapsed")
        p1j2 = r1_c2.selectbox("P1J2", nombres_lista, key="p1j2", label_visibility="collapsed")
        p1s1 = r1_s1.number_input("P1S1", 0, 7, key="p1s1", label_visibility="collapsed")
        p1s2 = r1_s2.number_input("P1S2", 0, 7, key="p1s2", label_visibility="collapsed")
        p1s3 = r1_s3.number_input("P1S3", 0, 7, key="p1s3", label_visibility="collapsed")
        st.divider()
        r2_c1, r2_c2, r2_s1, r2_s2, r2_s3 = st.columns([2, 2, 0.8, 0.8, 0.8])
        p2j1 = r2_c1.selectbox("P2J1", nombres_lista, key="p2j1", label_visibility="collapsed")
        p2j2 = r2_c2.selectbox("P2J2", nombres_lista, key="p2j2", label_visibility="collapsed")
        p2s1 = r2_s1.number_input("P2S1", 0, 7, key="p2s1", label_visibility="collapsed")
        p2s2 = r2_s2.number_input("P2S2", 0, 7, key="p2s2", label_visibility="collapsed")
        p2s3 = r2_s3.number_input("P2S3", 0, 7, key="p2s3", label_visibility="collapsed")
        
        if st.form_submit_button("💾 GUARDAR PARTIDO"):
            # Lógica simplificada de guardado
            st.info("Guardando datos...")
            # (Aquí iría la lógica de concatenar y conn.update que ya tenías)
            st.rerun()

elif menu == "👤 Gestionar Jugadores":
    st.title("Gestión")
    nombre_n = st.text_input("Nombre")
    foto_n = st.text_input("URL Foto")
    if st.button("Crear"):
        nueva_j = pd.DataFrame([{"Nombre": nombre_n, "Foto": foto_n, "Puntos": 0, "PP": 0, "PG": 0, "PP_perd": 0, "SG": 0, "SP": 0, "GG": 0, "GP": 0}])
        df_final = pd.concat([df_jugadores, nueva_j], ignore_index=True)
        conn.update(worksheet="Jugadores", data=df_final)
        st.rerun()
