import streamlit as st
import pandas as pd
from scipy.stats import poisson
import os

# Configuración inicial
st.set_page_config(page_title="Value Bets Poisson + Stats", layout="wide")
st.title("⚽ Modelo Value Bets con estadísticas y filtros por país/liga")

# Diccionario para identificar ligas y países a partir del nombre del archivo
LEAGUE_MAPPING = {
    "E0": ("Premier League", "Inglaterra"),
    "E1": ("Championship", "Inglaterra"),
    "E2": ("League One", "Inglaterra"),
    "E3": ("League Two", "Inglaterra"),
    "EC": ("National League", "Inglaterra"),
    "SC0": ("Premiership", "Escocia"),
    "SC1": ("Championship", "Escocia"),
    "SC2": ("League One", "Escocia"),
    "SC3": ("League Two", "Escocia"),
    "D1": ("Bundesliga", "Alemania"),
    "D2": ("Bundesliga 2", "Alemania"),
    "SP1": ("La Liga", "España"),
    "SP2": ("Liga Hypermotion", "España"),
    "I1": ("Calcio", "Italia"),
    "I2": ("Serie B", "Italia"),
    "F1": ("Ligue 1", "Francia"),
    "F2": ("Ligue 2", "Francia"),
    "B1": ("Jupiler Pro League", "Bélgica"),
    "N1": ("Eredivisie", "Holanda"),
    "P1": ("Liga Portugal", "Portugal"),
    "T1": ("Super Lig", "Turquía"),
    "G1": ("Superliga", "Grecia")
}

# Carga de archivos
uploaded_files = st.file_uploader(
    "📂 Sube varios archivos CSV con datos históricos",
    type=["csv"],
    accept_multiple_files=True
)

if uploaded_files:
    data_frames = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file, sep=';')
            if df.shape[1] <= 1:
                file.seek(0)
                df = pd.read_csv(file, sep=',')
            code = os.path.splitext(file.name)[0].upper()
            league, country = LEAGUE_MAPPING.get(code, ("Desconocida", "Desconocido"))
            df["League"] = league
            df["Country"] = country
            df["Code"] = code
            data_frames.append(df)
        except Exception as e:
            st.warning(f"Error al cargar {file.name}: {e}")

    if data_frames:
        df = pd.concat(data_frames, ignore_index=True)

        st.sidebar.header("🎯 Filtros")
        selected_country = st.sidebar.selectbox("País", sorted(df["Country"].unique()))
        filtered_df = df[df["Country"] == selected_country]

        selected_league = st.sidebar.selectbox("Liga", sorted(filtered_df["League"].unique()))
        league_df = filtered_df[filtered_df["League"] == selected_league]

        teams = sorted(pd.unique(league_df[['HomeTeam', 'AwayTeam']].values.ravel()))
        home_team = st.sidebar.selectbox("Equipo LOCAL", teams)
        away_team = st.sidebar.selectbox("Equipo VISITANTE", teams)

        st.subheader("📊 Estadísticas del partido")
        home_stats = league_df[league_df['HomeTeam'] == home_team]
        away_stats = league_df[league_df['AwayTeam'] == away_team]

        home_avg_goals = home_stats['FTHG'].mean()
        away_avg_goals = away_stats['FTAG'].mean()

        st.markdown(f"- ⚽ Goles promedio local ({home_team}): **{home_avg_goals:.2f}**")
        st.markdown(f"- ⚽ Goles promedio visitante ({away_team}): **{away_avg_goals:.2f}**")

        for label, col in {
            "Tiros": ("HS", "AS"),
            "Tiros a puerta": ("HST", "AST"),
            "Faltas": ("HF", "AF"),
            "Amarillas": ("HY", "AY"),
            "Corners": ("HC", "AC")
        }.items():
            if col[0] in league_df.columns and col[1] in league_df.columns:
                l_mean = home_stats[col[0]].mean()
                v_mean = away_stats[col[1]].mean()
                st.markdown(f"- {label}: local {l_mean:.1f} | visitante {v_mean:.1f}")

        # Modelo de Poisson
        max_goals = 5
        home_probs = [poisson.pmf(i, home_avg_goals) for i in range(max_goals+1)]
        away_probs = [poisson.pmf(i, away_avg_goals) for i in range(max_goals+1)]

        prob_home, prob_draw, prob_away = 0, 0, 0
        for i in range(max_goals+1):
            for j in range(max_goals+1):
                p = home_probs[i] * away_probs[j]
                if i > j:
                    prob_home += p
                elif i == j:
                    prob_draw += p
                else:
                    prob_away += p

        st.subheader("📈 Probabilidades estimadas")
        st.write(f"🏠 {home_team}: {prob_home:.2%}")
        st.write(f"🤝 Empate: {prob_draw:.2%}")
        st.write(f"🚗 {away_team}: {prob_away:.2%}")

        st.subheader("💸 Introduce cuotas")
        odd_home = st.number_input("Cuota local", min_value=1.0)
        odd_draw = st.number_input("Cuota empate", min_value=1.0)
        odd_away = st.number_input("Cuota visitante", min_value=1.0)

        st.subheader("🎯 Value Bets detectadas")
        value_bets = []
        if prob_home > 1 / odd_home:
            value_bets.append(f"🏠 LOCAL ({home_team}) @ {odd_home} ✅")
        if prob_draw > 1 / odd_draw:
            value_bets.append(f"🤝 EMPATE @ {odd_draw} ✅")
        if prob_away > 1 / odd_away:
            value_bets.append(f"🚗 VISITANTE ({away_team}) @ {odd_away} ✅")

        if value_bets:
            st.success("Apuestas con valor:")
            for vb in value_bets:
                st.write(vb)
        else:
            st.info("No se encontraron apuestas con valor.")

else:
    st.info("🔁 Esperando archivos CSV para procesar.")

