"""
Creazione: Tue Jul 28 18:01:07 2026
Autore: daniele
"""

import warnings
warnings.simplefilter('ignore', FutureWarning)
warnings.simplefilter('ignore', UserWarning)
warnings.filterwarnings('ignore', message='IProgress not found.*')

import os
import re
import sys
import ast
import configparser

import xarray as xr
xr.set_options(use_new_combine_kwarg_defaults=True)

import numpy as np
import pandas as pd

from concurrent.futures import ProcessPoolExecutor, as_completed
# TODO fallo in parallelo

sys.path.insert(0, os.path.expanduser('~/.config'))
from config_percorsi_Daniele import CARTELLA_REPO_ROOT
from config_percorsi_Daniele import CARTELLA_ARC_STORICO
# from config_percorsi_Daniele import CARTELLA_ARC_BACKUP
# from config_percorsi_Daniele import CARTELLA_STORAGE

cartella_lavoro = os.path.join(CARTELLA_REPO_ROOT, 'estrazioni_EPS')
cartella_ARC_STORICO = os.path.join(CARTELLA_ARC_STORICO)
os.chdir(cartella_lavoro)

from funzioni import f_lista_percorsi_membri_EPS

from danilib import f_open_grib_attrs

config = configparser.ConfigParser()
config.read('./config.ini')

df_coordinate = pd.read_csv('coordinate/df_coordinate.csv', index_col=0)
lista_campi = ast.literal_eval(config.get('COMMON', 'lista_campi'))
cartella_output = f"{CARTELLA_REPO_ROOT}/{config.get('COMMON', 'cartella_output')}"

print(cartella_output)

if len(sys.argv) > 1:
    data_arg = ' '.join(sys.argv[1:])
    lista_date = [pd.Timestamp(data_arg)]
    print(lista_date)
else:
    # lista_date = [pd.Timestamp('2024-01-01')]
    lista_date = pd.date_range('2025-01-01', '2026-07-28', freq='1d')
    
# %%

for data in lista_date:
    print(f"* {str(data)}")
    
    percorsi_output_attesi = [
        f"{cartella_output}/{campo}/{stazione}/{data.strftime('%Y-%m-%d')}.csv"
        for campo in lista_campi
        for stazione in df_coordinate.index
    ]
    percorsi_mancanti = [p for p in percorsi_output_attesi if not os.path.exists(p)]
    if not percorsi_mancanti:
        print('*** Tutti i file di output già presenti per questa data, continuo ***')
        continue
    else:
        campi_mancanti = sorted({p.split('/')[-3] for p in percorsi_mancanti})
        print(f"*** Mancano {len(percorsi_mancanti)}/{len(percorsi_output_attesi)} file. "
              f"Campi coinvolti: {campi_mancanti}. Esempio: {percorsi_mancanti[0]}")
    
    lista_percorsi = f_lista_percorsi_membri_EPS(CARTELLA_ARC_STORICO, CARTELLA_ARC_STORICO, data)
    
    dict_df = {}  # chiave (campo, stazione) -> lista di df, uno per membro
    
    for percorso_membro in lista_percorsi:
        try:
            lista_ds, df_attrs = f_open_grib_attrs(percorso_membro)
        except PermissionError:
            print('*** Permission Error ***')
            continue
        except FileNotFoundError:
            print('*** File Not Found Error ***')
            continue
  
        nome_file = os.path.basename(percorso_membro)
        if '_cf_' in nome_file:
            membro = 'CTL'
        else:
            membro = f"{int(re.search(r'_pf_(\d+)', nome_file).group(1)):02d}"

        print(f'  * membro {membro}')
        
        df_attrs = df_attrs[df_attrs['GRIB_dataType'] == 'fc']
        # Potrebbero non esserci tutti i campi. Estraggo solo quelli che davvero ci sono
        df_attrs = df_attrs.loc[df_attrs.index.intersection(lista_campi)]
        for campo in df_attrs.index:
            if len(lista_ds) == 1:
                # Può capitare che il grib abbia di fatto un solo dataset
                da_campo = lista_ds[0][campo].load()
            else:
                da_campo = lista_ds[df_attrs.loc[campo]['id_ds']][campo].load()
            valid_time = pd.to_datetime(da_campo['valid_time'])
            
            for stazione in df_coordinate.index:
                lat = df_coordinate.loc[stazione, 'Latitude']
                lon = df_coordinate.loc[stazione, 'Longitude']
                estrazione = da_campo.sel(latitude=lat, longitude=lon, method='nearest')
                df = pd.DataFrame(estrazione.values, index=valid_time)
                
                if estrazione.ndim == 2:
                    df.columns = [f'{campo}_{x}_{membro}' for x in estrazione[estrazione.dims[1]].values.astype(int)]
                else:
                    df.columns = [f'{campo}_{membro}']
                    
                ### !!! Rifai l'estrazione solo per tp, oppure calcola la cumulata dopo...
                # if campo == 'tp':
                #     assert df.index[0] == data, "L'istante iniziale non coincide con l'analisi"
                #     df = df.reindex(pd.date_range(start=data, end=df.index.max(), freq='6h'))
                #     df = df * 1000 # m -> mm
                #     df = df.diff()
                #     df.iloc[0] = 0
                #     df = df.clip(lower=0)
                
                dict_df.setdefault((campo, stazione), []).append(df)
    
    # un solo salvataggio per campo/stazione, con tutti i membri come colonne
    for (campo, stazione), lista_df_membri in dict_df.items():
        df_finale = pd.concat(lista_df_membri, axis=1)
        os.makedirs(f"{cartella_output}/{campo}/{stazione}", exist_ok=True)
        df_finale.to_csv(f"{cartella_output}/{campo}/{stazione}/{data.strftime('%Y-%m-%d')}.csv", index=True, header=True, mode='w', na_rep=np.nan)

print('\n\nDone.')

