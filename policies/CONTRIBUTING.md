ID: codex_fusionapi_v1.1
# Contributing (Policy v1.1)


- **ID på alt:** Issues, PR-er, commit-meldinger og kode må inneholde `ID: codex_fusionapi_vX.Y`.
- **Fusion API:** Bruk alltid nyeste `adsk.core`, `adsk.fusion` (ev. `adsk.cam`). Sjekk mot offisielle kilder.
- **Avvis:** Utdaterte kall/navnerom, manglende ID, uklare enheter.
- **Console banner:** print ID ved kjøring.

## Mappestruktur for skript
- Legg nye design under `scripts/<designnavn>/` og sørg for ett tydelig entry-skript (`main_<design>_addin.py`).
- Designmapper kan utvides med underkatalogene `parts/`, `utils/` osv. etter behov, men entry-filen skal alltid være på rotnivået i designmappen.
- Delte helpers ligger i `scripts/shared/`.
- `scripts/examples/` rommer referanseeksempler som ikke skal brytes når nye design introduseres.