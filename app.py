import streamlit as st
import pandas as pd
from scipy.stats import poisson
import csv

st.title("⚽ Modelo de Apuestas Value (Poisson)")

uploaded_file = st.file_uploader("📂 Sube tu archivo CSV de partidos", type=["csv"])

if uploaded_file is not None:
    # Detectar el separador automáticamente
    sample = uploaded_file.read(1024).decode("utf-8")
    uploaded_file.seek(0)
    try:
        dialect = csv.Sniffer().sniff(sample)
        sep = dialect.delimiter
    except:
        sep = ';'  # por defecto si falla

    df = pd.read_csv(uploaded_file, sep=sep)

    # Mostrar las primeras filas
    st.subheader("🔍 Vista previa del archivo")
    st.dataframe(df.head())

    # Calcular medias de goles
    home_goals_avg = df['FTHG'].mean()
    away_goals_avg = df['FTAG'].mean()

    st.write(f"Media de goles local: {home_goals_avg:.2f}")
    st.write(f"Media de goles visitante: {away_goals_avg:.2f}")

    # Modelo Poisson para hasta 5 goles
    max_goals = 5
    home_probs = [poisson.pmf(i, home_goals_avg) for i in range(max_goals + 1)]
    away_probs = [poisson.pmf(i, away_goals_avg) for i in range(max_goals + 1)]

    prob_home, prob_draw, prob_away = 0, 0, 0

    for hg in range(max_goals + 1):
        for ag in range(max_goals + 1):
            p = home_probs[hg] * away_probs[ag]
            if hg > ag:
                prob_home += p
            elif hg == ag:
                prob_draw += p
            else:
                prob_away += p

    st.subheader("📊 Probabilidades estimadas (modelo Poisson)")
    st.write(f"🏠 Gana LOCAL: {prob_home:.2%}")
    st.write(f"🤝 EMPATE: {prob_draw:.2%}")
    st.write(f"🚗 Gana VISITANTE: {prob_away:.2%}")

    # Detectar apuestas con value
    st.subheader("💰 Value Bets sugeridas:")

    value_bets = []

    for idx, row in df.iterrows():
        try:
            home_odd = float(row['B365H'])
            draw_odd = float(row['B365D'])
            away_odd = float(row['B365A'])
        except (ValueError, TypeError, KeyError):
            continue

        if home_odd > 0 and prob_home > 1 / home_odd:
            value_bets.append(f"Partido {idx + 1}: Apostar a 🏠 LOCAL @ {home_odd:.2f}")
        if draw_odd > 0 and prob_draw > 1 / draw_odd:
            value_bets.append(f"Partido {idx + 1}: Apostar a 🤝 EMPATE @ {draw_odd:.2f}")
        if away_odd > 0 and prob_away > 1 / away_odd:
            value_bets.append(f"Partido {idx + 1}: Apostar a 🚗 VISITANTE @ {away_odd:.2f}")

    if value_bets:
        for vb in value_bets:
            st.write(vb)
    else:
        st.info("No se detectaron apuestas con valor en este dataset.")

    if value_bets:
        for bet in value_bets:
            st.write(bet)
    else:
        st.write("No se detectaron apuestas con value en este dataset.")
