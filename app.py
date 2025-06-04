import streamlit as st
import pandas as pd
from scipy.stats import poisson
import datetime
import random
import requests

# --- CONFIGURACION INICIAL ---
st.set_page_config(page_title="Value Bets Poisson + Stats", layout="wide")
st.title("🌟 Value Bets: Manual + API Odds Reales")

# --- CONFIGURACION DE API ---
API_KEY = "a3c06fc76e5cb1284067b912d4ab004a"  # ⚠️ Reemplaza esto con tu clave personal
API_URL = "https://api.the-odds-api.com/v4/sports/soccer_epl/odds"

def obtener_partidos_api(region="uk", market="h2h"):
    params = {
        "apiKey": API_KEY,
        "regions": region,
        "markets": market,
        "oddsFormat": "decimal"
    }
    try:
        response = requests.get(API_URL, params=params)
        if response.status_code != 200:
            st.warning(f"⚠️ Error en la API: {response.status_code}")
            return []
        return response.json()
    except Exception as e:
        st.error(f"❌ Error accediendo a la API: {e}")
        return []

# --- FUNCION CALCULO POISSON ---
def calcular_probabilidades(local_goles, visitante_goles, max_goals=5):
    p_home = [poisson.pmf(i, local_goles) for i in range(max_goals + 1)]
    p_away = [poisson.pmf(i, visitante_goles) for i in range(max_goals + 1)]
    win, draw, lose = 0, 0, 0
    for hg in range(max_goals + 1):
        for ag in range(max_goals + 1):
            p = p_home[hg] * p_away[ag]
            if hg > ag:
                win += p
            elif hg == ag:
                draw += p
            else:
                lose += p
    return win, draw, lose

# --- SELECCION DE MODO ---
st.sidebar.header("⚙️ Modo de Uso")
mode = st.sidebar.radio("Selecciona modo:", ["Manual (CSV)", "Automático (API Odds reales)"])

# --- MODO MANUAL ---
if mode == "Manual (CSV)":
    uploaded_files = st.file_uploader("📂 Sube CSVs con datos históricos", type=["csv"], accept_multiple_files=True)
    if uploaded_files:
        dfs = []
        for file in uploaded_files:
            try:
                df_temp = pd.read_csv(file, sep=';')
                if df_temp.shape[1] <= 1:
                    file.seek(0)
                    df_temp = pd.read_csv(file, sep=',')
                df_temp['Liga'] = file.name.split('.')[0]
                dfs.append(df_temp)
            except Exception as e:
                st.warning(f"❌ Error al cargar {file.name}: {e}")

        if dfs:
            df = pd.concat(dfs, ignore_index=True)
            st.subheader("🔍 Vista previa de datos")
            st.dataframe(df.head())

            ligas = sorted(df['Liga'].unique())
            selected_liga = st.sidebar.selectbox("Filtrar por liga:", ligas)
            filtered_df = df[df['Liga'] == selected_liga]
            equipos = sorted(pd.unique(filtered_df[['HomeTeam', 'AwayTeam']].values.ravel()))

            home_team = st.sidebar.selectbox("Equipo LOCAL", equipos)
            away_team = st.sidebar.selectbox("Equipo VISITANTE", equipos)

            home_stats = filtered_df[filtered_df['HomeTeam'] == home_team]
            away_stats = filtered_df[filtered_df['AwayTeam'] == away_team]

            home_avg_goals = home_stats['FTHG'].mean()
            away_avg_goals = away_stats['FTAG'].mean()

            st.subheader("📊 Estadísticas promedio")
            st.write(f"Goles promedio local: **{home_avg_goals:.2f}**")
            st.write(f"Goles promedio visitante: **{away_avg_goals:.2f}**")

            extras = {
                "Tiros local (HS)": "HS",
                "Tiros visitante (AS)": "AS",
                "Tiros a puerta local (HST)": "HST",
                "Tiros a puerta visitante (AST)": "AST",
                "Corners local (HC)": "HC",
                "Corners visitante (AC)": "AC",
                "Tarjetas amarillas local (HY)": "HY",
                "Tarjetas amarillas visitante (AY)": "AY"
            }
            for label, col in extras.items():
                if col in filtered_df.columns:
                    hval = home_stats[col].mean()
                    aval = away_stats[col].mean()
                    st.write(f"{label}: Local {hval:.1f} | Visitante {aval:.1f}")

            ph, pd, pa = calcular_probabilidades(home_avg_goals, away_avg_goals)
            st.subheader("📈 Probabilidades estimadas")
            st.write(f"🏠 Local: {ph:.2%}")
            st.write(f"🤝 Empate: {pd:.2%}")
            st.write(f"🚗 Visitante: {pa:.2%}")

            st.subheader("💸 Cuotas para detectar valor")
            odd_home = st.number_input("Cuota Local", min_value=1.0, step=0.01)
            odd_draw = st.number_input("Cuota Empate", min_value=1.0, step=0.01)
            odd_away = st.number_input("Cuota Visitante", min_value=1.0, step=0.01)

            st.subheader("📌 Apuestas de Valor")
            if ph > 1/odd_home:
                st.success(f"🏠 Apuesta de valor: LOCAL @ {odd_home:.2f}")
            if pd > 1/odd_draw:
                st.success(f"🤝 Apuesta de valor: EMPATE @ {odd_draw:.2f}")
            if pa > 1/odd_away:
                st.success(f"🚗 Apuesta de valor: VISITANTE @ {odd_away:.2f}")

# --- MODO API AUTOMATICO ---
else:
    st.subheader("📡 Partidos reales con cuotas (API Sport Odds)")
    data_api = obtener_partidos_api()

    if not data_api:
        st.info("No se encontraron partidos o hubo error con la API.")
    else:
        for match in data_api:
            home = match['home_team']
            away = match['away_team']
            bookmakers = match.get('bookmakers', [])
            if not bookmakers:
                continue
            odds_data = bookmakers[0]['markets'][0]['outcomes']
            cuotas = {item['name']: item['price'] for item in odds_data}

            gl = random.uniform(1.0, 2.2)  # Puede reemplazarse con datos reales
            gv = random.uniform(0.7, 1.7)

            pl, pd, pv = calcular_probabilidades(gl, gv)

            valor = ""
            color = "lightcoral"
            if "Draw" in cuotas and pd > 1 / cuotas["Draw"]:
                valor = "🤝 Empate"
                color = "khaki"
            if "Home" in cuotas and pl > 1 / cuotas["Home"]:
                valor = f"🏠 Local ({home})"
                color = "lightgreen"
            if "Away" in cuotas and pv > 1 / cuotas["Away"]:
                valor = f"🚗 Visitante ({away})"
                color = "lightgreen"

            st.markdown(f"### {home} vs {away}")
            st.markdown(f"<div style='background-color:{color}; padding:10px; border-radius:10px'>"
                        f"<b>Probabilidades:</b> Local {pl:.1%} | Empate {pd:.1%} | Visitante {pv:.1%}<br>"
                        f"<b>Cuotas:</b> L {cuotas.get('Home', '-'):.2f} | D {cuotas.get('Draw', '-'):.2f} | V {cuotas.get('Away', '-'):.2f}<br>"
                        f"<b>Apuesta de Valor:</b> {valor if valor else 'Ninguna'}"
                        f"</div><br>", unsafe_allow_html=True)

