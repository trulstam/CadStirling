ID: codex_fusionapi_v1.2
# Codex×Fusion360 — Generativ mekanikk & designskripting


**Status:** v1.2 • **ID-regel:** Alle prompter/kode må inneholde en ID-tag (f.eks. `codex_fusionapi_v1.2`).


## Formål
Utforske og utvikle generative, parametriske modeller i Autodesk Fusion 360 via Python/C++ API.
- Repoet er nå koblet til Codex på web.


## Klargjøring og kloning
1. Installer Git og klon repoet:
   ```bash
   git clone https://github.com/<din-org>/CadStirling.git
   cd CadStirling
   ```
2. Bekreft at `ID: codex_fusionapi_v1.2` står i første linje av all kommunikasjon (issues, commits, PRer) og i toppen av alle kodefiler.
3. Kjør `git status` før nye endringer og sørg for at commit-meldingens første linje starter med ID-en.

## Plassering av skriptkatalog
- **Windows:** `%APPDATA%/Autodesk/Autodesk Fusion 360/API/Scripts`
- **macOS:** `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts`

Kopier (eller symlink) `scripts/`-mappen hit slik at Fusion 360 finner skriptene automatisk. Hvert skript får egen undermappe i Fusion-dialogen.

## Hurtigstart
1) Installer Fusion 360. 2) Åpne *Scripts and Add-ins* → **Scripts** → **+** → velg `scripts/examples/example_line_extrude.py` (fra katalogen over). 3) Kjør. 4) Når dialogen dukker opp, skriv ønsket linjelengde og ekstruderingshøyde (f.eks. `5 cm` og `2 cm`).

- `scripts/examples/` inneholder fungerende eksempler – `example_line_extrude.py` er første verifiserte skript.
- `scripts/shared/` er stedet for felles biblioteksfunksjoner (parametre, helpers, logging osv.).
- `scripts/stirling_core/` og `scripts/knife_gd66_carver/` rommer henholdsvis Stirlingmotor- og knivdesign, med egne entry-skript (se under).

## Designstruktur for skript
- Hver designfamilie har en egen mappe under `scripts/` (f.eks. `scripts/stirling_core/`).
- Hver mappe har ett tydelig entry-point (`main_*_addin.py`) som Fusion 360 peker til fra Scripts/Add-ins.
- Delte moduler legges i `scripts/shared/` og importeres fra designmappene ved behov.
- Nye design skal følge samme mønster: `scripts/<designnavn>/` med `main_<design>_addin.py` som hovedfil, og eventuelle underkataloger som `parts/` eller `utils/`.

## Lokalt oppsett og testing
1. Fra repoet, kopier `scripts/examples/example_line_extrude.py` til Fusion-skriptmappen (over).
2. Start Fusion 360 → *Scripts and Add-ins* → fanen **Scripts**.
3. Velg `example_line_extrude` og klikk **Run**. Se etter "COMPLIANCE BANNER" i *Text Commands*-panelet for å bekrefte ID-logging.
4. Justér verdier i dialogen for å teste ulike lengder/høyder. Bruk Fusion sin *Timeline* for å verifisere at geometrien oppdateres.
5. Eventuelle kodeendringer testes ved å lagre fila i repoet og klikke **Run** på nytt (Fusion laster skriptet på nytt ved hver kjøring).


## Kildereferanser
- API Manual: https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC
- Basic Concepts: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BasicConcepts_UM.htm
- Dev Portal: https://aps.autodesk.com/developer/overview/autodesk-fusion-api
- GitHub Samples: https://github.com/AutodeskFusion360
- Forum: https://forums.autodesk.com/t5/fusion-360-api-and-scripts/bd-p/1229
- Add-ins Guide: https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-C1545D80-D804-4CF3-886D-9B5C54B2D7A2


## ID-krav (obligatorisk)
- **Prompt/Issue/PR:** må ha `ID: codex_fusionapi_vX.Y` i første linje.
- **Kodefiler:** må ha `# ID: codex_fusionapi_vX.Y` i topp-kommentar.
- **Console-logg:** skriv et "COMPLIANCE BANNER" med ID ved kjøring.
- **Commits:** første linje i hver commit-melding må starte med ID-en for å dokumentere sporbarhet (f.eks. `ID: codex_fusionapi_v1.1 – oppdater README`).
- **Kjøring:** `_COMPLIANCE_BANNER`-strengen i skriptene logges automatisk i Fusion-konsollen.

## Kjente feilkilder
- **Fusion-modulene importeres ikke:** `adsk.core` og `adsk.fusion` er kun tilgjengelige inne i Fusion 360. Kjør skriptet via *Scripts and Add-ins* i stedet for lokalt Python-miljø.
- **Skript vises ikke i Fusion:** Bekreft at filen ligger i `%APPDATA%/Autodesk/Autodesk Fusion 360/API/Scripts` (eller tilsvarende på macOS) og at Fusion er restartet etter kopiering.
- **Ingen profil funnet ved ekstrudering:** Sørg for at linjen danner en lukket profil (skriptet lager linje med bredde). Hvis du har endret skriptet, sjekk at `sketch.profiles` ikke er tom og at enhetene er gyldige.


## Lisens
MIT (etter behov).
