
import os
import sys
import locale
locale.setlocale(locale.LC_TIME, 'it_IT.UTF-8')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from danilib import f_settaggio_db_arpal
connessione = f_settaggio_db_arpal()

sys.path.insert(0, os.path.expanduser('~/.config'))
from config_percorsi_Daniele import CARTELLA_REPO_ROOT

cartella_lavoro = os.path.join(CARTELLA_REPO_ROOT, 'estrazioni_EPS')
os.chdir(cartella_lavoro)

from funzioni import f_calcola_rank

# %% Plot semplici

stazione = 'CFUNZ'
# lista_date = pd.date_range('2020-01-01', '2020-03-15', freq='1d')
lista_date = [pd.Timestamp('2020-07-20')]

for data in lista_date:
    file = f"{cartella_lavoro}/output/2t/{stazione}/{data.strftime('%Y-%m-%d')}.csv"
    
    df = pd.read_csv(file, index_col=0, parse_dates=True) - 273.15
    
    t0 = df.index.min()
    t1 = df.index.max()
    query_obs = f"""
    SELECT
        TO_CHAR(data.dtrf, 'YYYY-MM-DD HH24:MI:SS') AS tempo,
        anag.code,
        anag.lon/1e5 AS lon,
        anag.lat/1e5 AS lat,
        anag.elev AS elev,
        anag.name AS name,
        tempm/10 AS TMEAN
    FROM
        data
    JOIN
        anag ON data.code = anag.code
    WHERE
        tempm IS NOT NULL
        AND data.code = '{stazione}'
        AND data.dtrf BETWEEN TO_DATE('{t0:%Y%m%d%H%M}', 'YYYYMMDDHH24MI')
                          AND TO_DATE('{t1:%Y%m%d%H%M}', 'YYYYMMDDHH24MI')
    ORDER BY
        data.dtrf
    """
    df_obs = pd.read_sql(query_obs, con=connessione)
    df_obs = df_obs.set_index('TEMPO')
    df_obs.index.name = ''
    df_obs.index = pd.to_datetime(df_obs.index)
    df_obs = df_obs.loc[df.index]
    nome_stazione = df_obs['NAME'].iloc[0]
    df_obs = df_obs['TMEAN']
    df_obs.name = 'Obs'
    
    colonne_membri = [c for c in df.columns if c != '2t_CTL']  # tutti tranne il controllo
    
    media = df[colonne_membri].mean(axis=1)
    
    fig, ax = plt.subplots(figsize=(10, 5))
    
    for i, membro in enumerate(colonne_membri):
        ax.plot(df.index, df[membro], color='grey', lw=0.4, alpha=0.5, label='membri ensemble' if i == 0 else None)
    
    ax.plot(df.index, media, color='tab:blue', lw=1.8, label='media ensemble')
    ax.plot(df.index, df['2t_CTL'], color='tab:red', lw=1.5, label='controllo (CTL)')
    ax.plot(df_obs.index, df_obs, color='black', lw=1.8, marker='o', markersize=3, label='Obs')
    
    ax.set_ylabel('2t (C)')
    ax.legend()
    ax.grid(alpha=0.3)
    ax.set_ylim(-5, 40)
    
    plt.title(f"{data.strftime('%A %d %B %Y')} - {nome_stazione}", loc='left')
    
    fig.tight_layout()
    plt.show()
    plt.close()

# %% Rank normalizzato (PIT discreto)

lista_date = pd.date_range('2020-01-01', '2020-12-31', freq='1d')

query_obs = f"""
SELECT
    TO_CHAR(data.dtrf, 'YYYY-MM-DD HH24:MI:SS') AS tempo,
    anag.code,
    anag.lon/1e5 AS lon,
    anag.lat/1e5 AS lat,
    anag.elev AS elev,
    anag.name AS name,
    tempm/10 AS TMEAN
FROM
    data
JOIN
    anag ON data.code = anag.code
WHERE
    tempm IS NOT NULL
    AND data.code = '{stazione}'
    AND data.dtrf BETWEEN TO_DATE('{lista_date[0]:%Y%m%d%H%M}', 'YYYYMMDDHH24MI')
                      AND TO_DATE('{(lista_date[-1] + pd.Timedelta(days=15)):%Y%m%d%H%M}', 'YYYYMMDDHH24MI')
ORDER BY
    data.dtrf
"""
df_obs = pd.read_sql(query_obs, con=connessione)
df_obs = df_obs.set_index('TEMPO')
df_obs.index.name = ''
df_obs.index = pd.to_datetime(df_obs.index)
nome_stazione = df_obs['NAME'].iloc[0]
df_obs = df_obs['TMEAN']
df_obs.name = 'Obs'

risultati = []
colonne_membri = None
casi_saltati_no_oss = 0

for data in lista_date:
    file_csv = f"{cartella_lavoro}/output/2t/{stazione}/{data.strftime('%Y-%m-%d')}.csv"
    df_run = pd.read_csv(file_csv, index_col=0, parse_dates=True).sort_index() - 273.15

    if colonne_membri is None:
        colonne_membri = df_run.columns.tolist()

    init_time = df_run.index[0]  # assumo FLT=0 sia la prima riga del run

    for valid_time, row in df_run.iterrows():
        flt = (valid_time - init_time).total_seconds() / 3600

        if valid_time not in df_obs.index or pd.isna(df_obs.loc[valid_time]):
            casi_saltati_no_oss += 1
            continue

        oss = df_obs.loc[valid_time]
        membri = row[colonne_membri].values.astype(float)
        membri = membri[~np.isnan(membri)]
        if len(membri) == 0:
            continue

        risultati.append({
            'init_time': init_time,
            'valid_time': valid_time,
            'flt': flt,
            'pit': f_calcola_rank(membri, oss),
        })

df_pit = pd.DataFrame(risultati)
print(f"Casi totali validi: {len(df_pit)} | casi saltati per oss mancante: {casi_saltati_no_oss}")

# --- 3. Plot del rank histogram (tutte le FLT insieme) ---
n_membri = len(colonne_membri)
plt.figure(figsize=(8, 5))
plt.hist(df_pit['pit'], bins=n_membri + 1, range=(0, 1), density=True, edgecolor='black', alpha=0.75)
plt.axhline(1.0, color='red', linestyle='--', label='Uniforme attesa (calibrato)')
plt.xlabel('Rank normalizzato (PIT discreto)')
plt.ylabel('Densità')
plt.ylim(0, 11)
plt.title(nome_stazione, loc='left')
plt.legend()
plt.tight_layout()
plt.show()
plt.close()



























print('\n\nDone')