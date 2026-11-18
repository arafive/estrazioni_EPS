"""
Cancella da output/<campo>/ le cartelle delle stazioni che non sono in
calibrazione_EPS/coordinate/df_stazioni_meteo.csv.

Uso:
    python3 pulizia_output.py            -> mostra solo cosa verrebbe cancellato
    python3 pulizia_output.py --esegui   -> cancella davvero
"""

import os
import sys
import shutil

import pandas as pd

sys.path.insert(0, os.path.expanduser('~/.config'))
from config_percorsi_Daniele import CARTELLA_REPO_ROOT

cartella_output = os.path.join(CARTELLA_REPO_ROOT, 'estrazioni_EPS', 'output')
file_stazioni = os.path.join(CARTELLA_REPO_ROOT, 'calibrazione_EPS', 'coordinate', 'df_stazioni_meteo.csv')

esegui = '--esegui' in sys.argv

stazioni_da_tenere = set(pd.read_csv(file_stazioni, index_col=0).index)
print(f'Stazioni da tenere ({len(stazioni_da_tenere)}): {sorted(stazioni_da_tenere)}')

da_cancellare = []
for campo in sorted(os.listdir(cartella_output)):
    cartella_campo = os.path.join(cartella_output, campo)
    if not os.path.isdir(cartella_campo):
        continue
    # set: sul disco NTFS le voci delle cartelle possono comparire due volte
    for stazione in sorted(set(os.listdir(cartella_campo))):
        percorso = os.path.join(cartella_campo, stazione)
        if os.path.isdir(percorso) and stazione not in stazioni_da_tenere:
            da_cancellare.append(percorso)

stazioni_cancellate = sorted({os.path.basename(p) for p in da_cancellare})
print(f'\nCartelle da cancellare: {len(da_cancellare)} ({len(stazioni_cancellate)} stazioni)')
print(stazioni_cancellate)

if not esegui:
    print('\nProva a vuoto: niente cancellato. Per cancellare: python3 pulizia_output.py --esegui')
    sys.exit(0)

def f_ignora_mancanti(funzione, percorso, eccezione):
    # Su NTFS (fuseblk) alcune cartelle elencano lo stesso file due volte:
    # al secondo tentativo il file e' gia' cancellato -> FileNotFoundError, da ignorare
    if isinstance(eccezione, FileNotFoundError):
        return
    raise eccezione


def f_cancella_cartella(percorso, tentativi=5):
    for _ in range(tentativi):
        try:
            shutil.rmtree(percorso, onexc=f_ignora_mancanti)
        except OSError:
            pass  # es. cartella "non vuota" per una voce doppia: si riprova
        if not os.path.exists(percorso):
            return True
    return False


non_cancellate = []
for percorso in da_cancellare:
    if not os.path.exists(percorso):
        continue  # gia' cancellata (voce doppia o lancio precedente)
    if f_cancella_cartella(percorso):
        print(f'  cancellata {percorso}')
    else:
        non_cancellate.append(percorso)
        print(f'  *** NON cancellata {percorso}')

print(f'\nNon cancellate: {len(non_cancellate)}')
print('\nDone.')
