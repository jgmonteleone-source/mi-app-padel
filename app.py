import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS INTEGRAL (DISEÑO MÓVIL Y SOMBRAS) ---
st.markdown("""
    <style>
    /* Sombras para bloques de Streamlit (Carga de partidos y filtros) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0px 8px 20px rgba(0,0,0,0.15) !important;
        border-radius: 15px !important;
        padding: 15px !important;
        background-color: white !important;
        margin-bottom: 15px !important;
    }

    /* Tarjeta de Ranking Personalizada */
    .ranking-card {
        background: white;
        border-radius: 20px;
        padding: 20px;
        box-shadow: 0px 10px 25px rgba(0,0,0,0.2);
        text-align: center;
        margin: 10px auto;
        border: 1px solid #f0f0f0;
        max-width: 320px;
    }

    .ranking-card img {
        width: 130px;
        height: 130px;
        border-radius: 50%;
        object-fit: cover;
        border: 4px solid #007bff;
        margin-bottom: 10px;
    }

    .ranking-name {
        font-size: 22px;
        font-weight: bold;
        color: #333;
        margin: 5px 0;
    }

    .ranking-points {
        font-size: 18px;
        color: #007bff;
        font-weight: bold;
    }

    /* Centrar selectores en móvil */
    .stSelectbox, .stNumberInput {
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN Y DATOS ---
conn = st.connection("gsheets", type=GSheetsConnection)

def cargar_datos():
    try:
        jugadores = conn.read(worksheet="Jugadores").dropna(subset=["Nombre"])
        partidos = conn.read(worksheet="Partidos").dropna(subset=["Fecha"])
        # Limpieza de datos
        jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
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
    st.markdown(f"<h4 style='text-align: center; color: gray;'>🏆 Posición: #{posicion}</h4>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center; color: #007bff;'>⭐ Puntos: {int(datos['Puntos'])}</h3>", unsafe_allow_html=True)
    st.divider()
    
    # Datos en el orden pedido
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"🏷️ **Posición:** {datos['Posicion']}")
        st.write(f"✅ **Ganados:** {int(datos['PG'])}")
        st.write(f"🎾 **Sets Ganados:** {int(datos['SG'])}")
    with col2:
        st.write(f"⭐ **Puntos:** {int(datos['Puntos'])}")
        st.write(f"❌ **Perdidos:** {int(datos['PP_perd'])}")
        st.write(f"🎾 **Sets Perdidos:** {int(datos['SP'])}")
    
    total = int(datos['PG']) + int(datos['PP_perd'])
    efectividad = (int(datos['PG']) / total * 100) if total > 0 else 0
    st.write(f"📈 **Efectividad: {efectividad:.1f}%**")
    st.progress(efectividad / 100)

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H", "📝 Cargar partido"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.title("🏆 Ranking Pro")
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)

    for i, row in df_rank.iterrows():
        img_url = row['Foto'] if str(row['Foto']).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
        
        # Tarjeta visual con sombra y datos dentro
        st.markdown(f"""
            <div class="ranking-card">
                <div style="color: #888; font-weight: bold;">PUESTO #{i+1}</div>
                <img src="{img_url}">
                <div class="ranking-name">{row['Nombre']}</div>
                <div class="ranking-points">{int(row['Puntos'])} PUNTOS</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Botón invisible/transparente para abrir la ficha
        if st.button(f"Ver estadísticas de {row['Nombre']}", key=f"btn_{row['Nombre']}", use_container_width=True):
            mostrar_perfil(row['Nombre'], df_jugadores)

# --- 2. H2H (CORREGIDO) ---
elif menu == "⚔️ H2H":
    st.title("⚔️ Cara a Cara")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Selecciona Jugador 1", nombres, index=0)
    j2 = st.selectbox("Selecciona Jugador 2", nombres, index=1)

    if j1 and j2:
        # Filtrar partidos donde ambos jugadores hayan estado (en cualquier pareja)
        mask = (
            ((df_partidos['Ganador1'] == j1) | (df_partidos['Ganador2'] == j1) | (df_partidos['Perdedor1'] == j1) | (df_partidos['Perdedor2'] == j1)) &
            ((df_partidos['Ganador1'] == j2) | (df_partidos['Ganador2'] == j2) | (df_partidos['Perdedor1'] == j2) | (df_partidos['Perdedor2'] == j2))
        )
        enfrentamientos = df_partidos[mask]
        
        victorias_j1 = len(enfrentamientos[(enfrentamientos['Ganador1'] == j1) | (enfrentamientos['Ganador2'] == j1)])
        victorias_j2 = len(enfrentamientos[(enfrentamientos['Ganador1'] == j2) | (enfrentamientos['Ganador2'] == j2)])
        
        st.subheader(f"Resultado Histórico: {j1} ({victorias_j1}) vs ({victorias_j2}) {j2}")
        st.dataframe(enfrentamientos[["Fecha", "Ganador1", "Ganador2", "Perdedor1", "Perdedor2", "Resultado"]], hide_index=True)

# --- 3. CARGAR PARTIDO (DISEÑO DE TARJETAS RESTAURADO) ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Nuevo Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    
    with st.form("registro_partido"):
        # Bloque Pareja 1
        with st.container(border=True):
            st.subheader("👥 Pareja 1")
            p1j1 = st.selectbox("Jugador 1", nombres, key="p1j1_new")
            p1j2 = st.selectbox("Jugador 2", nombres, key="p1j2_new")

        # Bloque Pareja 2
        with st.container(border=True):
            st.subheader("👥 Pareja 2")
            p2j1 = st.selectbox("Jugador 3", nombres, key="p2j1_new")
            p2j2 = st.selectbox("Jugador 4", nombres, key="p2j2_new")

        # Bloques de Sets
        col_sets = st.columns(3)
        with col_sets[0]:
            with st.container(border=True):
                st.write("**SET 1**")
                s1p1 = st.number_input("P1 ", 0, 7, key="s1p1_n")
                s1p2 = st.number_input("P2 ", 0, 7, key="s1p2_n")
        with col_sets[1]:
            with st.container(border=True):
                st.write("**SET 2**")
                s2p1 = st.number_input("P1  ", 0, 7, key="s2p1_n")
                s2p2 = st.number_input("P2  ", 0, 7, key="s2p2_n")
        with col_sets[2]:
            with st.container(border=True):
                st.write("**SET 3**")
                s3p1 = st.number_input("P1   ", 0, 7, key="s3p1_n")
                s3p2 = st.number_input("P2   ", 0, 7, key="s3p2_n")

        if st.form_submit_button("💾 GUARDAR RESULTADO", use_container_width=True):
            # Lógica de Validación
            ganador_s1 = "P1" if s1p1 > s1p2 else "P2"
            ganador_s2 = "P1" if s2p1 > s2p2 else "P2"
            
            error = False
            if ganador_s1 == ganador_s2 and (s3p1 > 0 or s3p2 > 0):
                st.error("⚠️ No se puede cargar un 3er set si una pareja ya ganó 2-0.")
                error = True
            
            for sA, sB in [(s1p1, s1p2), (s2p1, s2p2), (s3p1, s3p2)]:
                if (sA == 7 and sB not in [5, 6]) or (sB == 7 and sA not in [5, 6]):
                    st.error("⚠️ Regla del 7: Si un equipo tiene 7, el otro debe tener 5 o 6.")
                    error = True

            if not error:
                sets_p1 = (1 if s1p1 > s1p2 else 0) + (1 if s2p1 > s2p2 else 0) + (1 if s3p1 > s3p2 else 0)
                ganadores = [p1j1, p1j2] if sets_p1 >= 2 else [p2j1, p2j2]
                perdedores = [p2j1, p2j2] if sets_p1 >= 2 else [p1j1, p1j2]
                res_final = f"{s1p1}-{s1p2}, {s2p1}-{s2p2}" + (f", {s3p1}-{s3p2}" if (s3p1+s3p2)>0 else "")
                
                nueva_fila = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%d/%m/%Y"),
                    "Ganador1": ganadores[0], "Ganador2": ganadores[1],
                    "Perdedor1": perdedores[0], "Perdedor2": perdedores[1],
                    "Resultado": res_final
                }])
                
                _, df_actual = cargar_datos()
                df_total = pd.concat([df_actual, nueva_fila], ignore_index=True)
                conn.update(worksheet="Partidos", data=df_total)
                st.success("✅ Partido registrado con éxito.")
                st.cache_data.clear()
