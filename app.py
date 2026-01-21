import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60) # Cache de 1 minuto para evitar el error de cuota (429)
def cargar_datos():
    try:
        # Leemos las pestañas asegurando que carguen datos frescos si es necesario
        jugadores = conn.read(worksheet="Jugadores")
        partidos = conn.read(worksheet="Partidos")
        # Limpieza básica: quitar filas vacías y asegurar tipos numéricos
        jugadores = jugadores.dropna(subset=["Nombre"])
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ PRINCIPAL", ["🏆 Ranking", "⚔️ Cara a Cara (H2H)", "📝 Cargar Partido", "👤 Gestionar Jugadores"])

if menu == "🏆 Ranking":
    st.title("🏆 Clasificación General")
    
    if not df_jugadores.empty:
        # Aseguramos que Puntos sea numérico para ordenar bien
        df_jugadores["Puntos"] = pd.to_numeric(df_jugadores["Puntos"], errors='coerce').fillna(0)
        df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
        
        for i, row in df_rank.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([0.5, 1, 4, 1.5])
                c1.subheader(f"#{i+1}")
                
                # Validación de imagen para evitar el error AttributeError
                foto_url = row["Foto"] if pd.notnull(row["Foto"]) and str(row["Foto"]).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
                c2.image(foto_url, width=60)
                
                c3.subheader(row["Nombre"])
                c4.subheader(f"{int(row['Puntos'])} pts")
                st.divider()
    else:
        st.info("No hay jugadores registrados.")

elif menu == "⚔️ Cara a Cara (H2H)":
    st.title("⚔️ Cara a Cara (H2H)")
    if not df_jugadores.empty:
        nombres = sorted(df_jugadores["Nombre"].tolist())
        col1, col2 = st.columns(2)
        j_a = col1.selectbox("Jugador A", nombres)
        j_b = col2.selectbox("Jugador B", nombres, index=min(1, len(nombres)-1))
        
        if j_a != j_b:
            enf = df_partidos[
                ((df_partidos['Ganador1'] == j_a) | (df_partidos['Ganador2'] == j_a) | (df_partidos['Perdedor1'] == j_a) | (df_partidos['Perdedor2'] == j_a)) &
                ((df_partidos['Ganador1'] == j_b) | (df_partidos['Ganador2'] == j_b) | (df_partidos['Perdedor1'] == j_b) | (df_partidos['Perdedor2'] == j_b))
            ]
            v_a = len(enf[(enf['Ganador1'] == j_a) | (enf['Ganador2'] == j_a)])
            v_b = len(enf[(enf['Ganador1'] == j_b) | (enf['Ganador2'] == j_b)])
            st.header(f"Historial: {j_a} {v_a} - {v_b} {j_b}")
            st.dataframe(enf, use_container_width=True)

