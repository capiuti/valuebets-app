import streamlit as st
import pandas as pd

st.set_page_config(page_title="Value Bets App", layout="wide")
st.title("📊 Análisis de Ligas Europeas de Fútbol")

# Diccionario para mapear códigos de archivo a (país, liga)
league_mapping = {
    'E0': ('Inglaterra', 'Premier League'),
    'E1': ('Inglaterra', 'Championship'),
    'E2': ('Inglaterra', 'League One'),
    'E3': ('Inglaterra', 'League Two'),
    'EC': ('Inglaterra', 'National League'),
    'SC0': ('Escocia', 'Premiership'),
    'SC1': ('Escocia', 'Championship'),
    'SC2': ('Escocia', 'League One'),
    'SC3': ('Escocia', 'League Two'),
    'D1': ('Alemania', 'Bundesliga'),
    'D2': ('Alemania', 'Bundesliga 2'),
    'SP1': ('España', 'La Liga'),
    'SP2': ('España', 'Liga Hypermotion'),
    'I1': ('Italia', 'Serie A'),
    'I2': ('Italia', 'Serie B'),
    'F1': ('Francia', 'Ligue 1'),
    'F2': ('Francia', 'Ligue 2'),
    'B1': ('Bélgica', 'Jupiler Pro League'),
    'N1': ('Países Bajos', 'Eredivisie'),
    'P1': ('Portugal', 'Liga Portugal'),
    'T1': ('Turquía', 'Super Lig'),
    'G1': ('Grecia', 'Superliga'),
}

uploaded_files = st.file_uploader("📂 Carga tus archivos CSV (varios)", type="csv", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        code = file.name.split('.')[0].upper()
        country, league = league_mapping.get(code, ('Desconocido', 'Desconocida'))
        try:
            df = pd.read_csv(file, sep=';')
            if df.shape[1] <= 1:
                file.seek(0)
                df = pd.read_csv(file, sep=',')
            df['Country'] = country
            df['League'] = league
            df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
            df['Goals_Total'] = df['FTHG'] + df['FTAG']
            df['Goal_Diff'] = df['FTHG'] - df['FTAG']
            dfs.append(df)
        except Exception as e:
            st.warning(f"⚠️ Error al leer {file.name}: {e}")

    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)
        full_df = full_df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])

        tab1, tab2, tab3 = st.tabs(["🏆 Por Liga", "🌍 Por País", "⚽ Por Equipo"])

        with tab1:
            st.subheader("Filtrar por Liga")
            leagues = sorted(full_df['League'].dropna().unique())
            selected_league = st.selectbox("Selecciona una liga", leagues)
            df_league = full_df[full_df['League'] == selected_league]

            st.metric("📈 Promedio de Goles por Partido", round(df_league['Goals_Total'].mean(), 2))
            st.dataframe(df_league[['Date', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'Goals_Total']], use_container_width=True)

        with tab2:
            st.subheader("Filtrar por País")
            countries = sorted(full_df['Country'].dropna().unique())
            selected_country = st.selectbox("Selecciona un país", countries)
            df_country = full_df[full_df['Country'] == selected_country]

            st.metric("⚽ Total de Partidos", len(df_country))
            st.dataframe(df_country[['Date', 'League', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']], use_container_width=True)

        with tab3:
            st.subheader("Filtrar por Equipo")
            teams = sorted(pd.concat([full_df['HomeTeam'], full_df['AwayTeam']]).dropna().unique())
            selected_team = st.selectbox("Selecciona un equipo", teams)
            df_team = full_df[(full_df['HomeTeam'] == selected_team) | (full_df['AwayTeam'] == selected_team)]

            avg_goals = df_team['Goals_Total'].mean()
            win_home = df_team[df_team['HomeTeam'] == selected_team]['FTR'].value_counts().get('H', 0)
            win_away = df_team[df_team['AwayTeam'] == selected_team]['FTR'].value_counts().get('A', 0)
            total_games = len(df_team)
            win_rate = (win_home + win_away) / total_games * 100 if total_games > 0 else 0

            st.metric("⚽ Promedio Goles por Partido", round(avg_goals, 2))
            st.metric("🏅 Ratio de Victoria", f"{win_rate:.1f}%")
            st.dataframe(df_team[['Date', 'League', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR']], use_container_width=True)

else:
    st.info("👆 Sube tus archivos CSV históricos para comenzar.")


