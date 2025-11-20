ID: codex_fusionapi_v1.9

# Arkitektur – Parametrisk Stirlingmotor (stirling_core)

Dette dokumentet beskriver den overordnede arkitekturen for
`stirling_core`-add-in’en i CadStirling-prosjektet.

Målet er at både mennesker og modeller (Codex) skal kunne
forstå:

- koordinatsystem og referanseplaner
- hvilke komponenter som finnes og hvem som bygger hva
- hvordan genereringspipen er strukturert
- hvordan layout (plassering i assembly) fungerer
- hvor maskin- og materialbegrensninger kommer inn.

## 1. Overordnet mappestruktur

Relevante mapper i repoet:

- `scripts/stirling_core/main_stirling_addin.py`  
  – hoved-ADD-IN, entrypoint for Fusion 360.
- `docs/`  
  – teknisk dokumentasjon, BOM, arbeidsplaner, endringslogg.
- `cad/`  
  – eksporterte STEP/STL/OBJ-filer.
- `sim/`  
  – kinematikkplaner, eksporterte simulasjoner.
- `config/`  
  – (planlagt) maskinkonfigurasjon og materialkartotek.

Dette dokumentet beskriver bare Stirling-arkitekturen.
Andre fremtidige scripts skal følge samme prinsipper.

## 2. Koordinatsystem og referanseplaner

Globalt koordinatsystem (rootComponent i Fusion):

- Origo (0,0,0): senter av bunnplaten projisert i XY.
- XY-plan: oversiden av bunnplaten.
- Z-akse: peker opp fra bunnplaten.
- X-akse: langs lengderetning på bunnplaten.
- Y-akse: langs bredden på bunnplaten, “forover” mot veiv/svinghjul.

Alle komponenter tegnes lokalt rundt (0,0,0) i sitt eget
komponent-coordinate-system. Plassering i assembly skjer
KUN via transformasjoner i `create_component_records`.

## 3. Komponentroller

Hver hoveddel er en egen komponent:

- Ramme og bunnplate
- Arbeidssylinder (kvartsglass)
- Fortrengersylinder (kvartsglass)
- Arbeidsstempel
- Fortrenger
- Veivaksel
- Svinghjul
- Koblingsstenger
- Varme- og kjølemodul

En felles designregel:

> `build_*`-funksjonene tegner geometri i lokal origo.  
> De vet ingenting om assembly-layout eller joints.  
>
> `create_component_records` og senere joints/kinematikk
> tar ansvar for plassering og bevegelse.

## 4. Genereringspipeline (run)

Hovedpipen i `run()` skal i grove trekk følge denne flyten:

1. `register_user_parameters`  
   – sikrer alle brukerparametre (ID_WORK, STROKE, BASE_LENGTH, osv.)

2. `compute_geometry_inputs`  
   – beregner avledede størrelser (pistondiameter, klaring, osv.)

3. `compute_performance_metrics`  
   – slagvolum, dødvolum, estimert kompresjonsforhold.

4. `create_component_records`  
   – oppretter forekomster (occurrences) og plasserer komponenter
     i assembly (scatter-layout, se seksjon 5).

5. `build_geometry`  
   – kaller `build_frame`, `build_quartz_cylinder`, `build_piston`,
     `build_crankshaft`, osv. for å skape kroppene (bodies).

6. `apply_materials_and_appearances`  
   – legger på materialer og utseende.

7. `build_joints`  
   – (midlertidig deaktivert for kinematikk; se seksjon 6).

8. Dokumentasjon og eksport:  
   – `generate_drawings`, `evaluate_clearances`, `export_all`,
     `compile_bom_entries`, `write_bom`, `write_arbeidsplan`,
     `update_changelog`, `write_simulation_stub`, `apply_metadata`.

Maskin-/materialbegrensninger (seksjon 7) legges inn som en
egen, senere fase i denne pipen.

## 5. Layout – “Raw Part Scatter”

Før vi begynner med automatisk sammenstilling og joints,
benyttes et “scatter”-oppsett i assembly:

