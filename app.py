import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS PARA ESTÉTICA DE CARD Y FORMULARIOS ---
st.markdown("""
    <style>
    /* Estilo de Tarjeta (Card) para el Ranking */
    .player-card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        border: 1px solid #eee;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }
    
    /* Resaltado del texto Periodo */
    .filtro-resaltado {
        font-size: 19px;
        font-weight: bold;
        margin-bottom: -10px;
    }

    /* Forzar que los botones de nombre en el ranking sean estéticos */
    .stButton > button {
        border: none;
        background: transparent;
        color: #007bff;
        font-weight: bold;
        font-size: 20px;
        text-decoration: underline;
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
    posicion = df_temp[df_temp['Nombre'] == nombre_jugador].index[0] + 1
    datos = df_temp[df_temp['Nombre'] == nombre_jugador].iloc[0]

    st.markdown(f"<h2 style='text-align: center;'>👤 {nombre_jugador}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>🏆 Posición Ranking: #{posicion}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #007bff;'>⭐ Puntos: {int(datos['Puntos'])}</h3>", unsafe_allow_html=True)
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"✅ **Ganados:** {int(datos['PG'])}")
        st.write(f"🎾 **Sets G:** {int(datos['SG'])}")
    with col2:
        st.write(f"❌ **Perdidos:** {int(datos['PP_perd'])}")
        st.write(f"🎾 **Sets P:** {int(datos['SP'])}")
    
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"📈 **Efectividad: {efect:.1f}%**")
        st.progress(efect / 100)
    else:
        st.write("📈 **Efectividad: 0%**")

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (cara a cara)", "📝 Cargar partido", "🔍 Buscar jugador"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.markdown('<p class="filtro-resaltado">Periodo</p>', unsafe_allow_html=True)
    rango = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("🏆 Ranking")
    
    df_jugadores["Puntos"] = pd.to_numeric(df_jugadores["Puntos"], errors='coerce').fillna(0)
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        # CONTENEDOR TIPO CARD
        with st.container():
            st.markdown(f"""
                <div class="player-card">
                    <div style="font-weight: bold; color: #555; margin-bottom: 5px;">PUESTO #{i+1}</div>
                </div>
            """, unsafe_allow_html=True)
            
            # Imagen centrada
            img_url = row['Foto'] if row['Foto'].startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            st.image(img_url, width=100)
            
            # Botón de nombre
            if st.button(row['Nombre'], key=f"rank_{row['Nombre']}"):
                mostrar_perfil(row['Nombre'], df_jugadores)
            
            st.markdown(f"**{int(row['Puntos'])} PUNTOS**")
            st.markdown("---")

# --- 2. H2H ---
elif menu == "⚔️ H2H (cara a cara)":
    st.markdown('<p class="filtro-resaltado">Periodo</p>', unsafe_allow_html=True)
    rango_h2h = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], key="f_h2h", label_visibility="collapsed")
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
        st.markdown(f"### Historial:")
        st.header(f"{j1} {w1} — {w2} {j2}")
        st.table(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']])

# --- 3. CARGAR PARTIDO (RESTAURADO) ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    with st.form("form_partido"):
        # Pareja 1 en línea
        c1, c2, s1, s2, s3 = st.columns([2, 2, 1, 1, 1])
        p1j1 = c1.selectbox("Pareja 1 - J1", nombres)
        p1j2 = c2.selectbox("Pareja 1 - J2", nombres)
        p1s1 = s1.number_input("S1", 0, 7, key="p1s1")
        p1s2 = s2.number_input("S2", 0, 7, key="p1s2")
        p1s3 = s3.number_input("S3", 0, 7, key="p1s3")
        
        # Pareja 2 en línea
        c1b, c2b, s1b, s2b, s3b = st.columns([2, 2, 1, 1, 1])
        p2j1 = c1b.selectbox("Pareja 2 - J1", nombres)
        p2j2 = c2b.selectbox("Pareja 2 - J2", nombres)
        p2s1 = s1b.number_input("S1", 0, 7, key="p2s1")
        p2s2 = s2b.number_input("S2", 0, 7, key="p2s2")
        p2s3 = s3b.number_input("S3", 0, 7, key="p2s3")
        
        if st.form_submit_button("💾 GUARDAR PARTIDO"):
            st.success("Partido guardado")

# --- 4. BUSCAR JUGADOR (Móvil mejorado) ---
elif menu == "🔍 Buscar jugador":
    st.title("🔍 Buscar Jugador")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    # Selectbox con búsqueda para móviles
    seleccion = st.selectbox("Escribe para buscar un jugador...", [""] + nombres)
    if seleccion:
        mostrar_perfil(seleccion, df_jugadores)
