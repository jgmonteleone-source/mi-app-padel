import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS PARA EL RANKING (TABLA NO APILABLE) ---
st.markdown("""
    <style>
    .ranking-container {
        display: flex;
        align-items: center;
        padding: 10px 0;
        border-bottom: 1px solid #ddd;
    }
    .col-puesto { width: 10%; font-weight: bold; }
    .col-foto { width: 15%; }
    .col-nombre { width: 55%; text-align: left; }
    .col-puntos { width: 20%; text-align: right; font-weight: bold; }
    .img-perfil { border-radius: 50%; object-fit: cover; width: 40px; height: 40px; }
    /* Botones que parecen links */
    .stButton > button {
        border: none;
        background: transparent;
        color: #007bff;
        padding: 0;
        font-weight: bold;
        text-align: left;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=60)
def cargar_datos():
    try:
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        jugadores['Foto'] = jugadores['Foto'].astype(str).str.strip().str.replace(r'[\\"\']', '', regex=True)
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FUNCIÓN FILTRADO ---
def filtrar_por_fecha(df, opcion):
    hoy = datetime.now()
    if df.empty: return df
    if opcion == "Este año":
        return df[df['Fecha'].dt.year == hoy.year]
    elif opcion == "Año pasado":
        return df[df['Fecha'].dt.year == hoy.year - 1]
    elif opcion == "Este mes":
        return df[(df['Fecha'].dt.year == hoy.year) & (df['Fecha'].dt.month == hoy.month)]
    elif opcion == "Mes pasado":
        primero_este_mes = hoy.replace(day=1)
        ultimo_mes_pasado = primero_este_mes - timedelta(days=1)
        return df[(df['Fecha'].dt.year == ultimo_mes_pasado.year) & (df['Fecha'].dt.month == ultimo_mes_pasado.month)]
    return df

# --- FICHA TÉCNICA (MODAL) ---
@st.dialog("📊 Ficha Técnica")
def mostrar_perfil(nombre_jugador, df_jugadores):
    df_temp = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    try:
        posicion = df_temp[df_temp['Nombre'] == nombre_jugador].index[0] + 1
        datos = df_temp[df_temp['Nombre'] == nombre_jugador].iloc[0]
    except:
        st.error("Jugador no encontrado")
        return

    st.markdown(f"## 👤 {nombre_jugador}")
    st.markdown(f"### 🏆 Posición Ranking: #{posicion}")
    st.markdown(f"### ⭐ Puntos: {int(datos['Puntos'])}")
    st.divider()
    st.write(f"✅ **Ganados:** {int(datos['PG'])}")
    st.write(f"❌ **Perdidos:** {int(datos['PP_perd'])}")
    st.write(f"🎾 **Sets ganados:** {int(datos['SG'])}")
    st.write(f"🎾 **Sets perdidos:** {int(datos['SP'])}")
    
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"📈 **Efectividad:** {efect:.1f}%")
        st.progress(efect / 100)
    else:
        st.write("📈 **Efectividad: 0%**")

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (cara a cara)", "📝 Cargar partido", "🔍 Buscar jugador", "👤 Gestionar Jugadores"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    rango = st.selectbox("Periodo", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"])
    st.title("🏆 Ranking")
    
    df_jugadores["Puntos"] = pd.to_numeric(df_jugadores["Puntos"], errors='coerce').fillna(0)
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        # Estructura manual para evitar el apilamiento de Streamlit
        c1, c2, c3, c4 = st.columns([1, 1.5, 5, 2])
        with c1: st.markdown(f"<div style='padding-top:10px'>#{i+1}</div>", unsafe_allow_html=True)
        with c2:
            img = row['Foto'] if row['Foto'].startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            st.image(img, width=40)
        with c3:
            # Botón que actúa como link alineado a la izquierda
            if st.button(row['Nombre'], key=f"rank_{row['Nombre']}"):
                mostrar_perfil(row['Nombre'], df_jugadores)
        with c4: 
            st.markdown(f"<div style='padding-top:10px; text-align:right'><b>{int(row['Puntos'])}</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:0; padding:0; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

# --- 2. H2H ---
elif menu == "⚔️ H2H (cara a cara)":
    rango_h2h = st.selectbox("Filtrar periodo", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"])
    st.title("⚔️ Cara a Cara")
    
    df_p_filt = filtrar_por_fecha(df_partidos, rango_h2h)
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=min(1, len(nombres)-1))
    
    if j1 != j2:
        enf = df_p_filt[((df_p_filt['Ganador1']==j1)|(df_p_filt['Ganador2']==j1)|(df_p_filt['Perdedor1']==j1)|(df_p_filt['Perdedor2']==j1)) & 
                          ((df_p_filt['Ganador1']==j2)|(df_p_filt['Ganador2']==j2)|(df_p_filt['Perdedor1']==j2)|(df_p_filt['Perdedor2']==j2))]
        w1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
        w2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
        st.markdown("### Historial:")
        st.header(f"{j1} {w1} — {w2} {j2}")
        st.table(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']])

# --- 3. CARGAR PARTIDO ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    with st.form("f_partido"):
        c1, c2, s1, s2, s3 = st.columns([2, 2, 1, 1, 1])
        p1j1, p1j2 = c1.selectbox("P1 J1", nombres), c2.selectbox("P1 J2", nombres)
        p1s1, p1s2, p1s3 = s1.number_input("S1",0,7), s2.number_input("S2",0,7), s3.number_input("S3",0,7)
        c1b, c2b, s1b, s2b, s3b = st.columns([2, 2, 1, 1, 1])
        p2j1, p2j2 = c1b.selectbox("P2 J1", nombres), c2b.selectbox("P2 J2", nombres)
        p2s1, p2s2, p2s3 = s1b.number_input("S1",0,7, key="p2s1"), s2b.number_input("S2",0,7, key="p2s2"), s3b.number_input("S3",0,7, key="p2s3")
        if st.form_submit_button("GUARDAR"):
            st.info("Lógica de guardado ejecutada")

# --- 4. BUSCAR JUGADOR ---
elif menu == "🔍 Buscar jugador":
    st.title("🔍 Buscar Jugador")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    # st.selectbox por defecto permite escribir para filtrar si la lista es grande
    seleccion = st.selectbox("Escribe el nombre del jugador...", [""] + nombres, help="Puedes escribir para buscar")
    if seleccion != "":
        mostrar_perfil(seleccion, df_jugadores)

# --- 5. GESTIONAR ---
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
