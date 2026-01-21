import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS INTEGRAL ---
st.markdown("""
    <style>
    /* Tarjeta del Ranking */
    .ranking-card {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.1);
        border: 1px solid #eee;
        text-align: center;
    }
    
    /* Títulos de secciones en Carga de Partido */
    .seccion-carga {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 10px;
        margin-top: 15px;
        margin-bottom: 10px;
        border-left: 5px solid #007bff;
        font-weight: bold;
        font-size: 18px;
    }

    .filtro-resaltado {
        font-size: 19px;
        font-weight: bold;
        padding-top: 10px;
        display: block;
    }

    /* Botón de nombre */
    .stButton > button {
        border: none;
        background: transparent;
        color: #007bff;
        font-weight: bold;
        font-size: 22px;
        text-decoration: underline;
        margin: 0 auto;
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

# --- FICHA TÉCNICA (MODAL) ---
@st.dialog("📊 Ficha Técnica")
def mostrar_perfil(nombre_jugador, df_jugadores):
    df_temp = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    posicion = df_temp[df_temp['Nombre'] == nombre_jugador].index[0] + 1
    datos = df_temp[df_temp['Nombre'] == nombre_jugador].iloc[0]
    st.markdown(f"<h2 style='text-align: center;'>👤 {nombre_jugador}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>🏆 Posición: #{posicion}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #007bff;'>⭐ Puntos: {int(datos['Puntos'])}</h3>", unsafe_allow_html=True)
    st.divider()
    c1, c2 = st.columns(2)
    c1.write(f"✅ **Ganados:** {int(datos['PG'])}")
    c1.write(f"🎾 **Sets G:** {int(datos['SG'])}")
    c2.write(f"❌ **Perdidos:** {int(datos['PP_perd'])}")
    c2.write(f"🎾 **Sets P:** {int(datos['SP'])}")
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"📈 **Efectividad: {efect:.1f}%**")
        st.progress(efect / 100)

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (cara a cara)", "📝 Cargar partido", "🔍 Buscar jugador"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.markdown('<label class="filtro-resaltado">Periodo</label>', unsafe_allow_html=True)
    rango = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("🏆 Ranking")
    
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        # Usamos st.container con border=True para asegurar que sea una tarjeta real
        with st.container(border=True):
            st.markdown(f"<div style='text-align:center; font-weight:bold; color:#555;'>PUESTO #{i+1}</div>", unsafe_allow_html=True)
            
            # Imagen
            img_url = row['Foto'] if row['Foto'].startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            # Centramos la imagen usando columnas
            col_img_left, col_img_mid, col_img_right = st.columns([1, 2, 1])
            with col_img_mid:
                st.image(img_url, width=120)
            
            # Nombre
            if st.button(row['Nombre'], key=f"rank_{row['Nombre']}", use_container_width=True):
                mostrar_perfil(row['Nombre'], df_jugadores)
            
            # Puntos
            st.markdown(f"<div style='text-align:center; font-size:18px;'><b>{int(row['Puntos'])} PUNTOS</b></div>", unsafe_allow_html=True)

# --- 2. H2H ---
elif menu == "⚔️ H2H (cara a cara)":
    st.markdown('<label class="filtro-resaltado">Periodo</label>', unsafe_allow_html=True)
    rango_h2h = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], key="f_h2h", label_visibility="collapsed")
    st.title("⚔️ Cara a Cara")
    
    df_h2h = df_partidos.copy()
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

# --- 3. CARGAR PARTIDO (DISEÑO POR BLOQUES) ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("form_partido"):
        # BLOQUE PAREJA 1
        st.markdown('<div class="seccion-carga">🎾 Pareja 1</div>', unsafe_allow_html=True)
        p1j1 = st.selectbox("Jugador 1", nombres, key="p1j1_new")
        p1j2 = st.selectbox("Jugador 2", nombres, key="p1j2_new")
        
        # BLOQUE PAREJA 2
        st.markdown('<div class="seccion-carga">🎾 Pareja 2</div>', unsafe_allow_html=True)
        p2j1 = st.selectbox("Jugador 3", nombres, key="p2j1_new")
        p2j2 = st.selectbox("Jugador 4", nombres, key="p2j2_new")
        
        # BLOQUE SETS
        for i in [1, 2, 3]:
            st.markdown(f'<div class="seccion-carga">🔢 SET {i}</div>', unsafe_allow_html=True)
            col_a, col_b = st.columns(2)
            if i == 1:
                p1si = col_a.number_input("Pareja 1", 0, 7, key=f"p1s{i}")
                p2si = col_b.number_input("Pareja 2", 0, 7, key=f"p2s{i}")
            elif i == 2:
                p1si2 = col_a.number_input("Pareja 1", 0, 7, key=f"p1s{i}")
                p2si2 = col_b.number_input("Pareja 2", 0, 7, key=f"p2s{i}")
            else:
                p1si3 = col_a.number_input("Pareja 1", 0, 7, key=f"p1s{i}")
                p2si3 = col_b.number_input("Pareja 2", 0, 7, key=f"p2s{i}")

        st.markdown("---")
        if st.form_submit_button("💾 GUARDAR PARTIDO", use_container_width=True):
            st.success("¡Partido guardado exitosamente!")

# --- 4. BUSCAR JUGADOR ---
elif menu == "🔍 Buscar jugador":
    st.title("🔍 Buscar Jugador")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    seleccion = st.selectbox("Escribe el nombre...", [""] + nombres)
    if seleccion:
        mostrar_perfil(seleccion, df_jugadores)
