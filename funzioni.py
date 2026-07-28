
import os

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