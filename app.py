import streamlit as st
import pandas as pd
from scipy.stats import poisson
import datetime
import random

# --- CONFIGURACION INICIAL ---
st.set_page_config(page_title="Value Bets Poisson + Stats", layout="wide")
st.title("⚽ Value Bets: Manual + Datos en Tiempo Real (Simulados)")

st.sidebar.header("⚙️ Modo de Uso")
mode = st.sidebar.radio("Selecciona modo:", ["Manual (CSV)", "Automático (Partidos diarios simulados)"])

# --- FUNCION CALCULO POISSON ---
def calcular_probabilidades(local_goles, visitante_goles, max_goals=5):
    p_home = [poisson.pmf(i, local_goles) for i in range(max_goals + 1)]
    p_away = [poisson.pmf(i, visitante_goles) for i in range(max_goals + 1)]

    win, draw, lose = 0, 0, 0
    for hg in range(max_goals + 1):
        for ag in range(max_goals + 1):
            p = p_home[hg] * p_away[ag]
            if hg > ag:
                win += p
            elif hg == ag:
                draw += p
            else:
                lose += p
    return win, draw, lose

# --- MODO MANUAL CON CSV ---
if mode == "Manual (CSV)":
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
                df_temp['Liga'] = file.name.split('.')[0]  # Extraer nombre del archivo
                dfs.append(df_temp)
            except Exception as e:
                st.warning(f"❌ Error al cargar {file.name}: {e}")

        if dfs:
            df = pd.concat(dfs, ignore_index=True)

            st.subheader("🔍 Vista previa de datos")
            st.dataframe(df.head())

            ligas = sorted(df['Liga'].unique())
            selected_liga = st.sidebar.selectbox("Filtrar por liga (nombre de archivo):", ligas)

            filtered_df = df[df['Liga'] == selected_liga]
            equipos = sorted(pd.unique(filtered_df[['HomeTeam', 'AwayTeam']].values.ravel()))

            home_team = st.sidebar.selectbox("Equipo LOCAL", equipos)
            away_team = st.sidebar.selectbox("Equipo VISITANTE", equipos)

            home_stats = filtered_df[filtered_df['HomeTeam'] == home_team]
            away_stats = filtered_df[filtered_df['AwayTeam'] == away_team]

            home_avg_goals = home_stats['FTHG'].mean()
            away_avg_goals = away_stats['FTAG'].mean()

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
                if col in filtered_df.columns:
                    extra_stats[label] = (
                        home_stats[col].mean(),
                        away_stats[col].mean()
                    )

            st.subheader("📊 Estadísticas promedio")
            st.write(f"⚽ Goles promedio local ({home_team}): **{home_avg_goals:.2f}**")
            st.write(f"⚽ Goles promedio visitante ({away_team}): **{away_avg_goals:.2f}**")
            for label, (hval, aval) in extra_stats.items():
                st.write(f"{label}: Local {hval:.1f} | Visitante {aval:.1f}")

            ph, pd, pa = calcular_probabilidades(home_avg_goals, away_avg_goals)
            st.subheader("📈 Probabilidades estimadas")
            st.write(f"🏠 Gana local: {ph:.2%}")
            st.write(f"🤝 Empate: {pd:.2%}")
            st.write(f"🚗 Gana visitante: {pa:.2%}")

            st.subheader("💸 Introduce cuotas")
            odd_home = st.number_input(f"Cuota victoria local", min_value=1.0, step=0.01)
            odd_draw = st.number_input(f"Cuota empate", min_value=1.0, step=0.01)
            odd_away = st.number_input(f"Cuota victoria visitante", min_value=1.0, step=0.01)

            st.subheader("📌 Apuestas de Valor")
            if ph > 1/odd_home:
                st.success(f"🏠 Apostar a LOCAL @ {odd_home:.2f} ✓")
            if pd > 1/odd_draw:
                st.success(f"🤝 Apostar a EMPATE @ {odd_draw:.2f} ✓")
            if pa > 1/odd_away:
                st.success(f"🚗 Apostar a VISITANTE @ {odd_away:.2f} ✓")

# --- MODO AUTOMATICO SIMULADO ---
else:
    st.subheader("📅 Partidos diarios simulados (modo automático)")
    partidos = [
        {"fecha": datetime.date.today(), "local": "Real Madrid", "visitante": "Barcelona"},
        {"fecha": datetime.date.today(), "local": "Man City", "visitante": "Liverpool"},
        {"fecha": datetime.date.today(), "local": "PSG", "visitante": "Marseille"},
    ]

    simulaciones = []
    for partido in partidos:
        gl = random.uniform(1.0, 2.2)
        gv = random.uniform(0.7, 1.7)
        cl = round(random.uniform(1.5, 2.5), 2)
        cd = round(random.uniform(3.0, 3.8), 2)
        cv = round(random.uniform(2.7, 3.8), 2)

        pl, pd, pv = calcular_probabilidades(gl, gv)

        valor = ""
        color = "white"
        if pl > 1/cl:
            valor = f"🏠 LOCAL {partido['local']}"
            color = "lightgreen"
        elif pd > 1/cd:
            valor = f"🤝 EMPATE"
            color = "khaki"
        elif pv > 1/cv:
            valor = f"🚗 VISITANTE {partido['visitante']}"
            color = "lightgreen"
        else:
            color = "lightcoral"

        simulaciones.append({
            "Partido": f"{partido['local']} vs {partido['visitante']}",
            "Prob Local": f"{pl:.1%}",
            "Prob Empate": f"{pd:.1%}",
            "Prob Visitante": f"{pv:.1%}",
            "Cuota L": cl,
            "Cuota D": cd,
            "Cuota V": cv,
            "Value Bet": valor,
            "Color": color
        })

    for sim in simulaciones:
        st.markdown(f"### {sim['Partido']}")
        st.markdown(f"<div style='background-color:{sim['Color']}; padding:10px; border-radius:10px'>"
                    f"<b>Probabilidades:</b> Local {sim['Prob Local']} | Empate {sim['Prob Empate']} | Visitante {sim['Prob Visitante']}<br>"
                    f"<b>Cuotas:</b> L {sim['Cuota L']} | D {sim['Cuota D']} | V {sim['Cuota V']}<br>"
                    f"<b>Apuesta de Valor:</b> {sim['Value Bet'] if sim['Value Bet'] else 'Ninguna'}"
                    f"</div><br>", unsafe_allow_html=True)

