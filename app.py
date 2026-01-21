import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS INYECTADO (ESTO NO LO ROMPE EL MÓVIL) ---
st.markdown("""
    <style>
    /* Estilo de la Tarjeta */
    .card-ranking {
        background-color: white;
        border-radius: 15px;
        padding: 20px;
        margin: 15px auto;
        text-align: center;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.2) !important; /* Sombra pronunciada */
        border: 1px solid #eee;
        max-width: 300px; /* Tamaño ideal para móvil */
    }
    
    .card-ranking img {
        border-radius: 50%;
        width: 100px;
        height: 100px;
        object-fit: cover;
        margin-bottom: 10px;
        cursor: pointer;
        border: 3px solid #007bff;
    }

    .card-ranking h2 {
        color: #007bff;
        margin: 10px 0;
        font-size: 22px;
        text-decoration: underline;
    }

    .puesto-label {
        font-size: 14px;
        color: #777;
        font-weight: bold;
        text-transform: uppercase;
    }

    .puntos-label {
        font-size: 18px;
        font-weight: bold;
        color: #333;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
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
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H", "📝 Cargar partido", "🔍 Buscar"])

# --- 1. RANKING (HTML PURO PARA MÓVIL) ---
if menu == "🏆 Ranking":
    st.title("🏆 Ranking")
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        img_url = row['Foto'] if str(row['Foto']).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        
        # Creamos la tarjeta con HTML
        st.markdown(f"""
            <div class="card-ranking">
                <div class="puesto-label">Puesto #{i+1}</div>
                <img src="{img_url}">
            </div>
        """, unsafe_allow_html=True)
        
        # El botón de Streamlit para abrir la ficha (debajo de la imagen HTML)
        if st.button(row['Nombre'], key=f"btn_{row['Nombre']}", use_container_width=True):
            mostrar_perfil(row['Nombre'], df_jugadores)
        
        st.markdown(f"<div class='puntos-label'>{int(row['Puntos'])} Puntos</div><br>", unsafe_allow_html=True)

# --- 3. CARGAR PARTIDO (LÓGICA ACTUALIZADA) ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("form_partido"):
        st.subheader("🎾 Equipos")
        p1j1, p1j2 = st.selectbox("Pareja 1 - J1", nombres), st.selectbox("Pareja 1 - J2", nombres)
        p2j1, p2j2 = st.selectbox("Pareja 2 - J1", nombres), st.selectbox("Pareja 2 - J2", nombres)
        
        st.subheader("🔢 Resultados")
        c1, c2 = st.columns(2)
        s1p1 = c1.number_input("Set 1 - P1", 0, 7)
        s1p2 = c2.number_input("Set 1 - P2", 0, 7)
        s2p1 = c1.number_input("Set 2 - P1", 0, 7)
        s2p2 = c2.number_input("Set 2 - P2", 0, 7)
        s3p1 = c1.number_input("Set 3 - P1", 0, 7)
        s3p2 = c2.number_input("Set 3 - P2", 0, 7)

        if st.form_submit_button("💾 GUARDAR PARTIDO"):
            # Lógica de validación
            ganador_s1 = "P1" if s1p1 > s1p2 else "P2"
            ganador_s2 = "P1" if s2p1 > s2p2 else "P2"
            
            error = False
            # Regra 2-0 no necesita 3er set
            if ganador_s1 == ganador_s2 and (s3p1 > 0 or s3p2 > 0):
                st.error("⚠️ No se puede cargar un 3er set si ya ganaron 2-0.")
                error = True
            
            # Regra 7-5 / 7-6
            for sA, sB in [(s1p1, s1p2), (s2p1, s2p2), (s3p1, s3p2)]:
                if (sA == 7 and sB not in [5, 6]) or (sB == 7 and sA not in [5, 6]):
                    st.error("⚠️ Error: Si un set es 7, el otro debe ser 5 o 6.")
                    error = True

            if not error:
                # Determinar ganador final
                sets_p1 = (1 if s1p1 > s1p2 else 0) + (1 if s2p1 > s2p2 else 0) + (1 if s3p1 > s3p2 else 0)
                ganadores = [p1j1, p1j2] if sets_p1 >= 2 else [p2j1, p2j2]
                perdedores = [p2j1, p2j2] if sets_p1 >= 2 else [p1j1, p1j2]
                res_str = f"{s1p1}-{s1p2}, {s2p1}-{s2p2}" + (f", {s3p1}-{s3p2}" if (s3p1+s3p2)>0 else "")
                
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Ganador1": ganadores[0], "Ganador2": ganadores[1],
                    "Perdedor1": perdedores[0], "Perdedor2": perdedores[1],
                    "Resultado": res_str
                }])
                
                # Cargar partidos actuales para concatenar y no sobreescribir
                _, df_partidos_actual = cargar_datos()
                df_final = pd.concat([df_partidos_actual, nueva_fila], ignore_index=True)
                conn.update(worksheet="Partidos", data=df_final)
                st.success("✅ ¡Guardado!")
                st.cache_data.clear()
