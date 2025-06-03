import streamlit as st
import pandas as pd

st.set_page_config(page_title="Análisis Total Futbol", layout="wide")
st.title("⚽ Análisis Detallado de Partidos - Ligas Europeas")

# Diccionario de código de archivo -> (País, Liga)
league_mapping = {
    'E0': ('Inglaterra', 'Premier League'), 'E1': ('Inglaterra', 'Championship'),
    'E2': ('Inglaterra', 'League One'), 'E3': ('Inglaterra', 'League Two'),
    'EC': ('Inglaterra', 'National League'), 'SC0': ('Escocia', 'Premiership'),
    'SC1': ('Escocia', 'Championship'), 'SC2': ('Escocia', 'League One'),
    'SC3': ('Escocia', 'League Two'), 'D1': ('Alemania', 'Bundesliga'),
    'D2': ('Alemania', 'Bundesliga 2'), 'SP1': ('España', 'La Liga'),
    'SP2': ('España', 'Liga Hypermotion'), 'I1': ('Italia', 'Serie A'),
    'I2': ('Italia', 'Serie B'), 'F1': ('Francia', 'Ligue 1'),
    'F2': ('Francia', 'Ligue 2'), 'B1': ('Bélgica', 'Jupiler Pro League'),
    'N1': ('Países Bajos', 'Eredivisie'), 'P1': ('Portugal', 'Liga Portugal'),
    'T1': ('Turquía', 'Super Lig'), 'G1': ('Grecia', 'Superliga'),
}

uploaded_files = st.file_uploader("📂 Sube tus archivos CSV históricos", type="csv", accept_multiple_files=True)

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
            st.warning(f"⚠️ Error leyendo {file.name}: {e}")

    if dfs:
        full_df = pd.concat(dfs, ignore_index=True)
        full_df = full_df.dropna(subset=["Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG"])

        tab1, tab2, tab3, tab4 = st.tabs(["🏆 Por Liga", "🌍 Por País", "⚽ Por Equipo", "📊 Estadísticas Detalladas"])

        with tab1:
            st.subheader("Filtrar por Liga")
            leagues = sorted(full_df['League'].dropna().unique())
            league = st.selectbox("Selecciona una liga", leagues)
            st.dataframe(full_df[full_df['League'] == league], use_container_width=True)

        with tab2:
            st.subheader("Filtrar por País")
            countries = sorted(full_df['Country'].dropna().unique())
            country = st.selectbox("Selecciona un país", countries)
            st.dataframe(full_df[full_df['Country'] == country], use_container_width=True)

        with tab3:
            st.subheader("Filtrar por Equipo")
            teams = sorted(pd.concat([full_df['HomeTeam'], full_df['AwayTeam']]).dropna().unique())
            team = st.selectbox("Selecciona un equipo", teams)
            df_team = full_df[(full_df['HomeTeam'] == team) | (full_df['AwayTeam'] == team)]

            st.metric("Partidos jugados", len(df_team))
            st.metric("Media de goles totales", round(df_team['Goals_Total'].mean(), 2))
            st.metric("Ratio de victoria", f"{100 * ((df_team['HomeTeam'] == team) & (df_team['FTR'] == 'H')).sum() + ((df_team['AwayTeam'] == team) & (df_team['FTR'] == 'A')).sum() / len(df_team):.1f}%" if len(df_team) > 0 else "0%")

            st.dataframe(df_team, use_container_width=True)

        with tab4:
            st.subheader("📊 Estadísticas Detalladas + Cuotas")

            # Columnas seleccionables
            default_cols = ['Date', 'League', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG', 'FTR', 'Goals_Total', 'Goal_Diff']
            extra_stats = ['HTHG', 'HTAG', 'HTR', 'Referee', 'HS', 'AS', 'HST', 'AST', 'HF', 'AF', 'HC', 'AC', 'HY', 'AY', 'HR', 'AR']
            odds_cols = [col for col in full_df.columns if 'B365' in col or 'PS' in col or 'WH' in col or 'VC' in col]

            selected_cols = st.multiselect("Selecciona columnas adicionales", extra_stats + odds_cols, default=odds_cols[:3])
            show_df = full_df[default_cols + selected_cols]
            st.dataframe(show_df, use_container_width=True)

else:
    st.info("👆 Sube tus archivos CSV para comenzar.")



