import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Padel Pro App", layout="wide")

# --- CSS FIJO E INAMOVIBLE (VERSION MAESTRA) ---
st.markdown("""
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        box-shadow: 0px 10px 30px rgba(0,0,0,0.2) !important;
        border-radius: 15px !important;
        padding: 20px !important;
        background-color: white !important;
        border: 1px solid #f0f0f0 !important;
        margin-bottom: 25px !important;
    }
    .ranking-card { text-align: center; }
    .ranking-card img {
        width: 140px; height: 140px; border-radius: 50%;
        object-fit: cover; border: 4px solid #007bff;
        margin: 0 auto 15px auto; display: block;
    }
    .ranking-name { font-size: 24px; font-weight: bold; color: #333; }
    .ranking-points { font-size: 20px; color: #007bff; font-weight: bold; margin-top: 5px; }
    .filtro-resaltado { font-size: 19px; font-weight: bold; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONEXIÓN A DATOS (SOLUCIÓN FINAL) ---
# Extraemos los secretos a un diccionario normal que SÍ podemos modificar
creds = dict(st.secrets["connections"]["gsheets"])

# Arreglamos la llave privada en ese diccionario
if "private_key" in creds:
    creds["private_key"] = creds["private_key"].replace("\\n", "\n")

# Creamos la conexión pasando el diccionario corregido
# Usamos un nombre de conexión distinto ("gsheets_fixed") para evitar conflictos
conn = st.connection("gsheets_fixed", type=GSheetsConnection, **creds)



def cargar_datos():
    try:
        # 1. Carga de Jugadores con mayor tolerancia
        jugadores = conn.read(worksheet="Jugadores", ttl=0)
        
        # Si la hoja existe, limpiamos nombres de columnas (quita espacios raros)
        jugadores.columns = [c.strip() for c in jugadores.columns]
        
        # Nos aseguramos de que haya datos antes de procesar
        if not jugadores.empty:
            # Eliminamos filas donde el nombre esté vacío
            jugadores = jugadores.dropna(subset=["Nombre"])
            
            # Convertimos a número solo las columnas que existan realmente
            cols_posibles = ['Puntos', 'PG', 'PP_perd', 'SG', 'SP']
            for col in cols_posibles:
                if col in jugadores.columns:
                    jugadores[col] = pd.to_numeric(jugadores[col], errors='coerce').fillna(0)
            
            # Limpieza final de nombres de jugadores
            jugadores['Nombre'] = jugadores['Nombre'].astype(str).str.strip()
        
        # 2. Carga de Partidos (Mantenemos tu lógica que ya funciona)
        partidos = conn.read(worksheet="Partidos", ttl=0)
        if partidos.empty:
            partidos = pd.DataFrame(columns=["Fecha", "Ganador1", "Ganador2", "Perdedor1", "Perdedor2", "Resultado"])
        else:
            partidos = partidos.dropna(subset=["Fecha"])
            partidos['Fecha'] = pd.to_datetime(partidos['Fecha'], dayfirst=True, errors='coerce')
        
        return jugadores, partidos
    except Exception as e:
        # Esto te ayudará a ver el error real en la pantalla si algo falla
        st.error(f"Error cargando datos: {e}")
        return pd.DataFrame(), pd.DataFrame()
        

# Recargamos datos
df_jugadores, df_partidos = cargar_datos()

# --- FUNCIONES DE APOYO ---
def filtrar_por_fecha(df, opcion):
    hoy = datetime.now()
    if df.empty or 'Fecha' not in df.columns: return df
    if opcion == "Este año": return df[df['Fecha'].dt.year == hoy.year]
    elif opcion == "Año pasado": return df[df['Fecha'].dt.year == hoy.year - 1]
    elif opcion == "Este mes": return df[(df['Fecha'].dt.year == hoy.year) & (df['Fecha'].dt.month == hoy.month)]
    elif opcion == "Mes pasado":
        mes_pasado = (hoy.replace(day=1) - timedelta(days=1))
        return df[(df['Fecha'].dt.year == mes_pasado.year) & (df['Fecha'].dt.month == mes_pasado.month)]
    return df

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

# --- NAVEGACIÓN ---
menu = st.sidebar.radio("MENÚ", ["🏆 Ranking", "⚔️ H2H", "📝 Cargar partido", "🔍 Buscar Jugador"])

# --- 1. RANKING ---
if menu == "🏆 Ranking":
    st.markdown('<p class="filtro-resaltado">Periodo</p>', unsafe_allow_html=True)
    rango = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("🏆 Ranking")
    df_rank = df_jugadores.sort_values(by="Puntos", ascending=False).reset_index(drop=True)
    for i, row in df_rank.iterrows():
        with st.container(border=True):
            img_url = row['Foto'] if str(row['Foto']).startswith("http") else "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            st.markdown(f"""<div class="ranking-card"><div style="color: #888; font-weight: bold;">PUESTO #{i+1}</div><img src="{img_url}"><div class="ranking-name">{row['Nombre']}</div><div class="ranking-points">{int(row['Puntos'])} PUNTOS</div></div>""", unsafe_allow_html=True)
            if st.button("Ver Ficha", key=f"btn_{row['Nombre']}", use_container_width=True):
                mostrar_perfil(row['Nombre'], df_jugadores)

# --- 2. H2H ---
elif menu == "⚔️ H2H":
    st.markdown('<p class="filtro-resaltado">Periodo</p>', unsafe_allow_html=True)
    rango_h2h = st.selectbox("", ["Siempre", "Este año", "Año pasado", "Este mes", "Mes pasado"], label_visibility="collapsed")
    st.title("⚔️ Cara a Cara")
    df_p_filt = filtrar_por_fecha(df_partidos, rango_h2h)
    nombres = sorted(df_jugadores["Nombre"].tolist())
    j1 = st.selectbox("Jugador 1", nombres, index=0)
    j2 = st.selectbox("Jugador 2", nombres, index=1)
    
    if not df_p_filt.empty:
        mask = (((df_p_filt['Ganador1'] == j1) | (df_p_filt['Ganador2'] == j1) | (df_p_filt['Perdedor1'] == j1) | (df_p_filt['Perdedor2'] == j1)) & ((df_p_filt['Ganador1'] == j2) | (df_p_filt['Ganador2'] == j2) | (df_p_filt['Perdedor1'] == j2) | (df_p_filt['Perdedor2'] == j2)))
        enf = df_p_filt[mask].copy()
        v1 = len(enf[(enf['Ganador1'] == j1) | (enf['Ganador2'] == j1)])
        v2 = len(enf[(enf['Ganador1'] == j2) | (enf['Ganador2'] == j2)])
        st.markdown("### HISTORIAL:")
        st.markdown(f"## {j1} {v1} — {v2} {j2}")
        if not enf.empty:
            enf['Ganadores'] = enf['Ganador1'].astype(str) + " / " + enf['Ganador2'].astype(str)
            enf['Perdedores'] = enf['Perdedor1'].astype(str) + " / " + enf['Perdedor2'].astype(str)
            enf['Fecha_str'] = enf['Fecha'].dt.strftime('%d/%m/%Y')
            st.dataframe(enf[["Fecha_str", "Ganadores", "Perdedores", "Resultado"]], hide_index=True, use_container_width=True)
        else: st.info("No hay enfrentamientos.")
    else: st.info("No hay partidos registrados.")

# --- 3. CARGAR PARTIDO ---
elif menu == "📝 Cargar partido":
    st.title("📝 Registrar Partido")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    with st.form("f_reg"):
        with st.container(border=True):
            st.subheader("👥 Pareja 1")
            p1j1, p1j2 = st.selectbox("Jugador A", nombres, key="a"), st.selectbox("Jugador B", nombres, key="b")
        with st.container(border=True):
            st.subheader("👥 Pareja 2")
            p2j1, p2j2 = st.selectbox("Jugador C", nombres, key="c"), st.selectbox("Jugador D", nombres, key="d")
        
        for i in [1, 2, 3]:
            with st.container(border=True):
                st.subheader(f"🔢 SET {i}")
                c1, c2 = st.columns(2)
                if i==1: s1p1, s1p2 = c1.number_input("Pareja 1", 0, 7, key="s1p1"), c2.number_input("Pareja 2", 0, 7, key="s1p2")
                if i==2: s2p1, s2p2 = c1.number_input("Pareja 1 ", 0, 7, key="s2p1"), c2.number_input("Pareja 2 ", 0, 7, key="s2p2")
                if i==3: s3p1, s3p2 = c1.number_input("Pareja 1  ", 0, 7, key="s3p1"), c2.number_input("Pareja 2  ", 0, 7, key="s3p2")

        if st.form_submit_button("💾 GUARDAR PARTIDO", use_container_width=True):
            ganador_s1 = "P1" if s1p1 > s1p2 else ("P2" if s1p2 > s1p1 else "Empate")
            ganador_s2 = "P1" if s2p1 > s2p2 else ("P2" if s2p2 > s2p1 else "Empate")
            jugadores_partido = [p1j1, p1j2, p2j1, p2j2]
            
            error = False
            if len(jugadores_partido) != len(set(jugadores_partido)):
                st.error("⚠️ No puede repetirse un jugador.")
                error = True
            elif (s1p1 == s1p2) or (s2p1 == s2p2) or (s3p1 == s3p2 and (s3p1 > 0 or s3p2 > 0)):
                st.error("⚠️ No puede haber empate en un set.")
                error = True
            elif (s1p1 == 7 and s1p2 not in [5,6]) or (s1p2 == 7 and s1p1 not in [5,6]) or \
                 (s2p1 == 7 and s2p2 not in [5,6]) or (s2p2 == 7 and s2p1 not in [5,6]) or \
                 (s3p1 == 7 and s3p2 not in [5,6]) or (s3p2 == 7 and s3p1 not in [5,6]):
                st.error("⚠️ Si una pareja obtuvo 7 juegos, el rival debe tener 5 o 6.")
                error = True
            elif ganador_s1 == ganador_s2 and (s3p1 > 0 or s3p2 > 0):
                st.error("⚠️ No se puede cargar un 3er set si una pareja ya ganó 2-0.")
                error = True
            elif ganador_s1 != ganador_s2 and (s3p1 == 0 and s3p2 == 0):
                st.error("⚠️ Es obligatorio cargar el 3er set si el partido está empatado 1-1.")
                error = True
            
            if not error:
                sets_p1 = (1 if s1p1 > s1p2 else 0) + (1 if s2p1 > s2p2 else 0) + (1 if s3p1 > s3p2 else 0)
                ganadores = [p1j1, p1j2] if sets_p1 >= 2 else [p2j1, p2j2]
                perdedores = [p2j1, p2j2] if sets_p1 >= 2 else [p1j1, p1j2]
                res = f"{s1p1}-{s1p2}, {s2p1}-{s2p2}" + (f", {s3p1}-{s3p2}" if (s3p1+s3p2)>0 else "")
                
                # --- GUARDADO BLINDADO ---
                nueva_fila = pd.DataFrame([{"Fecha": datetime.now().strftime("%d/%m/%Y"), "Ganador1": ganadores[0], "Ganador2": ganadores[1], "Perdedor1": perdedores[0], "Perdedor2": perdedores[1], "Resultado": res}])
                
                # Leemos la hoja limpia, sin caché, para saber qué hay de verdad
                df_backup = conn.read(worksheet="Partidos", ttl=0)
                # Unimos lo viejo con lo nuevo (ignorando índices viejos)
                df_final = pd.concat([df_backup, nueva_fila], ignore_index=True)
                # Actualizamos la hoja completa
                conn.update(worksheet="Partidos", data=df_final)
                
                st.success("✅ ¡Guardado con éxito!")
                st.cache_data.clear() # Limpiamos caché para que el Ranking se entere

# --- 4. BUSCAR JUGADOR ---
elif menu == "🔍 Buscar Jugador":
    st.title("🔍 Buscar Jugador")
    nombres = sorted(df_jugadores["Nombre"].tolist())
    sel = st.selectbox("Escribe el nombre", [""] + nombres)
    if sel: mostrar_perfil(sel, df_jugadores)
