import streamlit as st
import pandas as pd
from scipy.stats import poisson
import csv

st.set_page_config(page_title="Value Bets Poisson", layout="wide")
st.title("⚽ Modelo de Apuestas Value (Poisson)")

# 🔄 Subida de múltiples archivos CSV
uploaded_files = st.file_uploader("📂 Sube varios archivos CSV de partidos históricos", type=["csv"], accept_multiple_files=True)

if uploaded_files:
    dfs = []

    for file in uploaded_files:
        sample = file.read(1024).decode("utf-8")
        file.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample)
            sep = dialect.delimiter
        except:
            sep = ';'

        try:
            df_temp = pd.read_csv(file, sep=sep)
            dfs.append(df_temp)
        except Exception as e:
            st.warning(f"❌ Error al cargar {file.name}: {e}")

    if dfs:
        df = pd.concat(dfs, ignore_index=True)

        # Mostrar preview
        st.subheader("🔍 Vista previa de los datos combinados")
        st.dataframe(df.head())

        # Comprobación de columnas necesarias
        required_cols = ['FTHG', 'FTAG', 'B365H', 'B365D', 'B365A']
        if not all(col in df.columns for col in required_cols):
            st.error("🚫 Faltan columnas necesarias en al menos uno de los archivos: " + ", ".join(required_cols))
        else:
            # Calcular medias
            home_avg = df['FTHG'].mean()
            away_avg = df['FTAG'].mean()

            st.write(f"⚙️ Media de goles local: **{home_avg:.2f}**")
            st.write(f"⚙️ Media de goles visitante: **{away_avg:.2f}**")

            # Probabilidades estimadas por modelo Poisson
            max_goals = 5
            home_probs = [poisson.pmf(i, home_avg) for i in range(max_goals + 1)]
            away_probs = [poisson.pmf(i, away_avg) for i in range(max_goals + 1)]

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

            st.subheader("💰 Value Bets detectadas")
            value_bets = []

            for idx, row in df.iterrows():
                try:
                    h_odd = float(row['B365H'])
                    d_odd = float(row['B365D'])
                    a_odd = float(row['B365A'])
                except (ValueError, TypeError, KeyError):
                    continue

                if h_odd > 0 and prob_home > 1 / h_odd:
                    value_bets.append(f"Partido {idx + 1}: Apostar a 🏠 LOCAL @ {h_odd:.2f}")
                if d_odd > 0 and prob_draw > 1 / d_odd:
                    value_bets.append(f"Partido {idx + 1}: Apostar a 🤝 EMPATE @ {d_odd:.2f}")
                if a_odd > 0 and prob_away > 1 / a_odd:
                    value_bets.append(f"Partido {idx + 1}: Apostar a 🚗 VISITANTE @ {a_odd:.2f}")

            if value_bets:
                for vb in value_bets:
                    st.write("✅", vb)
            else:
                st.info("No se detectaron apuestas con valor en estos datos.")
    else:
        st.error("No se pudo cargar ningún archivo válido.")
