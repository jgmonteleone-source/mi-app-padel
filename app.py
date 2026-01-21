import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS PARA CENTRADO Y SOMBRAS ---
st.markdown("""
    <style>
    /* Forzar sombra y bordes en tarjetas */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0px 8px 16px rgba(0,0,0,0.1) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        border: 1px solid #eee !important;
    }
    
    /* Centrado de todo el contenido del ranking */
    [data-testid="column"] {
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
    }

    .stButton > button {
        border: none;
        background: transparent;
        color: #007bff;
        font-weight: bold;
        font-size: 20px;
        margin: 0 auto;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        # Cargamos siempre sin cache para evitar el problema de sobreescritura por datos viejos
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        return jugadores, partidos
    except:
        return pd.DataFrame(), pd.DataFrame()

df_jugadores, df_partidos = cargar_datos()

# --- FICHA TÉCNICA ---
@st.dialog("📊 Ficha Técnica")
def mostrar_perfil(nombre_jugador, df_jugadores):
    df_temp = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    posicion = df_temp[df_temp['Nombre'] == nombre_jugador].index[0] + 1
    datos = df_temp[df_temp['Nombre'] == nombre_jugador].iloc[0]
    
    st.markdown(f"<h2 style='text-align: center;'>👤 {nombre_jugador}</h2>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: gray;'>🏆 Posición: #{posicion}</h3>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #007bff;'>⭐ Puntos: {int(datos['Puntos'])}</h3>", unsafe_allow_html=True)
    st.divider()
    st.write(f"✅ **Ganados:** {int(datos['PG'])}")
    st.write(f"❌ **Perdidos:** {int(datos['PP_perd'])}")
    st.write(f"🎾 **Sets ganados:** {int(datos['SG'])}")
    st.write(f"🎾 **Sets perdidos:** {int(datos['SP'])}")
    total = int(datos['PG']) + int(datos['PP_perd'])
    if total > 0:
        efect = (int(datos['PG']) / total) * 100
        st.write(f"📈 **Efectividad: {efect:.1f}%**")
        st.progress(efect / 100)

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H", "📝 Cargar partido", "🔍 Buscar jugador"])

# --- 1. RANKING (CON FOTO CLICKABLE Y CENTRADA) ---
if menu == "🏆 Ranking":
    st.title("🏆 Ranking")
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        with st.container(border=True):
            st.write(f"**PUESTO #{i+1}**")
            img_url = row['Foto'] if str(row['Foto']).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            
            # Truco para que la foto sea centrada y clickable
            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.button("", key=f"img_{row['Nombre']}"): # Botón invisible sobre la imagen
                    mostrar_perfil(row['Nombre'], df_jugadores)
                st.image(img_url, width=120)
                if st.button(row['Nombre'], key=f"txt_{row['Nombre']}"):
                    mostrar_perfil(row['Nombre'], df_jugadores)
            
            st.markdown(f"**{int(row['Puntos'])} PUNTOS**")

# --- 3. CARGAR PARTIDO (CON LÓGICA DE 2 SETS Y NO SOBREESCRITURA) ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("form_partido"):
        with st.container(border=True):
            st.subheader("🎾 Pareja 1")
            p1j1, p1j2 = st.selectbox("Jugador 1", nombres), st.selectbox("Jugador 2", nombres)
        with st.container(border=True):
            st.subheader("🎾 Pareja 2")
            p2j1, p2j2 = st.selectbox("Jugador 3", nombres), st.selectbox("Jugador 4", nombres)
        
        # Inputs de Sets
        with st.container(border=True):
            st.subheader("🔢 SET 1")
            c1, c2 = st.columns(2)
            s1p1 = c1.number_input("Pareja 1 ", 0, 7, key="s1p1")
            s1p2 = c2.number_input("Pareja 2 ", 0, 7, key="s1p2")
        with st.container(border=True):
            st.subheader("🔢 SET 2")
            c1, c2 = st.columns(2)
            s2p1 = c1.number_input("Pareja 1  ", 0, 7, key="s2p1")
            s2p2 = c2.number_input("Pareja 2  ", 0, 7, key="s2p2")
        with st.container(border=True):
            st.subheader("🔢 SET 3 (Si aplica)")
            c1, c2 = st.columns(2)
            s3p1 = c1.number_input("Pareja 1   ", 0, 7, key="s3p1")
            s3p2 = c2.number_input("Pareja 2   ", 0, 7, key="s3p2")

        if st.form_submit_button("💾 GUARDAR PARTIDO", use_container_width=True):
            # 1. Validar si ya hubo un ganador en 2 sets
            ganador_s1 = "P1" if s1p1 > s1p2 else "P2"
            ganador_s2 = "P1" if s2p1 > s2p2 else "P2"
            
            error = False
            if ganador_s1 == ganador_s2 and (s3p1 > 0 or s3p2 > 0):
                st.error("⚠️ No se puede cargar un 3er set si una pareja ya ganó 2-0.")
                error = True
            
            # 2. Validar regla del 7-5/7-6
            for s1, s2 in [(s1p1, s1p2), (s2p1, s2p2), (s3p1, s3p2)]:
                if (s1 == 7 and s2 not in [5, 6]) or (s2 == 7 and s1 not in [5, 6]):
                    st.error("⚠️ Resultado inválido: Si un set es 7, el otro debe ser 5 o 6.")
                    error = True

            if not error:
                # Determinar Ganadores Finales
                sets_p1 = (1 if s1p1 > s1p2 else 0) + (1 if s2p1 > s2p2 else 0) + (1 if s3p1 > s3p2 else 0)
                sets_p2 = (1 if s1p2 > s1p1 else 0) + (1 if s2p2 > s2p1 else 0) + (1 if s3p2 > s3p1 else 0)
                
                ganadores = [p1j1, p1j2] if sets_p1 > sets_p2 else [p2j1, p2j2]
                perdedores = [p2j1, p2j2] if sets_p1 > sets_p2 else [p1j1, p1j2]
                res_str = f"{s1p1}-{s1p2}, {s2p1}-{s2p2}" + (f", {s3p1}-{s3p2}" if (s3p1+s3p2)>0 else "")
                
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Ganador1": ganadores[0], "Ganador2": ganadores[1],
                    "Perdedor1": perdedores[0], "Perdedor2": perdedores[1],
                    "Resultado": res_str
                }])
                
                # RECARGAR DATOS ANTES DE ACTUALIZAR PARA NO SOBREESCRIBIR
                _, df_partidos_actual = cargar_datos()
                df_final = pd.concat([df_partidos_actual, nueva_fila], ignore_index=True)
                conn.update(worksheet="Partidos", data=df_final)
                st.success("✅ Partido guardado y ranking actualizado.")
                st.cache_data.clear()
