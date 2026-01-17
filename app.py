import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Función para cargar datos frescos
def cargar_datos():
    jugadores_df = conn.read(worksheet="Jugadores", ttl="0")
    partidos_df = conn.read(worksheet="Partidos", ttl="0")
    return jugadores_df, partidos_df

df_jugadores, df_partidos = cargar_datos()

# --- ESTILOS CSS ---
st.markdown("""
    <style>
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #e0e0e0; }
    [data-testid="stMetricValue"] { color: #1f77b4; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["🏆 Ranking", "⚔️ Cara a Cara (H2H)", "📝 Cargar Partido", "👤 Gestionar Jugadores"])

if menu == "🏆 Ranking":
    st.title("🏆 Clasificación General")
    
    # Ordenar por puntos
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False)
    
    for i, row in df_rank.iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([0.5, 1, 4, 1.5])
            c1.subheader(f"#{i+1 if 'i' in locals() else ''}") # Posición aproximada
            c2.image(row["Foto"], width=60)
            if c3.button(f"**{row['Nombre']}**", key=f"btn_{row['Nombre']}"):
                st.session_state.ver_jugador = row['Nombre']
            c4.subheader(f"{row['Puntos']} pts")
            st.divider()

    # Detalle del Jugador en la barra lateral
    if "ver_jugador" in st.session_state:
        nombre_sel = st.session_state.ver_jugador
        d = df_jugadores[df_jugadores["Nombre"] == nombre_sel].iloc[0]
        
        st.sidebar.image(d["Foto"], width=150)
        st.sidebar.title(d["Nombre"])
        st.sidebar.metric("Partidos Jugados (PP)", int(d['PP']))
        st.sidebar.write(f"✅ Ganados: {int(d['PG'])} | ❌ Perdidos: {int(d['PP_perd'])}")
        
        st.sidebar.subheader("Sets")
        st.sidebar.write(f"Ganados: {int(d['SG'])} | Perdidos: {int(d['SP'])}")
        
        st.sidebar.subheader("Games")
        st.sidebar.write(f"Ganados: {int(d['GG'])} | Perdidos: {int(d['GP'])}")
        
        if st.sidebar.button("Cerrar Detalle"):
            del st.session_state.ver_jugador
            st.rerun()

elif menu == "⚔️ Cara a Cara (H2H)":
    st.title("⚔️ Cara a Cara (H2H)")
    nombres_lista = df_jugadores["Nombre"].tolist()
    
    col1, col2 = st.columns(2)
    j_a = col1.selectbox("Jugador A", nombres_lista)
    j_b = col2.selectbox("Jugador B", nombres_lista, index=min(1, len(nombres_lista)-1))
    
    if j_a != j_b:
        # Filtrar partidos donde ambos jugaron (uno contra otro o juntos)
        enf = df_partidos[
            ((df_partidos['Ganador1'] == j_a) | (df_partidos['Ganador2'] == j_a) | (df_partidos['Perdedor1'] == j_a) | (df_partidos['Perdedor2'] == j_a)) &
            ((df_partidos['Ganador1'] == j_b) | (df_partidos['Ganador2'] == j_b) | (df_partidos['Perdedor1'] == j_b) | (df_partidos['Perdedor2'] == j_b))
        ]
        
        v_a = len(enf[(enf['Ganador1'] == j_a) | (enf['Ganador2'] == j_a)])
        v_b = len(enf[(enf['Ganador1'] == j_b) | (enf['Ganador2'] == j_b)])
        
        st.header(f"Historial Directo: {j_a} {v_a} - {v_b} {j_b}")
        if not enf.empty:
            st.dataframe(enf[["Fecha", "Ganador1", "Ganador2", "Perdedor1", "Perdedor2", "Resultado"]], use_container_width=True)
        else:
            st.info("No hay enfrentamientos registrados entre estos jugadores.")

elif menu == "📝 Cargar Partido":
    st.title("📝 Registrar Nuevo Partido")
    nombres_lista = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("form_partido"):
        h_c1, h_c2, h_s1, h_s2, h_s3 = st.columns([2, 2, 0.8, 0.8, 0.8])
        h_c1.write("**Parejas**")
        h_s1.write("**S1**"); h_s2.write("**S2**"); h_s3.write("**S3**")
        
        # Fila Pareja 1
        r1_c1, r1_c2, r1_s1, r1_s2, r1_s3 = st.columns([2, 2, 0.8, 0.8, 0.8])
        p1j1 = r1_c1.selectbox("P1J1", nombres_lista, key="p1j1", label_visibility="collapsed")
        p1j2 = r1_c2.selectbox("P1J2", nombres_lista, key="p1j2", label_visibility="collapsed")
        p1s1 = r1_s1.number_input("P1S1", 0, 7, key="p1s1", label_visibility="collapsed")
        p1s2 = r1_s2.number_input("P1S2", 0, 7, key="p1s2", label_visibility="collapsed")
        p1s3 = r1_s3.number_input("P1S3", 0, 7, key="p1s3", label_visibility="collapsed")
        
        st.divider()
        
        # Fila Pareja 2
        r2_c1, r2_c2, r2_s1, r2_s2, r2_s3 = st.columns([2, 2, 0.8, 0.8, 0.8])
        p2j1 = r2_c1.selectbox("P2J1", nombres_lista, key="p2j1", label_visibility="collapsed")
        p2j2 = r2_c2.selectbox("P2J2", nombres_lista, key="p2j2", label_visibility="collapsed")
        p2s1 = r2_s1.number_input("P2S1", 0, 7, key="p2s1", label_visibility="collapsed")
        p2s2 = r2_s2.number_input("P2S2", 0, 7, key="p2s2", label_visibility="collapsed")
        p2s3 = r2_s3.number_input("P2S3", 0, 7, key="p2s3", label_visibility="collapsed")
        
        if st.form_submit_button("💾 GUARDAR PARTIDO EN LA NUBE", use_container_width=True):
            jugadores_set = {p1j1, p1j2, p2j1, p2j2}
            if len(jugadores_set) < 4:
                st.error("Error: Hay jugadores repetidos.")
            else:
                # Calcular ganador
                s_p1 = (1 if p1s1 > p2s1 else 0) + (1 if p1s2 > p2s2 else 0) + (1 if p1s3 > p2s3 else 0)
                s_p2 = (1 if p2s1 > p1s1 else 0) + (1 if p2s2 > p1s2 else 0) + (1 if p2s3 > p1s3 else 0)
                
                if s_p1 == s_p2:
                    st.error("El partido no puede quedar en empate.")
                else:
                    # Preparar fila para GSheets
                    score_final = f"{p1s1}-{p2s1}, {p1s2}-{p2s2}" + (f", {p1s3}-{p2s3}" if (p1s3+p2s3)>0 else "")
                    ganadores = [p1j1, p1j2] if s_p1 > s_p2 else [p2j1, p2j2]
                    perdedores = [p2j1, p2j2] if s_p1 > s_p2 else [p1j1, p1j2]
                    
                    nueva_fila = pd.DataFrame([{
                        "Fecha": datetime.now().strftime("%d/%m/%Y"),
                        "Ganador1": ganadores[0], "Ganador2": ganadores[1],
                        "Perdedor1": perdedores[0], "Perdedor2": perdedores[1],
                        "Resultado": score_final
                    }])
                    
                    # ACTUALIZAR GOOGLE SHEETS
                    df_partidos_new = pd.concat([df_partidos, nueva_fila], ignore_index=True)
                    
                    # Lógica de puntos para actualizar la tabla de jugadores
                    pts_g = 3 if (s_p1 == 2 and s_p2 == 0) or (s_p2 == 2 and s_p1 == 0) else 2
                    pts_p = 1 if (s_p1 + s_p2 == 3) else 0
                    
                    # Actualizamos el DataFrame de jugadores localmente antes de subirlo
                    for j in ganadores:
                        idx = df_jugadores.index[df_jugadores['Nombre'] == j][0]
                        df_jugadores.at[idx, 'Puntos'] += pts_g
                        df_jugadores.at[idx, 'PG'] += 1
                        df_jugadores.at[idx, 'PP'] += 1
                        # (Aquí podrías añadir el resto de SG, GG, etc. siguiendo la misma lógica)
                        
                    for j in perdedores:
                        idx = df_jugadores.index[df_jugadores['Nombre'] == j][0]
                        df_jugadores.at[idx, 'Puntos'] += pts_p
                        df_jugadores.at[idx, 'PP_perd'] += 1
                        df_jugadores.at[idx, 'PP'] += 1

                    # Subir cambios
                    conn.update(worksheet="Partidos", data=df_partidos_new)
                    conn.update(worksheet="Jugadores", data=df_jugadores)
                    
                    st.success("¡Partido guardado con éxito en Google Sheets!")
                    st.balloons()

elif menu == "👤 Gestionar Jugadores":
    st.title("Gestión de Jugadores")
    # Formulario para añadir nuevo
    with st.expander("Añadir nuevo jugador"):
        nombre_n = st.text_input("Nombre")
        foto_n = st.text_input("URL Foto", value="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        if st.button("Crear"):
            nueva_j = pd.DataFrame([{"Nombre": nombre_n, "Foto": foto_n, "Puntos": 0, "PP": 0, "PG": 0, "PP_perd": 0, "SG": 0, "SP": 0, "GG": 0, "GP": 0}])
            df_final = pd.concat([df_jugadores, nueva_j], ignore_index=True)
            conn.update(worksheet="Jugadores", data=df_final)
            st.success("Jugador creado.")
            st.rerun()
