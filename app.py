import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        # Convertir fecha a objeto datetime
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FILTROS ---
st.sidebar.title("🏸 Padel Pro v2")
rango = st.sidebar.selectbox("Periodo del Ranking", ["Siempre", "Este año", "Año pasado", "Este mes"])

def filtrar_por_fecha(df, opcion):
    hoy = datetime.now()
    if df.empty: return df
    if opcion == "Este año":
        return df[df['Fecha'].dt.year == hoy.year]
    elif opcion == "Año pasado":
        return df[df['Fecha'].dt.year == hoy.year - 1]
    elif opcion == "Este mes":
        return df[(df['Fecha'].dt.year == hoy.year) & (df['Fecha'].dt.month == hoy.month)]
    return df

df_partidos_filt = filtrar_por_fecha(df_partidos, rango)

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H", "📝 Cargar Partido", "👤 Jugadores"])

if menu == "🏆 Ranking":
    st.title(f"🏆 Ranking - {rango}")
    
    # Calcular puntos dinámicos según el filtro
    # Si es "Siempre" usamos la columna Puntos, si no, calculamos desde partidos
    df_rank = df_jugadores.copy()
    
    # Aseguramos que las fotos sean strings limpios
    df_rank['Foto'] = df_rank['Foto'].astype(str).str.strip()

    for i, row in df_rank.sort_values(by="Puntos", ascending=False).reset_index(drop=True).iterrows():
        with st.container():
            c1, c2, c3, c4 = st.columns([0.5, 1, 4, 1.5])
            c1.subheader(f"#{i+1}")
            
            # GESTIÓN DE IMAGEN (PROTECCIÓN TOTAL)
            url_foto = row["Foto"]
            if url_foto.startswith("http"):
                c2.image(url_foto, width=80)
            else:
                c2.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
            
            # NAVEGACIÓN A PERFIL
            if c3.button(f"**{row['Nombre']}**", key=f"rank_{row['Nombre']}"):
                st.session_state.perfil = row['Nombre']
                st.rerun()
                
            c4.subheader(f"{int(row['Puntos'])} pts")
            st.divider()

    # FICHA DEL JUGADOR (Aparece al hacer clic)
    if 'perfil' in st.session_state:
        st.sidebar.divider()
        st.sidebar.subheader(f"📊 Ficha: {st.session_state.perfil}")
        p = df_jugadores[df_jugadores['Nombre'] == st.session_state.perfil].iloc[0]
        
        col_a, col_b = st.sidebar.columns(2)
        col_a.metric("Ganados", int(p['PG']))
        col_b.metric("Perdidos", int(p['PP_perd']))
        
        # % de victorias
        total = int(p['PG']) + int(p['PP_perd'])
        efectividad = (int(p['PG']) / total * 100) if total > 0 else 0
        st.sidebar.progress(efectividad / 100)
        st.sidebar.write(f"Efectividad: {efectividad:.1f}%")
        
        if st.sidebar.button("Cerrar Ficha"):
            del st.session_state.perfil
            st.rerun()