- Hver komponent plasseres separat i rommet slik at alle
  deler er lette å inspisere, måle og flytte manuelt.

Standard scatter-layout (alle verdier i millimeter):

- **Bunnplate (Ramme og bunnplate)**  
  - Origo: `(0, 0, 0)` (grounded).  
  - XY-plan: topplan på platen.

- **Arbeidssylinder**  
  - Senter: `(-DISPLACER_OFFSET/2, 0, BASE_THICK)`  
  - Aksen orienteres langs global Z (vertikal sylinder).

- **Fortrengersylinder**  
  - Senter: `( +DISPLACER_OFFSET/2, 0, BASE_THICK)`  
  - Inntil videre orienteres også denne langs global Z
    (to vertikale glass-sylindre, 90° i plan kommer senere).

- **Arbeidsstempel**  
  - Senter: `(-DISPLACER_OFFSET/2, 0, BASE_THICK + LEN_WORK/2)`

- **Fortrenger**  
  - Senter: `( +DISPLACER_OFFSET/2, 0, BASE_THICK + LEN_DISP/2)`

- **Veivaksel**  
  - Senter langs X: `0`  
  - Y-posisjon: `BASE_WIDTH/2 – 25`  
  - Z-posisjon: `BASE_THICK + max(LEN_WORK, LEN_DISP)/2`.

- **Svinghjul**  
  - Samme Z som veivaksel  
  - Y-posisjon: `(BASE_WIDTH/2 – 25) + 10`.

- **Koblingsstenger**  
  - F.eks. `(0, –BASE_WIDTH/2 + 25, BASE_THICK + LEN_WORK/2)`.

- **Varme/kjølemodul**  
  - F.eks. `(0, 0, –20)` for å ligge visuelt avskilt.

Poenget med scatter-layout er:

- Delene overlapper ikke.
- Alt er manuelt inspektérbart i Fusion.
- Geometrien kan verifiseres visuelt før vi låser kinematikken.

## 6. Joints og kinematikk (midlertidig deaktivert)

På dette stadiet er real-time kinematikk med joints i Fusion
utsatt for å unngå ustabile skript.

- `build_joints` har en minimal implementasjon som KUN
  skriver metadata:
  - `phase_deg = 90` (for senere MotionLink mellom veiv og fortrenger).
- Ingen `AsBuiltJoints` eller `Joints` opprettes automatisk.
- All bevegelsesanimasjon gjøres manuelt i Fusion inntil
  geometri og layout er verifisert.

Når geometrien er moden nok:

- Tegne faktiske veivtapper og koblingsstang-fester.
- Lage dedikerte `JointGeometry`-referanser
  (circular edge / planar face) for revolute/slider-ledd.
- Innføre MotionLink for 90° faseforskyvning.

## 7. Maskin- og materialbegrensninger (production layer)

Prosjektet skal på sikt støtte en “production layer” som
analyserer om delene kan produseres med tilgjengelig utstyr.

Planlagte filer:

- `config/machines.yaml`  
  – beskriver:
  - 3D-printere (build volume, min veggtykkelse, toleranser)
  - CNC-fres (X/Y/Z travel, max verktøydiameter)
  - Dreiebenker (swing, avstand mellom sentre, spindelboring)
  - Sager (blad-diameter, maks kutt-høyde/bredde).

- `config/materials.csv`  
  – beskriver materialer:
  - kode, navn, type (plate/stang/filament), pris, leverandør
  - lagerstatus eller tilgjengelighet.

Fremtidige hjelpefunksjoner:

- `load_machine_config()`
- `load_material_db()`
- `check_all_parts_manufacturability(design, records, machine_cfg)`
- `enrich_bom_with_material_data(bom_entries, material_db)`

Disse funksjonene vil:

- sjekke bounding box for hver komponent mot maskinbegrensninger
- flagge deler som for store for lokale maskiner
- estimere kostnad ut fra materialkartoteket.

Inntil videre skal production layer kun være dokumentert og
eventuelle kode-stubber må ligge bak try/except slik at fravær
av config-filer ikke krasjer add-in.
