import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS MEJORADO ---
st.markdown("""
    <style>
    /* Estilo de Tarjeta (Card) */
    .player-card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        border: 1px solid #eee;
        text-align: center;
    }
    
    /* Espaciado para el filtro Periodo */
    .filtro-resaltado {
        font-size: 19px;
        font-weight: bold;
        margin-bottom: 5px;
        padding-top: 10px;
        display: block;
    }

    /* Botón de nombre tipo Link */
    .stButton > button {
        border: none;
        background: transparent;
        color: #007bff;
        font-weight: bold;
        font-size: 20px;
        margin: 10px auto;
        display: block;
    }
    
    /* Imagen redonda */
    .img-ranking {
        border-radius: 50%;
        object-fit: cover;
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
        # Limpiar fecha y asegurar formato
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        jugadores['Foto'] = jugadores['Foto'].astype(str).str.strip().str.replace(r'[\\"\']', '', regex=True)
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FICHA TÉCNICA ---
@st.dialog("📊 Ficha Técnica")
def mostrar_perfil(nombre_jugador, df_jugadores):
    df_temp = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    posicion = df_temp[df_temp['Nombre'] == nombre_jugador].index[0] + 1
    datos = df_temp[df_temp['Nombre'] == nombre_jugador].iloc[0]
    st.markdown(f"<h2 style='text-align: center;'>👤 {nombre_jugador}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>🏆 Posición Ranking: #{posicion}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #007bff;'>⭐ Puntos: {int(datos['Puntos'])}</h3>", unsafe_allow_html=True)
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.write(f"✅ **Ganados:** {int(datos['PG'])}")
        st.write(f"🎾 **Sets G:** {int(datos['SG'])}")
    with c2:
        st.write(f"❌ **Perdidos:** {int(datos['PP_perd'])}")
        st.write(f"🎾 **Sets P:** {int(datos['SP'])}")
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"📈 **Efectividad: {efect:.1f}%**")
        st.progress(efect / 100)

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (cara a cara)", "📝 Cargar partido", "🔍 Buscar jugador"])

# --- 1. RANKING CON CARD CORREGIDA ---
if menu == "🏆 Ranking":
    st.markdown('<label class="filtro-resaltado">Periodo</label>', unsafe_allow_html=True)
    rango = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("🏆 Ranking")
    
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        # TODO DENTRO DE LA TARJETA
        st.markdown(f"""
            <div class="player-card">
                <div style="font-weight: bold; color: #555; margin-bottom: 10px;">PUESTO #{i+1}</div>
        """, unsafe_allow_html=True)
        
        img_url = row['Foto'] if row['Foto'].startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        st.image(img_url, width=90)
        
        if st.button(row['Nombre'], key=f"rank_{row['Nombre']}"):
            mostrar_perfil(row['Nombre'], df_jugadores)
            
        st.markdown(f"**{int(row['Puntos'])} PUNTOS**")
        st.markdown("</div>", unsafe_allow_html=True)

# --- 2. H2H SIN HORA ---
elif menu == "⚔️ H2H (cara a cara)":
    st.markdown('<label class="filtro-resaltado">Periodo</label>', unsafe_allow_html=True)
    rango_h2h = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], key="f_h2h", label_visibility="collapsed")
    st.title("⚔️ Cara a Cara")
    
    df_h2h = df_partidos.copy()
    # Formatear fecha para quitar la hora
    df_h2h['Fecha'] = df_h2h['Fecha'].dt.strftime('%d/%m/%Y')
    
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=min(1, len(nombres)-1))
    
    if j1 != j2:
        enf = df_h2h[((df_h2h['Ganador1']==j1)|(df_h2h['Ganador2']==j1)|(df_h2h['Perdedor1']==j1)|(df_h2h['Perdedor2']==j1)) & 
                     ((df_h2h['Ganador1']==j2)|(df_h2h['Ganador2']==j2)|(df_h2h['Perdedor1']==j2)|(df_h2h['Perdedor2']==j2))]
        w1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
        w2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
        st.markdown(f"### Historial:")
        st.header(f"{j1} {w1} — {w2} {j2}")
        st.dataframe(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']], use_container_width=True, hide_index=True)

# --- 3. CARGAR PARTIDO (ORDENADO PARA MÓVIL) ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    with st.form("form_partido"):
        st.subheader("🎾 Pareja 1")
        c1, c2 = st.columns(2)
        p1j1 = c1.selectbox("Jugador A", nombres, key="p1j1")
        p1j2 = c2.selectbox("Jugador B", nombres, key="p1j2")
        
        st.subheader("🎾 Pareja 2")
        c1b, c2b = st.columns(2)
        p2j1 = c1b.selectbox("Jugador C", nombres, key="p2j1")
        p2j2 = c2b.selectbox("Jugador D", nombres, key="p2j2")
        
        st.subheader("🔢 Marcador (Sets)")
        # En móvil esto se verá como 3 filas de 2 inputs, muy cómodo
        s1, s2, s3 = st.columns(3)
        p1s1 = s1.number_input("P1 - Set 1", 0, 7)
        p2s1 = s1.number_input("P2 - Set 1", 0, 7)
        
        p1s2 = s2.number_input("P1 - Set 2", 0, 7)
        p2s2 = s2.number_input("P2 - Set 2", 0, 7)
        
        p1s3 = s3.number_input("P1 - Set 3", 0, 7)
        p2s3 = s3.number_input("P2 - Set 3", 0, 7)
        
        if st.form_submit_button("💾 GUARDAR PARTIDO"):
            st.success("¡Partido guardado!")

# --- 4. BUSCAR JUGADOR ---
elif menu == "🔍 Buscar jugador":
    st.title("🔍 Buscar Jugador")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    seleccion = st.selectbox("Escribe el nombre...", [""] + nombres)
    if seleccion:
        mostrar_perfil(seleccion, df_jugadores)
