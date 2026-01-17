import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Padel Pro App", layout="wide", initial_sidebar_state="expanded")

# --- ESTILOS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .main { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

# --- INICIALIZACIÓN DE DATOS ---
if 'partidos_historial' not in st.session_state:
    st.session_state.partidos_historial = []
if 'jugadores' not in st.session_state:
    nombres = ["Agustín Tapia", "Arturo Coello", "Ale Galán", "Fede Chingotto"]
    st.session_state.jugadores = {
        n: {"puntos": 0, "foto": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png", 
            "pp": 0, "pg": 0, "pp_perd": 0, "sg": 0, "sp": 0, "gg": 0, "gp": 0} 
        for n in nombres
    }

# --- FUNCIONES DE CÁLCULO ---
def registrar_partido(g1, g2, p1, p2, score_str):
    try:
        sets = [s.strip().split('-') for s in score_str.split(',')]
        sets = [(int(s[0]), int(s[1])) for s in sets]
        sg_g, sg_p, gg_g, gg_p = 0, 0, 0, 0
        for g_f, g_c in sets:
            gg_g += g_f; gg_p += g_c
            if g_f > g_c: sg_g += 1
            else: sg_p += 1
        
        # Guardar en historial
        st.session_state.partidos_historial.append({
            "Fecha": datetime.now().strftime("%d/%m/%Y"),
            "Ganadores": f"{g1} / {g2}",
            "Perdedores": f"{p1} / {p2}",
            "Resultado": score_str,
            "Lista_G": [g1, g2],
            "Lista_P": [p1, p2]
        })
        
        # Lógica de Puntos (3, 2, 1, 0)
        p_gan = 3 if sg_p == 0 else 2
        p_per = 1 if sg_g == 1 else 0

        for g in [g1, g2]:
            st.session_state.jugadores[g]["puntos"] += p_gan
            st.session_state.jugadores[g]["pg"] += 1
            st.session_state.jugadores[g]["pp"] += 1
            st.session_state.jugadores[g]["sg"] += sg_g
            st.session_state.jugadores[g]["sp"] += sg_p
            st.session_state.jugadores[g]["gg"] += gg_g
            st.session_state.jugadores[g]["gp"] += gg_p

        for p in [p1, p2]:
            st.session_state.jugadores[p]["puntos"] += p_per
            st.session_state.jugadores[p]["pp_perd"] += 1
            st.session_state.jugadores[p]["pp"] += 1
            st.session_state.jugadores[p]["sg"] += sg_p
            st.session_state.jugadores[p]["sp"] += sg_g
            st.session_state.jugadores[p]["gg"] += gg_p
            st.session_state.jugadores[p]["gp"] += gg_g
        return True
    except: return False

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["🏆 Ranking", "⚔️ Cara a Cara (H2H)", "📝 Cargar Partido", "👤 Gestionar Jugadores"])

if menu == "🏆 Ranking":
    st.title("🏆 Ranking de la Liga")
    df = pd.DataFrame.from_dict(st.session_state.jugadores, orient='index').sort_values("puntos", ascending=False)
    
    for i, nombre in enumerate(df.index):
        with st.container():
            c1, c2, c3, c4 = st.columns([0.5, 1, 4, 1])
            c1.subheader(f"#{i+1}")
            c2.image(st.session_state.jugadores[nombre]["foto"], width=60)
            if c3.button(f"**{nombre}**", key=f"rank_{nombre}"):
                st.session_state.ver = nombre
            c4.subheader(f"{st.session_state.jugadores[nombre]['puntos']} pts")
            st.divider()

    if "ver" in st.session_state:
        n = st.session_state.ver
        d = st.session_state.jugadores[n]
        st.sidebar.image(d["foto"], width=150)
        st.sidebar.title(n)
        st.sidebar.metric("Partidos Jugados", d['pp'])
        st.sidebar.write(f"✅ Ganados: {d['pg']} | ❌ Perdidos: {d['pp_perd']}")
        st.sidebar.progress(d['pg']/d['pp'] if d['pp']>0 else 0)
        st.sidebar.write(f"🎾 Sets: {d['sg']}G - {d['sp']}P")
        st.sidebar.write(f"🔢 Games: {d['gg']}G - {d['gp']}P")
        if st.sidebar.button("Cerrar Detalle"):
            del st.session_state.ver
            st.rerun()

elif menu == "⚔️ Cara a Cara (H2H)":
    st.title("⚔️ Cara a Cara (H2H)")
    lista_j = list(st.session_state.jugadores.keys())
    col1, col2 = st.columns(2)
    j_a = col1.selectbox("Selecciona Jugador 1", lista_j)
    j_b = col2.selectbox("Selecciona Jugador 2", lista_j, index=1)
    
    if j_a == j_b:
        st.warning("Selecciona dos jugadores distintos.")
    else:
        enf = [p for p in st.session_state.partidos_historial 
               if (j_a in p['Lista_G'] or j_a in p['Lista_P']) and (j_b in p['Lista_G'] or j_b in p['Lista_P'])]
        
        v_a = sum(1 for p in enf if j_a in p['Lista_G'])
        v_b = sum(1 for p in enf if j_b in p['Lista_G'])
        
        st.divider()
        st.header(f"Historial: {j_a} {v_a} - {v_b} {j_b}")
        if enf:
            st.table(pd.DataFrame(enf)[["Fecha", "Ganadores", "Perdedores", "Resultado"]])
        else:
            st.info("Aún no se han enfrentado.")

elif menu == "📝 Cargar Partido":
    st.title("📝 Registrar Nuevo Partido")
    lista_j = sorted(list(st.session_state.jugadores.keys()))
    with st.form("match_form"):
        c1, c2 = st.columns(2)
        g1 = c1.selectbox("Ganador 1", lista_j); g2 = c1.selectbox("Ganador 2", lista_j)
        p1 = c2.selectbox("Perdedor 1", lista_j); p2 = c2.selectbox("Perdedor 2", lista_j)
        resultado = st.text_input("Resultado (ej: 6-4, 7-5 o 6-3, 2-6, 7-6)")
        if st.form_submit_button("GUARDAR RESULTADO"):
            if len({g1, g2, p1, p2}) < 4:
                st.error("No puedes repetir jugadores en el mismo partido.")
            elif registrar_partido(g1, g2, p1, p2, resultado):
                st.success("¡Partido registrado y ranking actualizado!")
            else:
                st.error("Formato de resultado no válido.")

elif menu == "👤 Gestionar Jugadores":
    st.title("👤 Gestión de Perfiles")
    # Añadir nuevo jugador
    with st.expander("➕ Añadir Nuevo Jugador"):
        nuevo_n = st.text_input("Nombre completo")
        nueva_f = st.text_input("URL de la Foto", value="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        if st.button("Crear Jugador"):
            if nuevo_n and nuevo_n not in st.session_state.jugadores:
                st.session_state.jugadores[nuevo_n] = {"puntos": 0, "foto": nueva_f, "pp": 0, "pg": 0, "pp_perd": 0, "sg": 0, "sp": 0, "gg": 0, "gp": 0}
                st.success(f"{nuevo_n} añadido.")
                st.rerun()

    # Editar fotos existentes
    st.subheader("Editar Fotos Actuales")
    for j in st.session_state.jugadores:
        col_n, col_img = st.columns([3, 1])
        nueva_url = col_n.text_input(f"URL Foto de {j}", value=st.session_state.jugadores[j]["foto"], key=f"foto_{j}")
        st.session_state.jugadores[j]["foto"] = nueva_url
        col_img.image(nueva_url, width=50)
