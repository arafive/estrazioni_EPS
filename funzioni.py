
import os

import numpy as np

def f_lista_percorsi_membri_EPS(CARTELLA_ARC_STORICO, CARTELLA_ARC_BACKUP, data):

    sub_cartella_modello = f"{CARTELLA_ARC_STORICO}/ECMWF/{data.strftime('%Y/%m/%d')}"
    if not os.path.exists(sub_cartella_modello):
        sub_cartella_modello = f"{CARTELLA_ARC_BACKUP}/ECMWF/{data.strftime('%Y/%m/%d')}"
    
    membri = [x for x in os.listdir(sub_cartella_modello) if x.startswith('ecmf_') and x.endswith('.grb') and ('pf' in x or 'cf' in x) and '00_' in x]
    membri = sorted(membri, key=lambda s: int(s.rsplit('_', 1)[1].split('.')[0]))

    lista_percorsi = []
    for m in membri:
        lista_percorsi.append(f'{sub_cartella_modello}/{m}')

    return lista_percorsi


def f_calcola_rank(membri, oss):
    """Rank normalizzato dell'osservazione tra i membri, con tie-breaking
    casuale (Hamill 2001) per gestire osservazioni uguali a uno o piu' membri."""
    membri_ord = np.sort(membri)
    n = len(membri_ord)
    rank_inf = np.searchsorted(membri_ord, oss, side='left')
    rank_sup = np.searchsorted(membri_ord, oss, side='right')
    rank = np.random.randint(rank_inf, rank_sup + 1) if rank_sup > rank_inf else rank_inf
    return rank / n


def f_calcola_crps(membri, oss):
    """CRPS empirico (stimatore NRG) per un singolo caso ensemble."""
    n = len(membri)
    termine1 = np.mean(np.abs(membri - oss))
    diff = np.abs(membri[:, None] - membri[None, :])
    termine2 = diff.sum() / (2 * n * n)
    return termine1 - termine2