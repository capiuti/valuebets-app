
import streamlit as st
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Value Bets - Modelo Poisson", layout="centered")

st.title("⚽ Value Bets con Modelo Poisson")

st.markdown("Sube tu archivo CSV con partidos y cuotas para detectar apuestas con valor.")

uploaded_file = st.file_uploader("📥 Sube tu archivo CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    
    # Verifica columnas esenciales
    required_cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'B365H', 'B365D', 'B365A']
    if not all(col in df.columns for col in required_cols):
        st.error("El CSV debe incluir las columnas: " + ", ".join(required_cols))
    else:
        st.success("Datos cargados correctamente ✅")
        
        # Calcular promedios globales
        avg_home_goals = df['FTHG'].mean()
        avg_away_goals = df['FTAG'].mean()

        # Calcular ataque y defensa para cada equipo
        teams = df['HomeTeam'].unique()
        stats = {}

        for team in teams:
            home = df[df['HomeTeam'] == team]
            away = df[df['AwayTeam'] == team]
            
            att_home = home['FTHG'].mean() / avg_home_goals
            def_home = home['FTAG'].mean() / avg_away_goals
            att_away = away['FTAG'].mean() / avg_away_goals
            def_away = away['FTHG'].mean() / avg_home_goals
            
            stats[team] = {
                'att_home': att_home,
                'def_home': def_home,
                'att_away': att_away,
                'def_away': def_away,
            }

        st.markdown("### 🧮 Resultados:")
        result_table = []

        for idx, row in df.iterrows():
            home, away = row['HomeTeam'], row['AwayTeam']
            if home not in stats or away not in stats:
                continue

            exp_home_goals = stats[home]['att_home'] * stats[away]['def_away'] * avg_home_goals
            exp_away_goals = stats[away]['att_away'] * stats[home]['def_home'] * avg_away_goals

            # Calcular probabilidades 1X2 usando Poisson
            max_goals = 5
            prob_home_win = prob_draw = prob_away_win = 0.0

            for i in range(0, max_goals+1):
                for j in range(0, max_goals+1):
                    p = poisson.pmf(i, exp_home_goals) * poisson.pmf(j, exp_away_goals)
                    if i > j:
                        prob_home_win += p
                    elif i == j:
                        prob_draw += p
                    else:
                        prob_away_win += p

            probs = [prob_home_win, prob_draw, prob_away_win]
            odds_model = [round(1/p, 2) if p > 0 else 100 for p in probs]
            odds_real = [row['B365H'], row['B365D'], row['B365A']]

            value = []
            for m, r in zip(odds_model, odds_real):
                expected_value = (1/m) * r - 1
                value.append(round(expected_value, 2))

            result_table.append({
                "Partido": f"{home} vs {away}",
                "EV 1": value[0],
                "EV X": value[1],
                "EV 2": value[2],
                "Value Bet": (
                    "1" if value[0] > 0 else
                    "X" if value[1] > 0 else
                    "2" if value[2] > 0 else "-"
                )
            })

        st.dataframe(pd.DataFrame(result_table))