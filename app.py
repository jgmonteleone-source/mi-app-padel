import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro Stats", layout="wide")

# --- BASE DE DATOS TEMPORAL (Se reinicia al refrescar hasta conectar Firebase) ---
if 'jugadores' not in st.session_state:
    nombres = ["Agustín Tapia", "Arturo Coello", "Ale Galán", "Fede Chingotto"]
    st.session_state.jugadores = {
        n: {"puntos": 0, "foto": "👤", "pp": 0, "pg": 0, "pp_perd": 0, "sg": 0, "sp": 0, "gg": 0, "gp": 0} 
        for n in nombres
    }

# --- FUNCIÓN LÓGICA DE PROCESAMIENTO ---
def procesar_resultado(ganadores, perdedores, score_str):
    try:
        # Limpiar y convertir el score (ej: "6-4, 2-6, 6-3")
        sets = [s.strip().split('-') for s in score_str.split(',')]
        sets = [(int(s[0]), int(s[1])) for s in sets]
        
        sg_ganadores = 0
        sg_perdedores = 0
        gg_ganadores = 0
        gg_perdedores = 0

        for g1, g2 in sets:
            gg_ganadores += g1
            gg_perdedores += g2
            if g1 > g2: sg_ganadores += 1
            else: sg_perdedores += 1

        # Determinar puntos según tus reglas
        pts_gan = 3 if sg_perdedores == 0 else 2
        pts_per = 1 if sg_ganadores == 1 else 0

        # Actualizar a los 2 ganadores
        for g in ganadores:
            st.session_state.jugadores[g]["puntos"] += pts_gan
            st.session_state.jugadores[g]["pp"] += 1
            st.session_state.jugadores[g]["pg"] += 1
            st.session_state.jugadores[g]["sg"] += sg_ganadores
            st.session_state.jugadores[g]["sp"] += sg_perdedores
            st.session_state.jugadores[g]["gg"] += gg_ganadores
            st.session_state.jugadores[g]["gp"] += gg_perdedores

        # Actualizar a los 2 perdedores
        for p in perdedores:
            st.session_state.jugadores[p]["puntos"] += pts_per
            st.session_state.jugadores[p]["pp"] += 1
            st.session_state.jugadores[p]["pp_perd"] += 1
            st.session_state.jugadores[p]["sg"] += sg_perdedores
            st.session_state.jugadores[p]["sp"] += sg_ganadores
            st.session_state.jugadores[p]["gg"] += gg_perdedores
            st.session_state.jugadores[p]["gp"] += gg_ganadores
            
        return True
    except:
        return False

# --- INTERFAZ ---
st.title("🎾 Padel Ranking Pro")

menu = st.sidebar.selectbox("Menú", ["Ranking General", "Cargar Partido"])

if menu == "Ranking General":
    st.header("🏆 Clasificación")
    df = pd.DataFrame.from_dict(st.session_state.jugadores, orient='index')
    df = df.sort_values(by="puntos", ascending=False)
    
    for nombre in df.index:
        col1, col2, col3 = st.columns([1, 3, 2])
        col1.write(st.session_state.jugadores[nombre]["foto"])
        if col2.button(nombre):
            st.session_state.ver_perfil = nombre
        col3.write(f"**{st.session_state.jugadores[nombre]['puntos']} Pts**")

    if "ver_perfil" in st.session_state:
        st.divider()
        n = st.session_state.ver_perfil
        d = st.session_state.jugadores[n]
        st.subheader(f"📊 Estadísticas de {n}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Partidos (PG/PP)", f"{d['pg']}/{d['pp_perd']}")
        c2.metric("Sets (SG/SP)", f"{d['sg']}/{d['sp']}")
        c3.metric("Games (GG/GP)", f"{d['gg']}/{d['gp']}")
        if st.button("Cerrar Perfil"):
            del st.session_state.ver_perfil
            st.rerun()

elif menu == "Cargar Partido":
    st.header("📝 Nuevo Resultado")
    lista_j = list(st.session_state.jugadores.keys())
    
    with st.form("registro"):
        st.subheader("Pareja Ganadora")
        g1 = st.selectbox("Ganador 1", lista_j)
        g2 = st.selectbox("Ganador 2", lista_j)
        
        st.subheader("Pareja Perdedora")
        p1 = st.selectbox("Perdedor 1", lista_j)
        p2 = st.selectbox("Perdedor 2", lista_j)
        
        resultado = st.text_input("Resultado (ej: 6-4, 2-6, 6-3)")
        
        if st.form_submit_button("Registrar Partido"):
            if g1 != g2 and p1 != p2 and g1 not in [p1, p2]:
                exito = procesar_resultado([g1, g2], [p1, p2], resultado)
                if exito: 
                    st.success("¡Ranking actualizado!")
                else: 
                    st.error("Formato de resultado incorrecto (usa: 6-4, 6-2)")
            else:
                st.error("Un jugador no puede estar en dos posiciones a la vez.")
