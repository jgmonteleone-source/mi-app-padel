import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS PARA SOMBRAS Y CENTRADO DEFINITIVO ---
st.markdown("""
    <style>
    /* Forzar sombra en contenedores con borde */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0px 8px 16px rgba(0,0,0,0.2) !important;
        border-radius: 15px !important;
        padding: 15px !important;
        margin-bottom: 20px !important;
        background-color: white !important;
    }
    
    /* Centrado de imagen */
    [data-testid="stImage"] {
        display: flex;
        justify-content: center;
        margin-left: auto;
        margin-right: auto;
    }

    .titulo-card {
        text-align: center;
        font-weight: bold;
        color: #555;
        font-size: 14px;
        margin-bottom: 10px;
    }

    .puntos-card {
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        color: #007bff;
        margin-top: 5px;
    }

    .filtro-resaltado {
        font-size: 19px;
        font-weight: bold;
        padding-top: 15px;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=10)
def cargar_datos():
    try:
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        jugadores['Foto'] = jugadores['Foto'].astype(str).str.strip().str.replace(r'[\\"\']', '', regex=True)
        return jugadores, partidos
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
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
    else:
        st.write("📈 **Efectividad: 0%**")

# --- MENÚ ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H (cara a cara)", "📝 Cargar partido", "🔍 Buscar jugador"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.markdown('<label class="filtro-resaltado">Periodo</label>', unsafe_allow_html=True)
    rango = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("🏆 Ranking")
    
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        with st.container(border=True):
            st.markdown(f"<div class='titulo-card'>PUESTO #{i+1}</div>", unsafe_allow_html=True)
            
            img_url = row['Foto'] if row['Foto'].startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            # Mostramos la imagen
            st.image(img_url, width=120)
            
            # El botón de nombre sirve para abrir la ficha
            if st.button(f"Ver Ficha: {row['Nombre']}", key=f"rank_{row['Nombre']}", use_container_width=True):
                mostrar_perfil(row['Nombre'], df_jugadores)
            
            st.markdown(f"<div class='puntos-card'>{int(row['Puntos'])} PUNTOS</div>", unsafe_allow_html=True)

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
        st.header(f"{j1} {w1} — {w2} {j2}")
        st.dataframe(enf[['Fecha', 'Ganador1', 'Ganador2', 'Resultado']], use_container_width=True, hide_index=True)

# --- 3. CARGAR PARTIDO CON VALIDACIÓN 7-5/7-6 ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("form_partido"):
        with st.container(border=True):
            st.subheader("🎾 Pareja 1")
            p1j1 = st.selectbox("Jugador A", nombres, key="p1j1")
            p1j2 = st.selectbox("Jugador B", nombres, key="p1j2")
            
        with st.container(border=True):
            st.subheader("🎾 Pareja 2")
            p2j1 = st.selectbox("Jugador C", nombres, key="p2j1")
            p2j2 = st.selectbox("Jugador D", nombres, key="p2j2")
        
        sets = []
        for i in [1, 2, 3]:
            with st.container(border=True):
                st.subheader(f"🔢 SET {i}")
                c1, c2 = st.columns(2)
                s_p1 = c1.number_input("Pareja 1", 0, 7, key=f"s{i}p1")
                s_p2 = c2.number_input("Pareja 2", 0, 7, key=f"s{i}p2")
                sets.append((s_p1, s_p2))

        if st.form_submit_button("💾 GUARDAR PARTIDO", use_container_width=True):
            # VALIDACIÓN DE REGLA 7-5 / 7-6
            error_set = False
            for idx, (s1, s2) in enumerate(sets):
                if (s1 == 7 and s2 not in [5, 6]) or (s2 == 7 and s1 not in [5, 6]):
                    st.error(f"⚠️ Error en SET {idx+1}: Si un resultado es 7, el otro debe ser 5 o 6.")
                    error_set = True
                    break
            
            if not error_set:
                s1p1, s1p2 = sets[0]
                s2p1, s2p2 = sets[1]
                s3p1, s3p2 = sets[2]
                
                sets_ganados_p1 = (1 if s1p1 > s1p2 else 0) + (1 if s2p1 > s2p2 else 0) + (1 if s3p1 > s3p2 else 0)
                sets_ganados_p2 = (1 if s1p2 > s1p1 else 0) + (1 if s2p2 > s2p1 else 0) + (1 if s3p2 > s3p1 else 0)
                
                if sets_ganados_p1 != sets_ganados_p2:
                    ganadores = [p1j1, p1j2] if sets_ganados_p1 > sets_ganados_p2 else [p2j1, p2j2]
                    perdedores = [p2j1, p2j2] if sets_ganados_p1 > sets_ganados_p2 else [p1j1, p1j2]
                    res_str = f"{s1p1}-{s1p2}, {s2p1}-{s2p2}" + (f", {s3p1}-{s3p2}" if (s3p1+s3p2)>0 else "")
                    
                    nueva_fila = pd.DataFrame([{
                        "Fecha": datetime.now().strftime("%d/%m/%Y"),
                        "Ganador1": ganadores[0], "Ganador2": ganadores[1],
                        "Perdedor1": perdedores[0], "Perdedor2": perdedores[1],
                        "Resultado": res_str
                    }])
                    
                    try:
                        df_actualizado = pd.concat([df_partidos, nueva_fila], ignore_index=True)
                        conn.update(worksheet="Partidos", data=df_actualizado)
                        st.success("✅ ¡Partido guardado exitosamente!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"❌ Error al guardar: {e}")
