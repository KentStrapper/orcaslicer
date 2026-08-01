# Kentstrapper OrcaSlicer — Regole per le release future

## Architettura del progetto

Questo repo contiene **solo le patch Kentstrapper** (non il sorgente upstream).
La CI clona `SoftFever/OrcaSlicer v2.4.2` al momento della build e applica le patch.

```
kentstrapper-patches/   ← questo repo
orcaslicer-source/      ← clonato dalla CI a build time
```

## Come funzionano le patch (ordine CI)

1. **PATCH 1** — copia i file `.cpp`/`.hpp` da `src/` sopra i corrispondenti upstream
2. **PATCH 1b** — `scripts/patch_extruder_count.py` (fix crash conteggio estrusori)
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

## Procedura per una nuova release

1. Aggiornare la versione upstream nel workflow se necessario
   (`.github/workflows/build_kentstrapper_windows.yml`, step "Clone OrcaSlicer")
2. Verificare che i file overlay in `src/` siano ancora compatibili con l'upstream
   (confrontare con `SoftFever/OrcaSlicer` tag corrispondente)
3. Push su `main` → la CI crea automaticamente una release GitHub
4. Testare visivamente: barra superiore e sidebar devono essere **arancioni**, non verdi

## Reference release funzionante

`kentstrapper-V2.3.2-Kentstrapper-b2646a8-20260427-0750` — usare come riferimento
visivo per confrontare colori e comportamento dei bottoni.