elif menu == "📝 Cargar Partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("form_registro"):
        c1, c2, s1, s2, s3 = st.columns([2, 2, 1, 1, 1])
        p1j1 = c1.selectbox("Pareja 1 - J1", nombres)
        p1j2 = c2.selectbox("Pareja 1 - J2", nombres)
        p1s1 = s1.number_input("P1 S1", 0, 7)
        p1s2 = s2.number_input("P1 S2", 0, 7)
        p1s3 = s3.number_input("P1 S3", 0, 7)
        
        c1b, c2b, s1b, s2b, s3b = st.columns([2, 2, 1, 1, 1])
        p2j1 = c1b.selectbox("Pareja 2 - J1", nombres)
        p2j2 = c2b.selectbox("Pareja 2 - J2", nombres)
        p2s1 = s1b.number_input("P2 S1", 0, 7)
        p2s2 = s2b.number_input("P2 S2", 0, 7)
        p2s3 = s3b.number_input("P2 S3", 0, 7)
        
        enviar = st.form_submit_button("💾 GUARDAR Y ACTUALIZAR")
        
        if enviar:
            if len({p1j1, p1j2, p2j1, p2j2}) < 4:
                st.error("Hay jugadores repetidos.")
            else:
                # Lógica de Sets
                sets_p1 = (1 if p1s1 > p2s1 else 0) + (1 if p1s2 > p2s2 else 0) + (1 if p1s3 > p2s3 else 0)
                sets_p2 = (1 if p2s1 > p1s1 else 0) + (1 if p2s2 > p1s2 else 0) + (1 if p2s3 > p1s3 else 0)
                
                if sets_p1 == sets_p2:
                    st.error("No puede haber empate en sets.")
                else:
                    # Puntos y Ganadores
                    if sets_p1 > sets_p2:
                        gan, perd = [p1j1, p1j2], [p2j1, p2j2]
                        pt_g, pt_p = (3 if sets_p2 == 0 else 2), (1 if sets_p2 == 1 else 0)
                    else:
                        gan, perd = [p2j1, p2j2], [p1j1, p1j2]
                        pt_g, pt_p = (3 if sets_p1 == 0 else 2), (1 if sets_p1 == 1 else 0)

                    # Actualizar DataFrame Jugadores
                    for j in gan:
                        idx = df_jugadores.index[df_jugadores['Nombre'] == j][0]
                        df_jugadores.at[idx, 'Puntos'] = pd.to_numeric(df_jugadores.at[idx, 'Puntos'], errors='coerce') + pt_g
                        df_jugadores.at[idx, 'PG'] = pd.to_numeric(df_jugadores.at[idx, 'PG'], errors='coerce') + 1
                        df_jugadores.at[idx, 'PP'] = pd.to_numeric(df_jugadores.at[idx, 'PP'], errors='coerce') + 1
                    for j in perd:
                        idx = df_jugadores.index[df_jugadores['Nombre'] == j][0]
                        df_jugadores.at[idx, 'Puntos'] = pd.to_numeric(df_jugadores.at[idx, 'Puntos'], errors='coerce') + pt_p
                        df_jugadores.at[idx, 'PP_perd'] = pd.to_numeric(df_jugadores.at[idx, 'PP_perd'], errors='coerce') + 1
                        df_jugadores.at[idx, 'PP'] = pd.to_numeric(df_jugadores.at[idx, 'PP'], errors='coerce') + 1
                    
                    # Nuevo partido
                    res = f"{p1s1}-{p2s1}, {p1s2}-{p2s2}" + (f", {p1s3}-{p2s3}" if (p1s3+p2s3)>0 else "")
                    n_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "Ganador1": gan[0], "Ganador2": gan[1], "Perdedor1": perd[0], "Perdedor2": perd[1], "Resultado": res}])
                    
                    # Guardar
                    # --- ESTE ES EL BLOQUE QUE DEBES SUSTITUIR ---
                    
                    # 3. Preparar los datos para subir (Orden exacto de tu Excel)
                    orden_columnas = ["Nombre", "Foto", "Puntos", "PP", "PG", "PP_perd", "SG", "SP", "GG", "GP"]
                    
                    # Nos aseguramos de que todas las columnas existan en el DataFrame antes de filtrar
                    for col in orden_columnas:
                        if col not in df_jugadores.columns:
                            df_jugadores[col] = 0
                    
                    df_jugadores_subir = df_jugadores[orden_columnas]

                    # 4. SUBIR A GOOGLE SHEETS
                    try:
                        # Primero intentamos actualizar Jugadores
                        conn.update(worksheet="Jugadores", data=df_jugadores_subir)
                        
                        # Luego actualizamos Partidos
                        res = f"{p1s1}-{p2s1}, {p1s2}-{p2s2}" + (f", {p1s3}-{p2s3}" if (p1s3+p2s3)>0 else "")
                        n_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "Ganador1": gan[0], "Ganador2": gan[1], "Perdedor1": perd[0], "Perdedor2": perd[1], "Resultado": res}])
                        df_partidos_upd = pd.concat([df_partidos, n_fila], ignore_index=True)
                        
                        conn.update(worksheet="Partidos", data=df_partidos_upd)
                        
                        st.cache_data.clear() # Limpia la memoria para ver los cambios
                        st.success("✅ ¡Base de datos y Ranking actualizados con éxito!")
                        st.balloons()
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error al intentar escribir en Google Sheets: {e}")
                    
                    st.cache_data.clear()
                    st.success("✅ ¡Actualizado!")
                    st.rerun()

elif menu == "👤 Gestionar Jugadores":
    st.title("Añadir Jugador")
    with st.form("nuevo_j"):
        nom = st.text_input("Nombre")
        fot = st.text_input("URL Foto (opcional)")
        if st.form_submit_button("Crear"):
            n_j = pd.DataFrame([{"Nombre": nom, "Foto": fot, "Puntos": 0, "PP": 0, "PG": 0, "PP_perd": 0, "SG": 0, "SP": 0, "GG": 0, "GP": 0}])
            conn.update(worksheet="Jugadores", data=pd.concat([df_jugadores, n_j], ignore_index=True))
            st.cache_data.clear()
            st.rerun()
