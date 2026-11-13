# Kentstrapper OrcaSlicer — Regole per le release future

## Architettura del progetto

Questo repo contiene **solo le patch Kentstrapper** (non il sorgente upstream).
La CI clona `SoftFever/OrcaSlicer v2.5.0` al momento della build e applica le patch.
Dalla v2.5.0 la build si fa con `build_win.bat -d` (dipendenze) e `build_win.bat -s -i`
(slicer + install in `build/OrcaSlicer`): il vecchio `build_release_vs.bat` non esiste più.

```
kentstrapper-patches/   ← questo repo
orcaslicer-source/      ← clonato dalla CI a build time
```

## Come funzionano le patch (ordine CI)

1. **PATCH 1** — copia i file `.cpp`/`.hpp` da `src/` sopra i corrispondenti upstream
2. **PATCH 1b** — `scripts/patch_extruder_count.py` (fix crash conteggio estrusori; dalla
   v2.5.0 il fix è già upstream e lo script non fa nulla)
3. **PATCH 2** — `scripts/patch_colors.py` (sostituzione globale teal → arancione)
4. **PATCH 2b** — `scripts/patch_splash.py` (splash screen)
5. **PATCH 3** — verifica che non rimanga nessun teal nei file chiave + scan globale
6. **PATCH 4/5** — icone e splash screen da `branding/`
7. **PATCH 8** — binary-patch dell'EXE per colori teal residui nei dati embedded

## Colori corporate Kentstrapper

| Uso | Colore | Hex | RGB |
|-----|--------|-----|-----|
| Accent principale (selezionato) | Arancione | `#FF8800` | `255, 136, 0` |
| Accent hover | Arancione scuro | `#CC6E00` | `204, 110, 0` |
| Sfondo tab selezionata (sidebar) | Pesca chiaro | `#FFE0B2` | `255, 224, 178` |
| Top bar background | Grigio scuro | `#2D2D30` / `#3B4446` | — |

**Non usare mai** `#009688` (teal), `#26A69A`, `#52C7B8` o qualsiasi variante verde/teal.

## File di patch C++ inclusi in questo repo

| File | Controlla | Widget |
|------|-----------|--------|
| `src/slic3r/GUI/Notebook.cpp` | Barra superiore (Prepare/Preview/Device/Project) | `ButtonsListCtrl` |
| `src/slic3r/GUI/Tabbook.cpp` | Sidebar sinistra (tab parametri verticali) | `TabButtonsListCtrl` |
| `src/slic3r/GUI/TabButton.cpp` | Bottone singolo sidebar | `TabButton` |
| `src/slic3r/GUI/Widgets/Button.cpp` | Bottone generico (usato da Notebook) | `Button` |
| `src/slic3r/GUI/Widgets/StateColor.cpp` | Mappa colori light/dark mode | `gDarkColors` |
| `src/slic3r/GUI/Widgets/StaticBox.cpp` | Box con bordi arrotondati | `StaticBox` |

## Lezione imparata: il bug teal nella top bar

Il file upstream `Notebook.cpp` usava `wxColour(0,150, 136)` con **spaziatura mista**
(no spazio dopo la prima virgola). `patch_colors.py` copriva `"0, 150, 136"` e
`"0,150,136"` ma NON `"0,150, 136"`, lasciando il tab selezionato teal quando il
mouse non era sopra.

**Soluzione**: `Notebook.cpp` è ora un file overlay in questo repo (PATCH 1 lo copia
sull'upstream). Non affidarsi solo a `patch_colors.py` per i file critici dell'UI.

## Lezione imparata: overlay vecchi annullano fix upstream

Gli overlay sostituiscono il file upstream **intero**. Nella 2.4.2 `Button.cpp` e
`StateColor.cpp` erano basati su una versione più vecchia e annullavano per errore codice
upstream (pulsanti `ButtonType::Icon`, fix tooltip Wayland, colore toggle in dark mode).
Un overlay deve differire dall'upstream della sua versione **solo** per le modifiche
Kentstrapper (colori + i fix di `StaticBox.cpp`).

## Procedura per una nuova versione upstream (es. 2.5.0 → 2.6.0)

1. Clonare upstream vecchia (`VECCHIA`) e nuova (`NUOVA`) versione
2. Per ogni file in `src/`: confrontare `VECCHIA` vs `NUOVA`. Se cambiato (anche il `.hpp`),
   non copiare l'overlay così com'è: fare un merge a 3 vie
   `git merge-file overlay VECCHIA/file NUOVA/file` e risolvere i conflitti tenendo il
   codice nuovo con i nostri colori
3. `diff NUOVA/file overlay` deve mostrare **solo** modifiche Kentstrapper
4. Simulare PATCH 1 → 1b → 2 → 2b → 3 sui sorgenti nuovi: zero teal residuo, script OK
5. Cercare colori verdi/teal nuovi introdotti dalla versione nuova e aggiungerli a
   `patch_colors.py`
6. Controllare che gli script di build e i file usati da PATCH 4–7 esistano ancora
7. Aggiornare tag nel workflow (step "Clone OrcaSlicer") e il testo della release
8. Prima build di prova: lanciare il workflow a mano sul branch di sviluppo con
   `create-release` = false (nessuna release). Poi push su `main` → release automatica
9. Testare visivamente: barra superiore e sidebar devono essere **arancioni**, non verdi

## Problema noto (da sistemare)

PATCH 6 e 7 cercano un file `.nsi` che upstream non ha (né in 2.4.2 né in 2.5.0): il
nome dell'installer e la copia dei profili in `%APPDATA%\OrcaSlicer\user\default` non
vengono applicati. I profili finiscono solo in `resources/kentstrapper_profiles`.

## Reference release funzionante

`kentstrapper-V2.3.2-Kentstrapper-b2646a8-20260427-0750` — usare come riferimento
visivo per confrontare colori e comportamento dei bottoni.
