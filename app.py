import streamlit as st
import pandas as pd
from scipy.stats import poisson

st.set_page_config(page_title="Value Bets + Filtros", layout="wide")
st.title("⚽ Value Bets con filtros por País, Liga y Equipo")

uploaded_files = st.file_uploader(
    "📂 Sube archivos CSV", 
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
            st.warning(f"Error cargando {file.name}: {e}")

    if dfs:
        df = pd.concat(dfs, ignore_index=True)

        # Verificamos columnas importantes, incluyendo Country y League
        required_cols = ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'B365H', 'B365D', 'B365A']
        extra_cols = ['Country', 'League']
        missing = [col for col in required_cols if col not in df.columns]
        if missing:
            st.error(f"Faltan columnas obligatorias: {', '.join(missing)}")
        else:
            if not all(col in df.columns for col in extra_cols):
                st.warning("Las columnas 'Country' y/o 'League' no están presentes, los filtros serán limitados.")
                df['Country'] = 'Desconocido'
                df['League'] = 'Desconocida'

            # Filtros por país y liga
            countries = sorted(df['Country'].dropna().unique())
            country_filter = st.sidebar.selectbox("Selecciona País", ["Todos"] + countries)

            if country_filter != "Todos":
                df_filtered = df[df['Country'] == country_filter]
            else:
                df_filtered = df.copy()

            leagues = sorted(df_filtered['League'].dropna().unique())
            league_filter = st.sidebar.selectbox("Selecciona Liga", ["Todas"] + leagues)

            if league_filter != "Todas":
                df_filtered = df_filtered[df_filtered['League'] == league_filter]

            # Equipos filtrados por la selección previa
            teams = sorted(pd.unique(df_filtered[['HomeTeam', 'AwayTeam']].values.ravel()))
            home_team = st.sidebar.selectbox("Equipo LOCAL", teams)
            away_team = st.sidebar.selectbox("Equipo VISITANTE", teams)

            # Estadísticas y predicción igual que antes, pero usando df_filtered
            home_stats = df_filtered[df_filtered['HomeTeam'] == home_team]
            away_stats = df_filtered[df_filtered['AwayTeam'] == away_team]

            home_avg_goals = home_stats['FTHG'].mean()
            away_avg_goals = away_stats['FTAG'].mean()

            st.write(f"Goles promedio local ({home_team}): {home_avg_goals:.2f}")
            st.write(f"Goles promedio visitante ({away_team}): {away_avg_goals:.2f}")

            max_goals = 5
            home_goal_probs = [poisson.pmf(i, home_avg_goals) for i in range(max_goals + 1)]
            away_goal_probs = [poisson.pmf(i, away_avg_goals) for i in range(max_goals + 1)]

            prob_home_win = sum(
                home_goal_probs[hg] * away_goal_probs[ag]
                for hg in range(max_goals + 1)
                for ag in range(max_goals + 1)
                if hg > ag
            )
            prob_draw = sum(
                home_goal_probs[hg] * away_goal_probs[ag]
                for hg in range(max_goals + 1)
                for ag in range(max_goals + 1)
                if hg == ag
            )
            prob_away_win = sum(
                home_goal_probs[hg] * away_goal_probs[ag]
                for hg in range(max_goals + 1)
                for ag in range(max_goals + 1)
                if hg < ag
            )

            st.write(f"Probabilidad local: {prob_home_win:.2%}")
            st.write(f"Probabilidad empate: {prob_draw:.2%}")
            st.write(f"Probabilidad visitante: {prob_away_win:.2%}")

            odd_home = st.number_input(f"Cuota victoria local ({home_team})", 1.0, 10.0, 2.0, 0.01)
            odd_draw = st.number_input("Cuota empate", 1.0, 10.0, 3.0, 0.01)
            odd_away = st.number_input(f"Cuota victoria visitante ({away_team})", 1.0, 10.0, 2.5, 0.01)

            value_bets = []
            if prob_home_win > 1 / odd_home:
                value_bets.append(f"Apostar a local {home_team} @ {odd_home} (Value)")
            if prob_draw > 1 / odd_draw:
                value_bets.append(f"Apostar a empate @ {odd_draw} (Value)")
            if prob_away_win > 1 / odd_away:
                value_bets.append(f"Apostar a visitante {away_team} @ {odd_away} (Value)")

            if value_bets:
                st.success("Apuestas con valor detectadas:")
                for v in value_bets:
                    st.write("✅", v)
            else:
                st.info("No hay apuestas con valor para estas cuotas.")

    else:
        st.error("No se cargaron archivos válidos.")





