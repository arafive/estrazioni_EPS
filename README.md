# Verifica stadio2 Tmax/Tmin sui METAR
Script per misurare il "win" della previsione giornaliera stadio2 di Tmax e Tmin sulle stazioni METAR.
Il win è l'intero_1 uguale all'estremo osservato. L'estremo è il valore più alto o più basso dei METAR
e SPECI nella giornata locale della stazione (00-24 ora locale, con ora legale). La previsione_C arrotondata
non viene usata per il win; serve solo per MAE e bias.
## Struttura delle cartelle
Gli script stanno tutti nella stessa cartella, insieme a `stadio2_comune.py`, che contiene le funzioni
comuni e non va lanciato da solo. Le previsioni sono un livello sopra, in `../previsioni_operative/AAAA/MM/GG/`.
I METAR grezzi stanno in `wx/` dentro la cartella degli script, e da lì si leggono sia le temperature sia la pioggia.
## Aggiornare i dati
```
python3 scarica_wx_iem.py --out wx --aggiorna
```
Scarica dall'archivio IEM solo i giorni mancanti, ripartendo dall'ultimo giorno presente. Senza
`--aggiorna` scarica tutto dal 2020 per le stazioni che non ci sono ancora. Le nuove previsioni basta
copiarle in `previsioni_operative`.
## Statistiche
```
python3 win_generale.py   --wx wx --prev ../previsioni_operative   # win, int2, int3, top3, MAE, bias
python3 win_distacco.py   --wx wx --prev ../previsioni_operative   # win per distacco prob_1 - prob_2
python3 win_ampiezza.py   --wx wx --prev ../previsioni_operative   # win per ampiezza q95 - q05, incrociata col distacco
python3 win_condizione.py --wx wx --prev ../previsioni_operative   # win nelle giornate asciutte e nelle altre
python3 confronta_temp.py --oss ../osservati --wx wx               # confronto tra CSV osservati e METAR in wx
```
Opzioni comuni: `--vista globale` o `--vista stazioni` per stampare solo una parte, `--stazioni LIMC,EGLC`,
`--giorni 0,1`, `--dal AAAA-MM-GG` e `--al AAAA-MM-GG` sulla data della corsa. Con `--oss ../osservati`
le temperature si leggono dai CSV osservati invece che da `wx`. L'elenco completo si ottiene con `--help`.
Nelle tabelle per stazione i valori tra parentesi sono calcolati su meno di 10 casi. Con circa 80 giorni
per stazione e scadenza, differenze di 10-15 punti possono uscire anche per caso: conviene fidarsi solo
di quelle che si ripetono tra scadenze o stazioni.
`verifica_tmaxmin.py` è la verifica generale di tutte le versioni (raw, v4, stadio2, esaorarie) e per ora
legge solo i CSV osservati.
