import streamlit as st
import pandas as pd

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- LÓGICA DE DATOS (Mantenemos sesión temporal por ahora, luego conectamos Sheets) ---
if 'partidos_historial' not in st.session_state:
    st.session_state.partidos_historial = [] # Aquí se guardarán todos los partidos cargados
if 'jugadores' not in st.session_state:
    # Agregamos campo 'foto' con una URL por defecto
    nombres = ["Agustín Tapia", "Arturo Coello", "Ale Galán", "Fede Chingotto", "Juan Lebrón", "Paquito Navarro"]
    st.session_state.jugadores = {
        n: {"puntos": 0, "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", 
            "pp": 0, "pg": 0, "pp_perd": 0, "sg": 0, "sp": 0, "gg": 0, "gp": 0} 
        for n in nombres
    }

# --- PROCESAMIENTO MATEMÁTICO ---
def registrar_en_memoria(g1, g2, p1, p2, score_str):
    try:
        sets = [s.strip().split('-') for s in score_str.split(',')]
        sets = [(int(s[0]), int(s[1])) for s in sets]
        sg_g, sg_p, gg_g, gg_p = 0, 0, 0, 0
        for g_f, g_c in sets:
            gg_g += g_f; gg_p += g_c
            if g_f > g_c: sg_g += 1
            else: sg_p += 1
        
        # Guardar en historial para el H2H
        st.session_state.partidos_historial.append({
            "ganadores": [g1, g2], "perdedores": [p1, p2], "score": score_str
        })
        
        # Puntos ranking
        p_gan = 3 if sg_p == 0 else 2
        p_per = 1 if sg_g == 1 else 0

        for g in [g1, g2]:
            st.session_state.jugadores[g].update({
                "puntos": st.session_state.jugadores[g]["puntos"] + p_gan,
                "pp": st.session_state.jugadores[g]["pp"] + 1,
                "pg": st.session_state.jugadores[g]["pg"] + 1,
                "sg": st.session_state.jugadores[g]["sg"] + sg_g,
                "sp": st.session_state.jugadores[g]["sp"] + sg_p,
                "gg": st.session_state.jugadores[g]["gg"] + gg_g,
                "gp": st.session_state.jugadores[g]["gp"] + gg_p
            })
        for p in [p1, p2]:
            st.session_state.jugadores[p].update({
                "puntos": st.session_state.jugadores[p]["puntos"] + p_per,
                "pp": st.session_state.jugadores[p]["pp"] + 1,
                "pp_perd": st.session_state.jugadores[p]["pp_perd"] + 1,
                "sg": st.session_state.jugadores[p]["sg"] + sg_p,
                "sp": st.session_state.jugadores[p]["sp"] + sg_g,
                "gg": st.session_state.jugadores[p]["gg"] + gg_p,
                "gp": st.session_state.jugadores[p]["gp"] + gg_g
            })
        return True
    except: return False

# --- INTERFAZ ---
menu = st.sidebar.radio("Navegación", ["🏆 Ranking", "⚔️ Cara a Cara (H2H)", "📝 Cargar Partido"])

if menu == "🏆 Ranking":
    st.header("Ranking General")
    df = pd.DataFrame.from_dict(st.session_state.jugadores, orient='index').sort_values("puntos", ascending=False)
    for nombre in df.index:
        c1, c2, c3 = st.columns([1, 4, 1])
        c1.image(st.session_state.jugadores[nombre]["foto"], width=50)
        if c2.button(nombre, key=f"btn_{nombre}"): st.session_state.ver = nombre
        c3.subheader(f"{st.session_state.jugadores[nombre]['puntos']} pts")

    if "ver" in st.session_state:
        st.divider()
        n = st.session_state.ver
        d = st.session_state.jugadores[n]
        st.image(d["foto"], width=100)
        st.title(n)
        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Partidos (G/P)", f"{d['pg']}/{d['pp_perd']}")
        col_b.metric("Sets (G/P)", f"{d['sg']}/{d['sp']}")
        col_c.metric("Games (G/P)", f"{d['gg']}/{d['gp']}")
        if st.button("Cerrar"): del st.session_state.ver; st.rerun()

elif menu == "⚔️ Cara a Cara (H2H)":
    st.header("Enfrentamientos Directos")
    col1, col2 = st.columns(2)
    j_a = col1.selectbox("Jugador A", list(st.session_state.jugadores.keys()))
    j_b = col2.selectbox("Jugador B", list(st.session_state.jugadores.keys()))
    
    # Filtrar historial
    enfrentamientos = [p for p in st.session_state.partidos_historial 
                      if (j_a in p['ganadores'] or j_a in p['perdedores']) and 
                         (j_b in p['ganadores'] or j_b in p['perdedores'])]
    
    victorias_a = sum(1 for p in enfrentamientos if j_a in p['ganadores'])
    victorias_b = sum(1 for p in enfrentamientos if j_b in p['ganadores'])
    
    st.subheader(f"Resultado Histórico: {j_a} {victorias_a} - {victorias_b} {j_b}")
    st.table(pd.DataFrame(enfrentamientos))

elif menu == "📝 Cargar Partido":
    st.header("Registrar Resultado")
    with st.form("match"):
        g1 = st.selectbox("Ganador 1", list(st.session_state.jugadores.keys()))
        g2 = st.selectbox("Ganador 2", list(st.session_state.jugadores.keys()))
        p1 = st.selectbox("Perdedor 1", list(st.session_state.jugadores.keys()))
        p2 = st.selectbox("Perdedor 2", list(st.session_state.jugadores.keys()))
        res = st.text_input("Resultado (ej: 6-4, 7-5)")
        if st.form_submit_button("Guardar"):
            if registrar_en_memoria(g1, g2, p1, p2, res): st.success("¡Datos guardados!")
            else: st.error("Error en el formato.")
