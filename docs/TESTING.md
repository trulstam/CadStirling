# Manual testing and compatibility validation

Denne filen samler minimumsstegene som må kjøres i Fusion 360, sjekkpunkter for API-endringer og forslag til enhetstester basert på mock-objekter.

## Manuelle teststeg
1. **Synkroniser skript:** Kopier `scripts/examples/example_line_extrude.py` til den lokale Fusion-skriptmappen (`%APPDATA%/Autodesk/Autodesk Fusion 360/API/Scripts` på Windows eller `~/Library/Application Support/Autodesk/Autodesk Fusion 360/API/Scripts` på macOS).
2. **Start Fusion 360** og åpne *Scripts and Add-ins* → fanen **Scripts**.
3. **Kjør skriptet** `example_line_extrude`.
4. **Dialogverdi 1:** Angi linjelengde (f.eks. `5 cm`).
5. **Dialogverdi 2:** Angi ekstruderingshøyde (f.eks. `2 cm`).
6. **Forventet resultat:**
   - I Fusion-konsollen vises `COMPLIANCE BANNER :: ID codex_fusionapi_v1.1 :: example_line_extrude`.
   - En linje tegnes i XY-planet og ekstruderes til et solid med høyden angitt i dialogen.
   - Endringene kan ses og gjentas i *Timeline*. Justering av de to parameterne skal regenerere modellen.
7. **Feilhåndtering:** Avbryt dialogen for å bekrefte at skriptet viser `Kjøringsfeil: Brukeren avbrøt parameterdialogen.` i en melding eller i konsollen.

## Sjekkpunkter ved API-endringer
- **Les release notes:** Hver gang Autodesk publiserer en ny versjon av Fusion, les release notes for API: <https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC> og <https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-1AAE5E0C-833E-45C0-A018-49D9ACEE8DEB>. Noter breaking changes eller avvik i `adsk.core`, `adsk.fusion` og `adsk.cam`.
- **Bekreft objekt-API:** Sammenlign release notes med funksjonene brukt i repoet (`Application.get`, `Design.cast`, `Sketch.profiles`, `ExtrudeFeatures.createInput`, osv.).
- **Valider `_COMPLIANCE_BANNER`:** Kontroller at banneret fortsatt følger kravene og at skriptene logger strengen.

## Validering ved ny Fusion-versjon
1. **Miljøsjekk:** Oppgrader Fusion 360 og sørg for at skriptmappen fortsatt peker på repoet eller ny kopi.
2. **Automatisert makro:** (valgfritt) Bruk Fusion sin *Parameter Table* for å kjøre skriptet med minst tre kombinasjoner av linjelengde/ekstruderingshøyde (små, medium, store verdier) og bekreft at timeline regenererer uten feil.
3. **Logg resultater:** Dokumenter versjonen (build-nummer) i `docs/VALIDATION_LOG.md` (opprett ved behov) med dato, tester og resultat.
4. **Regresjon:** Gjenta manuelle teststeg over og sjekk at geometrien oppfører seg likt. Hvis release notes varslet API-endring, kjør ekstra tester for de påvirkede metodene.

## Enhetstesting via mocking av `adsk`
Selv om Fusion API vanligvis krever å kjøre inne i Fusion 360, kan man teste logisk kode ved å mocke nødvendige objekter:
- **Testkandidater:** `_ensure_design`, `_prompt_for_value` og `_create_line_and_extrude` fra `scripts/examples/example_line_extrude.py` fordi de opererer på kjente API-metoder og har deterministisk logikk.
- **Teknikk:** Lag mock-klasser som implementerer minimumet av attributter/metoder (f.eks. `app.documents.add`, `design.rootComponent`, `root.sketches.add`). Python-biblioteket `unittest.mock` kan brukes til å erstatte `adsk`-objekter.
- **Grense:** Geometrisk resultat (faktisk modell) kan ikke verifiseres uten Fusion, men funksjonskall og parametere kan verifiseres via mocks (f.eks. at `_create_line_and_extrude` kaller `extrudes.add` med riktig `ValueInput`).
- **Anbefalt struktur:** Opprett `codex/tests/test_example_line_extrude.py` (ny katalog) og injiser mockede `app`, `ui` og `design`-objekter. Sikre at alle tester importeres uten at Fusion er installert.
