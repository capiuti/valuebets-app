import streamlit as st
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Value Bets Poisson + Stats", layout="wide")
st.title("⚽ Modelo Value Bets con estadísticas personalizadas")

uploaded_files = st.file_uploader(
    "📂 Sube varios archivos CSV con datos históricos", 
    type=["csv"], 
    accept_multiple_files=True
)

if uploaded_files:
    dfs = []

    for file in uploaded_files:
        try:
            df_temp = pd.read_csv(file, sep=';')
            if df_temp.shape[1] <= 1:
                file.seek(0)
                df_temp = pd.read_csv(file, sep=',')
            dfs.append(df_temp)
        except Exception as e:
            st.warning(f"❌ Error al cargar {file.name}: {e}")

    if dfs:
        df = pd.concat(dfs, ignore_index=True)

        st.subheader("🔍 Vista previa de datos")
        st.dataframe(df.head())

        required_cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'B365H', 'B365D', 'B365A']
        if not all(col in df.columns for col in required_cols):
            st.error(f"Faltan columnas necesarias: {', '.join(required_cols)}")
        else:
            teams = sorted(pd.unique(df[['HomeTeam', 'AwayTeam']].values.ravel()))

            st.sidebar.header("⚙️ Configuración del partido a predecir")
            home_team = st.sidebar.selectbox("Equipo LOCAL", teams)
            away_team = st.sidebar.selectbox("Equipo VISITANTE", teams)

            # Filtrar partidos con estos equipos para estadísticas
            home_stats = df[df['HomeTeam'] == home_team]
            away_stats = df[df['AwayTeam'] == away_team]

            # Goles promedio (local y visitante)
            home_avg_goals = home_stats['FTHG'].mean()
            away_avg_goals = away_stats['FTAG'].mean()

            # Estadísticas adicionales si están disponibles
            extra_stats = {}
            extras = {
                "Tiros local (HS)": "HS",
                "Tiros visitante (AS)": "AS",
                "Tiros a puerta local (HST)": "HST",
                "Tiros a puerta visitante (AST)": "AST",
                "Faltas local (HF)": "HF",
                "Faltas visitante (AF)": "AF",
                "Tarjetas amarillas local (HY)": "HY",
                "Tarjetas amarillas visitante (AY)": "AY"
            }
            for label, col in extras.items():
                if col in df.columns:
                    extra_stats[label] = (
                        home_stats[col].mean(),
                        away_stats[col].mean()
                    )

            st.subheader("📊 Estadísticas promedio para el partido")
            st.write(f"⚽ Goles promedio local ({home_team}): **{home_avg_goals:.2f}**")
            st.write(f"⚽ Goles promedio visitante ({away_team}): **{away_avg_goals:.2f}**")

            for stat_label, (home_val, away_val) in extra_stats.items():
                st.write(f"{stat_label}: local {home_val:.1f} | visitante {away_val:.1f}")

            # Modelo Poisson para probabilidades
            max_goals = 5
            home_goal_probs = [poisson.pmf(i, home_avg_goals) for i in range(max_goals + 1)]
            away_goal_probs = [poisson.pmf(i, away_avg_goals) for i in range(max_goals + 1)]

            prob_home_win = 0
            prob_draw = 0
            prob_away_win = 0

            for hg in range(max_goals + 1):
                for ag in range(max_goals + 1):
                    p = home_goal_probs[hg] * away_goal_probs[ag]
                    if hg > ag:
                        prob_home_win += p
                    elif hg == ag:
                        prob_draw += p
                    else:
                        prob_away_win += p

            st.subheader("📈 Probabilidades estimadas")
            st.write(f"🏠 Gana local ({home_team}): {prob_home_win:.2%}")
            st.write(f"🤝 Empate: {prob_draw:.2%}")
            st.write(f"🚗 Gana visitante ({away_team}): {prob_away_win:.2%}")

            st.subheader("💸 Introduce cuotas para detectar Value Bets")
            odd_home = st.number_input(f"Cuota victoria local ({home_team})", min_value=1.0, step=0.01, format="%.2f")
            odd_draw = st.number_input("Cuota empate", min_value=1.0, step=0.01, format="%.2f")
            odd_away = st.number_input(f"Cuota victoria visitante ({away_team})", min_value=1.0, step=0.01, format="%.2f")

            value_bets = []
            if odd_home > 0 and prob_home_win > 1 / odd_home:
                value_bets.append(f"🏠 Apostar a LOCAL {home_team} @ {odd_home} (Value Bet!)")
            if odd_draw > 0 and prob_draw > 1 / odd_draw:
                value_bets.append(f"🤝 Apostar a EMPATE @ {odd_draw} (Value Bet!)")
            if odd_away > 0 and prob_away_win > 1 / odd_away:
                value_bets.append(f"🚗 Apostar a VISITANTE {away_team} @ {odd_away} (Value Bet!)")

            if value_bets:
                st.success("✅ ¡Se detectaron apuestas con valor!")
                for vb in value_bets:
                    st.write(vb)
            else:
                st.info("No hay apuestas con valor detectadas con las cuotas actuales.")

    else:
        st.error("No se pudo cargar ningún archivo válido.")