elif menu == "⚔️ H2H":
    st.title("⚔️ Cara a Cara")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    col1, col2 = st.columns(2)
    j1 = col1.selectbox("Jugador 1", nombres, index=0)
    j2 = col2.selectbox("Jugador 2", nombres, index=1)
    
    enf = df_partidos_filt[
        ((df_partidos_filt['Ganador1'] == j1) | (df_partidos_filt['Ganador2'] == j1) | (df_partidos_filt['Perdedor1'] == j1) | (df_partidos_filt['Perdedor2'] == j1)) &
        ((df_partidos_filt['Ganador1'] == j2) | (df_partidos_filt['Ganador2'] == j2) | (df_partidos_filt['Perdedor1'] == j2) | (df_partidos_filt['Perdedor2'] == j2))
    ]
    
    v1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
    v2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
    
    st.header(f"Resultado: {j1} {v1} - {v2} {j2}")
    st.dataframe(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']], use_container_width=True)

elif menu == "📝 Cargar Partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("registro_final"):
        c1, c2, s1, s2, s3 = st.columns([2, 2, 1, 1, 1])
        p1j1 = c1.selectbox("P1 - Jugador 1", nombres)
        p1j2 = c2.selectbox("P1 - Jugador 2", nombres)
        p1s1, p1s2, p1s3 = s1.number_input("S1", 0, 7, key="p1s1"), s2.number_input("S2", 0, 7, key="p1s2"), s3.number_input("S3", 0, 7, key="p1s3")
        
        c1b, c2b, s1b, s2b, s3b = st.columns([2, 2, 1, 1, 1])
        p2j1 = c1b.selectbox("P2 - Jugador 1", nombres)
        p2j2 = c2b.selectbox("P2 - Jugador 2", nombres)
        p2s1, p2s2, p2s3 = s1b.number_input("S1", 0, 7, key="p2s1"), s2b.number_input("S2", 0, 7, key="p2s2"), s3b.number_input("S3", 0, 7, key="p2s3")
        
        if st.form_submit_button("💾 GUARDAR RESULTADO"):
            # Lógica de sets
            sets_p1 = (1 if p1s1 > p2s1 else 0) + (1 if p1s2 > p2s2 else 0) + (1 if p1s3 > p2s3 else 0)
            sets_p2 = (1 if p2s1 > p1s1 else 0) + (1 if p2s2 > p1s2 else 0) + (1 if p2s3 > p1s3 else 0)
            
            if sets_p1 == sets_p2 or len({p1j1, p1j2, p2j1, p2j2}) < 4:
                st.error("Revisa los datos (empate o jugadores repetidos)")
            else:
                if sets_p1 > sets_p2:
                    gan, perd = [p1j1, p1j2], [p2j1, p2j2]
                    pt_g, pt_p = (3 if sets_p2 == 0 else 2), (1 if sets_p2 == 1 else 0)
                else:
                    gan, perd = [p2j1, p2j2], [p1j1, p1j2]
                    pt_g, pt_p = (3 if sets_p1 == 0 else 2), (1 if sets_p1 == 1 else 0)

                # Actualización de Jugadores
                df_jugadores['Puntos'] = pd.to_numeric(df_jugadores['Puntos'], errors='coerce').fillna(0)
                for j in gan:
                    idx = df_jugadores.index[df_jugadores['Nombre'] == j][0]
                    df_jugadores.at[idx, 'Puntos'] += pt_g
                    df_jugadores.at[idx, 'PG'] += 1
                for j in perd:
                    idx = df_jugadores.index[df_jugadores['Nombre'] == j][0]
                    df_jugadores.at[idx, 'Puntos'] += pt_p
                    df_jugadores.at[idx, 'PP_perd'] += 1
                
                # Guardar
                res = f"{p1s1}-{p2s1}, {p1s2}-{p2s2}" + (f", {p1s3}-{p2s3}" if (p1s3+p2s3)>0 else "")
                n_f = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "Ganador1": gan[0], "Ganador2": gan[1], "Perdedor1": perd[0], "Perdedor2": perd[1], "Resultado": res}])
                
                conn.update(worksheet="Partidos", data=pd.concat([df_partidos, n_f], ignore_index=True))
                conn.update(worksheet="Jugadores", data=df_jugadores)
                st.cache_data.clear()
                st.success("¡Partido Guardado!")
                st.rerun()

elif menu == "👤 Jugadores":
    st.title("Gestión de Jugadores")
    nom = st.text_input("Nombre del nuevo jugador")
    fot = st.text_input("URL de la foto")
    if st.button("Crear Jugador"):
        n_j = pd.DataFrame([{"Nombre": nom, "Foto": fot, "Puntos": 0, "PG": 0, "PP": 0, "PP_perd": 0, "SG": 0, "SP": 0, "GG": 0, "GP": 0}])
        conn.update(worksheet="Jugadores", data=pd.concat([df_jugadores, n_j], ignore_index=True))
        st.cache_data.clear()
        st.rerun()
