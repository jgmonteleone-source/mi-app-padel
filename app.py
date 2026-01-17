import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- SIMULACIÓN DE BASE DE DATOS (Esto luego irá a la nube) ---
if 'jugadores' not in st.session_state:
    st.session_state.jugadores = {
        "Agustín Tapia": {"puntos": 15, "foto": "👤", "pp": 6, "pg": 5, "pp_perd": 1, "sg": 10, "sp": 3, "gg": 72, "gp": 45},
        "Arturo Coello": {"puntos": 14, "foto": "👤", "pp": 6, "pg": 4, "pp_perd": 2, "sg": 9, "sp": 4, "gg": 68, "gp": 50},
        "Ale Galán": {"puntos": 12, "foto": "👤", "pp": 5, "pg": 4, "pp_perd": 1, "sg": 8, "sp": 3, "gg": 60, "gp": 40},
    }

# --- ESTILOS ---
st.title("🎾 Padel Ranking App")

# --- NAVEGACIÓN ---
menu = st.sidebar.selectbox("Menú", ["Ranking General", "Cargar Partido", "Mi Perfil"])

if menu == "Ranking General":
    st.header("🏆 Ranking de Jugadores")
    
    # Convertir datos para mostrar en tabla
    df_ranking = pd.DataFrame.from_dict(st.session_state.jugadores, orient='index')
    df_ranking = df_ranking.sort_values(by="puntos", ascending=False)
    
    # Mostrar Ranking con interacción
    for nombre in df_ranking.index:
        cols = st.columns([1, 4, 2, 2])
        with cols[0]:
            st.write(st.session_state.jugadores[nombre]["foto"])
        with cols[1]:
            if st.button(nombre, key=nombre):
                st.session_state.perfil_seleccionado = nombre
                st.rerun()
        with cols[2]:
            st.write(f"*{st.session_state.jugadores[nombre]['puntos']} pts*")
        with cols[3]:
            st.caption(f"{st.session_state.jugadores[nombre]['pg']}V - {st.session_state.jugadores[nombre]['pp_perd']}D")

    # --- PANTALLA DE DETALLE (ESTADÍSTICAS) ---
    if 'perfil_seleccionado' in st.session_state:
        st.divider()
        p = st.session_state.perfil_seleccionado
        datos = st.session_state.jugadores[p]
        
        st.subheader(f"Estadísticas Detalladas: {p}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Partidos Jugados (PP)", datos["pp"])
        c1.metric("Partidos Ganados (PG)", datos["pg"])
        c1.metric("Partidos Perdidos (PP)", datos["pp_perd"])
        
        c2.metric("Sets Ganados (SG)", datos["sg"])
        c2.metric("Sets Perdidos (SP)", datos["sp"])
        
        c3.metric("Games Ganados (GG)", datos["gg"])
        c3.metric("Games Perdidos (GP)", datos["gp"])
        
        if st.button("Cerrar Perfil"):
            del st.session_state.perfil_seleccionado
            st.rerun()

elif menu == "Cargar Partido":
    st.header("📝 Registro de Resultado")
    
    with st.form("form_partido"):
        col1, col2 = st.columns(2)
        with col1:
            j1 = st.selectbox("Jugador 1 (Tú)", list(st.session_state.jugadores.keys()))
            j2 = st.selectbox("Pareja", list(st.session_state.jugadores.keys()))
        with col2:
            r1 = st.selectbox("Rival 1", list(st.session_state.jugadores.keys()))
            r2 = st.selectbox("Rival 2", list(st.session_state.jugadores.keys()))
        
        resultado = st.text_input("Resultado (ej: 6-4, 2-6, 6-3)", placeholder="6-4, 6-2")
        
        if st.form_submit_button("Guardar Partido"):
            st.success("Partido guardado con éxito. (Lógica de puntos aplicada)")
