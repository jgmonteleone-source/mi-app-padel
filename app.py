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
    
    with st.form("form_partido_definitivo"):
        h_c1, h_c2, h_s1, h_s2, h_s3 = st.columns([2, 2, 0.8, 0.8, 0.8])
        h_c1.write("**Parejas**"); h_s1.write("**S1**"); h_s2.write("**S2**"); h_s3.write("**S3**")
        
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
        
        if st.form_submit_button("💾 GUARDAR PARTIDO Y ACTUALIZAR RANKING", use_container_width=True):
            if len({p1j1, p1j2, p2j1, p2j2}) < 4:
                st.error("Error: Hay jugadores repetidos.")
            else:
                # 1. Cálculo de Sets y Ganador
                sets_p1 = (1 if p1s1 > p2s1 else 0) + (1 if p1s2 > p2s2 else 0) + (1 if p1s3 > p2s3 else 0)
                sets_p2 = (1 if p2s1 > p1s1 else 0) + (1 if p2s2 > p1s2 else 0) + (1 if p2s3 > p1s3 else 0)
                
                if sets_p1 == sets_p2:
                    st.error("El partido no puede quedar en empate.")
                else:
                    # Determinar puntos y estadísticas
                    if sets_p1 > sets_p2:
                        ganadores, perdedores = [p1j1, p1j2], [p2j1, p2j2]
                        pts_g, pts_p = (3 if sets_p2 == 0 else 2), (1 if sets_p2 == 1 else 0)
                        # Stats para ganadores
                        sg_gan, sp_gan, gg_gan, gp_gan = sets_p1, sets_p2, (p1s1+p1s2+p1s3), (p2s1+p2s2+p2s3)
                    else:
                        ganadores, perdedores = [p2j1, p2j2], [p1j1, p1j2]
                        pts_g, pts_p = (3 if sets_p1 == 0 else 2), (1 if sets_p1 == 1 else 0)
                        # Stats para ganadores
                        sg_gan, sp_gan, gg_gan, gp_gan = sets_p2, sets_p1, (p2s1+p2s2+p2s3), (p1s1+p1s2+p1s3)

                    # 2. ACTUALIZACIÓN DE JUGADORES (EL AJUSTE CLAVE)
                    # Limpiamos nombres para evitar errores de coincidencia
                    df_jugadores['Nombre'] = df_jugadores['Nombre'].str.strip()

                    for j in ganadores:
                        idx_list = df_jugadores.index[df_jugadores['Nombre'].str.lower() == j.strip().lower()].tolist()
                        if idx_list:
                            idx = idx_list[0]
                            # Usamos fillna(0) por si la celda de Excel está vacía
                            df_jugadores.at[idx, 'Puntos'] = pd.to_numeric(df_jugadores.at[idx, 'Puntos'], errors='coerce') or 0
                            df_jugadores.at[idx, 'Puntos'] += pts_g
                            df_jugadores.at[idx, 'PG'] = (pd.to_numeric(df_jugadores.at[idx, 'PG'], errors='coerce') or 0) + 1
                            df_jugadores.at[idx, 'PP'] = (pd.to_numeric(df_jugadores.at[idx, 'PP'], errors='coerce') or 0) + 1
                            df_jugadores.at[idx, 'SG'] = (pd.to_numeric(df_jugadores.at[idx, 'SG'], errors='coerce') or 0) + sg_gan
                            df_jugadores.at[idx, 'SP'] = (pd.to_numeric(df_jugadores.at[idx, 'SP'], errors='coerce') or 0) + sp_gan
                            df_jugadores.at[idx, 'GG'] = (pd.to_numeric(df_jugadores.at[idx, 'GG'], errors='coerce') or 0) + gg_gan
                            df_jugadores.at[idx, 'GP'] = (pd.to_numeric(df_jugadores.at[idx, 'GP'], errors='coerce') or 0) + gp_gan

                    for j in perdedores:
                        idx_list = df_jugadores.index[df_jugadores['Nombre'].str.lower() == j.strip().lower()].tolist()
                        if idx_list:
                            idx = idx_list[0]
                            df_jugadores.at[idx, 'Puntos'] = pd.to_numeric(df_jugadores.at[idx, 'Puntos'], errors='coerce') or 0
                            df_jugadores.at[idx, 'Puntos'] += pts_p
                            df_jugadores.at[idx, 'PP_perd'] = (pd.to_numeric(df_jugadores.at[idx, 'PP_perd'], errors='coerce') or 0) + 1
                            df_jugadores.at[idx, 'PP'] = (pd.to_numeric(df_jugadores.at[idx, 'PP'], errors='coerce') or 0) + 1
                            df_jugadores.at[idx, 'SG'] = (pd.to_numeric(df_jugadores.at[idx, 'SG'], errors='coerce') or 0) + sp_gan # Sus ganados son los perdidos del otro
                            df_jugadores.at[idx, 'SP'] = (pd.to_numeric(df_jugadores.at[idx, 'SP'], errors='coerce') or 0) + sg_gan
                            df_jugadores.at[idx, 'GG'] = (pd.to_numeric(df_jugadores.at[idx, 'GG'], errors='coerce') or 0) + gp_gan
                            df_jugadores.at[idx, 'GP'] = (pd.to_numeric(df_jugadores.at[idx, 'GP'], errors='coerce') or 0) + gg_gan

                    # 3. Guardar en Partidos
                    res_str = f"{p1s1}-{p2s1}, {p1s2}-{p2s2}" + (f", {p1s3}-{p2s3}" if (p1s3+p2s3)>0 else "")
                    nueva_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "Ganador1": ganadores[0], "Ganador2": ganadores[1], "Perdedor1": perdedores[0], "Perdedor2": perdedores[1], "Resultado": res_str}])
                    df_partidos_upd = pd.concat([df_partidos, nueva_fila], ignore_index=True)

                    # 4. SUBIR A GOOGLE SHEETS
                    conn.update(worksheet="Partidos", data=df_partidos_upd)
                    conn.update(worksheet="Jugadores", data=df_jugadores)
                    
                    st.success("✅ ¡Base de datos actualizada!")
                    st.balloons()
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
