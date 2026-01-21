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
        
        # Convertir a fecha real
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        
        # Limpieza de textos
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        jugadores['Foto'] = jugadores['Foto'].astype(str).str.strip()
        
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error al conectar: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FILTROS TEMPORALES ---
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
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (Cara a Cara)", "📝 Cargar Partido", "👤 Gestionar Jugadores"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.title(f"🏆 Ranking - {rango}")
    
    if not df_jugadores.empty:
        # Puntos a número y ordenado
        df_jugadores["Puntos"] = pd.to_numeric(df_jugadores["Puntos"], errors='coerce').fillna(0)
        df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
        
        for i, row in df_rank.iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([0.5, 1, 4, 1.5])
                c1.subheader(f"#{i+1}")
                
                # Gestión de imagen
                url_f = row["Foto"]
                f_final = url_f if url_f.startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
                c2.image(f_final, width=80)
                
                # Nombre y botón perfil
                if c3.button(f"**{row['Nombre']}**", key=f"rank_{row['Nombre']}"):
                    st.session_state.p_id = row['Nombre']
                    st.rerun()
                
                c4.subheader(f"{int(row['Puntos'])} pts")
                st.divider()

        # Ficha lateral
        if 'p_id' in st.session_state:
            st.sidebar.divider()
            st.sidebar.subheader(f"📊 Ficha: {st.session_state.p_id}")
            d = df_jugadores[df_jugadores['Nombre'] == st.session_state.p_id].iloc[0]
            ca, cb = st.sidebar.columns(2)
            ca.metric("PG", int(d['PG']))
            cb.metric("PP", int(d['PP_perd']))
            
            t = int(d['PG']) + int(d['PP_perd'])
            if t > 0:
                ef = (int(d['PG']) / t) * 100
                st.sidebar.write(f"Efectividad: {ef:.1f}%")
                st.sidebar.progress(ef / 100)
            
            if st.sidebar.button("Cerrar Ficha"):
                del st.session_state.p_id
                st.rerun()

# --- 2. H2H ---
elif menu == "⚔️ H2H (Cara a Cara)":
    st.title(f"⚔️ H2H - {rango}")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=min(1, len(nombres)-1))
    
    if j1 != j2:
        enf = df_partidos_filt[
            ((df_partidos_filt['Ganador1'] == j1) | (df_partidos_filt['Ganador2'] == j1) | (df_partidos_filt['Perdedor1'] == j1) | (df_partidos_filt['Perdedor2'] == j1)) &
            ((df_partidos_filt['Ganador1'] == j2) | (df_partidos_filt['Ganador2'] == j2) | (df_partidos_filt['Perdedor1'] == j2) | (df_partidos_filt['Perdedor2'] == j2))
        ]
        w1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
        w2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
        st.header(f"Historial: {j1} {w1} - {w2} {j2}")
        st.table(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']])

# --- 3. CARGAR PARTIDO ---
elif menu == "📝 Cargar Partido":
    st.title("📝 Cargar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    with st.form("f_partido"):
        c1, c2, s1, s2, s3 = st.columns([2, 2, 1, 1, 1])
        p1j1, p1j2 = c1.selectbox("P1 J1", nombres), c2.selectbox("P1 J2", nombres)
        p1s1, p1s2, p1s3 = s1.number_input("S1",0,7), s2.number_input("S2",0,7), s3.number_input("S3",0,7)
        
        c1b, c2b, s1b, s2b, s3b = st.columns([2, 2, 1, 1, 1])
        p2j1, p2j2 = c1b.selectbox("P2 J1", nombres), c2b.selectbox("P2 J2", nombres)
        p2s1, p2s2, p2s3 = s1b.number_input("S1",0,7, key="p2s1"), s2b.number_input("S2",0,7, key="p2s2"), s3b.number_input("S3",0,7, key="p2s3")
        
        if st.form_submit_button("GUARDAR"):
            sets1 = (1 if p1s1>p2s1 else 0)+(1 if p1s2>p2s2 else 0)+(1 if p1s3>p2s3 else 0)
            sets2 = (1 if p2s1>p1s1 else 0)+(1 if p2s2>p1s2 else 0)+(1 if p2s3>p1s3 else 0)
            
            if sets1 != sets2 and len({p1j1, p1j2, p2j1, p2j2}) == 4:
                if sets1 > sets2:
                    gan, perd = [p1j1, p1j2], [p2j1, p2j2]
                    ptg, ptp = (3 if sets2==0 else 2), (1 if sets2==1 else 0)
                else:
                    gan, perd = [p2j1, p2j2], [p1j1, p1j2]
                    ptg, ptp = (3 if sets1==0 else 2), (1 if sets1==1 else 0)
                
                # Actualizar puntos
                for j in gan:
                    idx = df_jugadores.index[df_jugadores['Nombre']==j][0]
                    df_jugadores.at[idx, 'Puntos'] = pd.to_numeric(df_jugadores.at[idx, 'Puntos'], errors='coerce') + ptg
                    df_jugadores.at[idx, 'PG'] = pd.to_numeric(df_jugadores.at[idx, 'PG'], errors='coerce') + 1
                for j in perd:
                    idx = df_jugadores.index[df_jugadores['Nombre']==j][0]
                    df_jugadores.at[idx, 'Puntos'] = pd.to_numeric(df_jugadores.at[idx, 'Puntos'], errors='coerce') + ptp
                    df_jugadores.at[idx, 'PP_perd'] = pd.to_numeric(df_jugadores.at[idx, 'PP_perd'], errors='coerce') + 1

                res = f"{p1s1}-{p2s1}, {p1s2}-{p2s2}" + (f", {p1s3}-{p2s3}" if (p1s3+p2s3)>0 else "")
                n_f = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "Ganador1": gan[0], "Ganador2": gan[1], "Perdedor1": perd[0], "Perdedor2": perd[1], "Resultado": res}])
                
                conn.update(worksheet="Jugadores", data=df_jugadores)
                conn.update(worksheet="Partidos", data=pd.concat([df_partidos, n_f], ignore_index=True))
                st.cache_data.clear()
                st.success("¡Guardado!")
                st.rerun()

# --- 4. GESTIONAR ---
elif menu == "👤 Gestionar Jugadores":
    st.title("Nuevo Jugador")
    with st.form("n_j"):
        nj = st.text_input("Nombre")
        fj = st.text_input("URL Foto")
        if st.form_submit_button("Crear"):
            df_n = pd.DataFrame([{"Nombre": nj, "Foto": fj, "Puntos": 0, "PG": 0, "PP": 0, "PP_perd": 0, "SG": 0, "SP": 0, "GG": 0, "GP": 0}])
            conn.update(worksheet="Jugadores", data=pd.concat([df_jugadores, df_n], ignore_index=True))
            st.cache_data.clear()
            st.rerun()
