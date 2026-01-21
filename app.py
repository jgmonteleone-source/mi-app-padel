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
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        jugadores['Foto'] = jugadores['Foto'].astype(str).str.strip()
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FUNCIÓN DE FILTRADO ---
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

# --- VENTANA FLOTANTE (MODAL) PARA ESTADÍSTICAS ---
@st.dialog("📊 Estadísticas Personales")
def mostrar_perfil(nombre_jugador, df_jugadores):
    datos = df_jugadores[df_jugadores['Nombre'] == nombre_jugador].iloc[0]
    col1, col2 = st.columns(2)
    col1.metric("Victorias (PG)", int(datos['PG']))
    col2.metric("Derrotas (PP)", int(datos['PP_perd']))
    
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"**Efectividad: {efect:.1f}%**")
        st.progress(efect / 100)
    st.write(f"Puntos Totales: {int(datos['Puntos'])}")

# --- MENÚ LATERAL (Solo navegación) ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (Cara a Cara)", "📝 Cargar Partido", "👤 Gestionar Jugadores"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    # Filtro dentro del apartado
    rango = st.selectbox("Periodo del Ranking", ["Siempre", "Este año", "Año pasado", "Este mes"], key="filt_rank")
    st.title(f"🏆 Ranking")
    
    if not df_jugadores.empty:
        df_jugadores["Puntos"] = pd.to_numeric(df_jugadores["Puntos"], errors='coerce').fillna(0)
        df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
        
        for i, row in df_rank.iterrows():
            # Columnas ajustadas para que quepan en una sola línea en móvil
            c1, c2, c3, c4 = st.columns([1, 2, 5, 2])
            
            with c1: st.write(f"**#{i+1}**")
            
            with c2:
                url_f = row["Foto"]
                f_final = url_f if (isinstance(url_f, str) and url_f.startswith("http")) else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
                st.image(f_final, width=50) # Ancho menor para asegurar la línea única
                
            with c3:
                if st.button(row['Nombre'], key=f"btn_{row['Nombre']}", use_container_width=True):
                    mostrar_perfil(row['Nombre'], df_jugadores)
            
            with c4: st.write(f"**{int(row['Puntos'])}** pts")
            st.divider()

# --- 2. H2H ---
elif menu == "⚔️ H2H (Cara a Cara)":
    rango_h2h = st.selectbox("Periodo", ["Siempre", "Este año", "Año pasado", "Este mes"], key="filt_h2h")
    st.title("⚔️ Cara a Cara")
    
    df_p_filt = filtrar_por_fecha(df_partidos, rango_h2h)
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=min(1, len(nombres)-1))
    
    if j1 != j2:
        enf = df_p_filt[
            ((df_p_filt['Ganador1'] == j1) | (df_p_filt['Ganador2'] == j1) | (df_p_filt['Perdedor1'] == j1) | (df_p_filt['Perdedor2'] == j1)) &
            ((df_p_filt['Ganador1'] == j2) | (df_p_filt['Ganador2'] == j2) | (df_p_filt['Perdedor1'] == j2) | (df_p_filt['Perdedor2'] == j2))
        ]
        w1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
        w2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
        
        # Salto de línea solicitado
        st.markdown(f"### Historial:")
        st.header(f"{j1} {w1} — {w2} {j2}")
        
        st.table(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']])

# --- 3. CARGAR PARTIDO (Manteniendo tu lógica que funciona) ---
elif menu == "📝 Cargar Partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    with st.form("f_partido"):
        c1, c2, s1, s2, s3 = st.columns([2, 2, 1, 1, 1])
        p1j1, p1j2 = c1.selectbox("P1 J1", nombres), c2.selectbox("P1 J2", nombres)
        p1s1, p1s2, p1s3 = s1.number_input("S1",0,7, key="p1s1"), s2.number_input("S2",0,7, key="p1s2"), s3.number_input("S3",0,7, key="p1s3")
        c1b, c2b, s1b, s2b, s3b = st.columns([2, 2, 1, 1, 1])
        p2j1, p2j2 = c1b.selectbox("P2 J1", nombres), c2b.selectbox("P2 J2", nombres)
        p2s1, p2s2, p2s3 = s1b.number_input("S1",0,7, key="p2s1"), s2b.number_input("S2",0,7, key="p2s2"), s3b.number_input("S3",0,7, key="p2s3")
        
        if st.form_submit_button("GUARDAR PARTIDO"):
            sets1 = (1 if p1s1>p2s1 else 0)+(1 if p1s2>p2s2 else 0)+(1 if p1s3>p2s3 else 0)
            sets2 = (1 if p2s1>p1s1 else 0)+(1 if p2s2>p1s2 else 0)+(1 if p2s3>p1s3 else 0)
            if sets1 != sets2 and len({p1j1, p1j2, p2j1, p2j2}) == 4:
                if sets1 > sets2:
                    gan, perd = [p1j1, p1j2], [p2j1, p2j2]
                    ptg, ptp = (3 if sets2==0 else 2), (1 if sets2==1 else 0)
                else:
                    gan, perd = [p2j1, p2j2], [p1j1, p1j2]
                    ptg, ptp = (3 if sets1==0 else 2), (1 if sets1==1 else 0)
                
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
                st.rerun()

# --- 4. GESTIONAR JUGADORES ---
elif menu == "👤 Gestionar Jugadores":
    st.title("Añadir Jugador")
    with st.form("n_j"):
        nj = st.text_input("Nombre")
        fj = st.text_input("URL Foto")
        if st.form_submit_button("Registrar"):
            df_n = pd.DataFrame([{"Nombre": nj, "Foto": fj, "Puntos": 0, "PG": 0, "PP": 0, "PP_perd": 0, "SG": 0, "SP": 0, "GG": 0, "GP": 0}])
            conn.update(worksheet="Jugadores", data=pd.concat([df_jugadores, df_n], ignore_index=True))
            st.cache_data.clear()
            st.rerun()
