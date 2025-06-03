
import streamlit as st
import pandas as pd
from scipy.stats import poisson

st.title("Modelo de Value Bets con Poisson")

uploaded_file = st.file_uploader("Sube tu archivo CSV con datos de partidos", type=["csv"])

if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, sep=';')
    st.write("Vista previa del archivo cargado:")
    st.dataframe(df.head())

    # Usamos las columnas adecuadas para goles y cuotas Bet365
    home_goals_avg = df['FTHG'].mean()
    away_goals_avg = df['FTAG'].mean()

    st.write(f"Media goles local: {home_goals_avg:.2f}")
    st.write(f"Media goles visitante: {away_goals_avg:.2f}")

    max_goals = 5

    home_goals_probs = [poisson.pmf(i, home_goals_avg) for i in range(max_goals+1)]
    away_goals_probs = [poisson.pmf(i, away_goals_avg) for i in range(max_goals+1)]

    prob_home_win = 0
    prob_draw = 0
    prob_away_win = 0

    for hg in range(max_goals+1):
        for ag in range(max_goals+1):
            p = home_goals_probs[hg] * away_goals_probs[ag]
            if hg > ag:
                prob_home_win += p
            elif hg == ag:
                prob_draw += p
            else:
                prob_away_win += p

    st.write(f"Probabilidad estimada local gana: {prob_home_win:.2%}")
    st.write(f"Probabilidad estimada empate: {prob_draw:.2%}")
    st.write(f"Probabilidad estimada visitante gana: {prob_away_win:.2%}")

    value_bets = []

    for idx, row in df.iterrows():
        home_odd = row.get('B365H', None)
        draw_odd = row.get('B365D', None)
        away_odd = row.get('B365A', None)

        if home_odd and home_odd > 0:
            implied_prob = 1 / home_odd
            if prob_home_win > implied_prob:
                value_bets.append(f"Partido {idx+1}: Apostar a LOCAL, cuota {home_odd}")

        if draw_odd and draw_odd > 0:
            implied_prob = 1 / draw_odd
            if prob_draw > implied_prob:
                value_bets.append(f"Partido {idx+1}: Apostar a EMPATE, cuota {draw_odd}")

        if away_odd and away_odd > 0:
            implied_prob = 1 / away_odd
            if prob_away_win > implied_prob:
                value_bets.append(f"Partido {idx+1}: Apostar a VISITANTE, cuota {away_odd}")

    st.write("### Value bets detectadas:")
    if value_bets:
        for bet in value_bets:
            st.write(bet)
    else:
        st.write("No se detectaron apuestas con value en este dataset.")
