import streamlit as st
import pandas as pd

st.set_page_config(page_title="Value Bets App", layout="wide")
st.title("📊 Análisis de Ligas Europeas de Fútbol")

# Diccionario para mapear código -> (País, Liga)
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

# Subida de archivos CSV
uploaded_files = st.file_uploader("📂 Carga tus archivos CSV de ligas", type="csv", accept_multiple_files=True)

if uploaded_files:
    dfs = []
    for file in uploaded_files:
        filename = file.name.split('.')[0]
        country, league = league_mapping.get(filename, ('Desconocido', 'Desconocida'))

        try:
            df = pd.read_csv(file, sep=';')
            if df.shape[1] <= 1:
                file.seek(0)
                df = pd.read_csv(file, sep=',')
        except Exception as e:
            st.error(f"Error al cargar {file.name}: {e}")
            continue

        df['Country'] = country
        df['League'] = league
        df['Date'] = pd.to_datetime(df['Date'], dayfirst=True, errors='coerce')
        df['Goals_Total'] = df['FTHG'] + df['FTAG']
        df['Goal_Diff'] = df['FTHG'] - df['FTAG']
        dfs.append(df)

    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)

        # Filtros
        st.sidebar.header("Filtros")
        country_sel = st.sidebar.multiselect("🌍 País", full_df['Country'].unique())
        league_sel = st.sidebar.multiselect("🏆 Liga", full_df['League'].unique())
        team_sel = st.sidebar.multiselect("⚽ Equipo (local o visitante)", 
                                          sorted(pd.concat([full_df['HomeTeam'], full_df['AwayTeam']]).unique()))

        df_filtered = full_df.copy()
        if country_sel:
            df_filtered = df_filtered[df_filtered['Country'].isin(country_sel)]
        if league_sel:
            df_filtered = df_filtered[df_filtered['League'].isin(league_sel)]
        if team_sel:
            df_filtered = df_filtered[df_filtered['HomeTeam'].isin(team_sel) | df_filtered['AwayTeam'].isin(team_sel)]

        st.markdown("### 🧾 Resultados Filtrados")
        st.dataframe(df_filtered[['Date', 'Country', 'League', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'Goals_Total', 'Goal_Diff', 'FTR']].sort_values(by='Date', ascending=False), use_container_width=True)

        st.markdown("### 📈 Estadísticas")
        avg_goals = df_filtered['Goals_Total'].mean()
        home_wins = (df_filtered['FTR'] == 'H').sum()
        draw = (df_filtered['FTR'] == 'D').sum()
        away_wins = (df_filtered['FTR'] == 'A').sum()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Media de goles", f"{avg_goals:.2f}")
        col2.metric("🏠 Victorias Local", home_wins)
        col3.metric("🤝 Empates", draw)
        col4.metric("🚌 Victorias Visitante", away_wins)

    else:
        st.warning("⚠️ No se pudo cargar ningún archivo válido.")
else:
    st.info("👆 Carga archivos CSV históricos de ligas europeas para comenzar.")

