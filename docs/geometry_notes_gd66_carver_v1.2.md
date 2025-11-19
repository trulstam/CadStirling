# GD66 Carver v1.2 – Geometrinotater (codex_fusionapi_v1.2)

Disse notatene oppsummerer geometri- og produksjonskontrakten for GD66-baserte
spikkekniven og er synkronisert med skriptet `scripts/knife_gd66_carver/main_knife_addin.py`.

## 1. Arkitektur
- **ParameterLayer**: oppretter alle dimensjoner som brukerparametere i Fusion 360.
- **GeometryLayer**: definerer hvilke skisser og kontroller som skal eksistere, uten at
  de modelleres automatisk i skriptet.
- **ManufacturingLayer**: navngitte flater, slipemasker og maskinbegrensninger som må
  følges i produksjon.

## 2. ParameterLayer
| Navn | Verdi | Kommentar |
| --- | --- | --- |
| blade_length | 42 mm | Bladlengde |
| blade_width_raw | 20 mm | Emnebredde før sliping |
| blade_width_final | 14 mm | Ferdig bredde etter hollow-removal |
| spine_thickness_raw | 4.7 mm | Rå ryggtykkelse |
| spine_thickness_final | 3.6 mm | Ferdig ryggtykkelse |
| bevel_angle_deg | 26 deg | Primærslip |
| taper_ratio | 0.65 | Lineær avsmalning |
| tip_height | 2.2 mm | Tupphøyde |
| ricasso_length | 6 mm | Ricasso-lengde |
| heel_radius | 2.0 mm | Heel-radius |
| handle_length | 102 mm | Håndtakslengde |
| handle_thickness | 12 mm | Maks tykkelse |
| scale_thickness | 3.0 mm | Tykkelse per skala |
| wedge_angle_deg | 4 deg | Kilevinkel bak |
| front_pin_offset | 6 mm | Avstand til fremre pin |
| rear_pin_offset | 78 mm | Avstand til bakre pin |
| palm_swell | 2.4 mm | Ekstra tykkelse |
| choil_clearance | 1.8 mm | Frigang foran pinch-grip |

## 3. GeometryLayer
- **Skisse `blade_profile_sketch`:** spine_raw, spine_final, hollow-arc,
  material_removal_mask, edge_line, ricasso og tip_guide for taper.
- **Avsmalning:** lineær taper via `taper_ratio` som påvirker både egg og rygg.
- **Bevel:** konstrueres fra plan vinkelrett på bladaksen og genereres som
  `extrude-cut` eller `loft-cut` i modellen.
- **Skisse `handle_profile_sketch`:** pinch-grip profil, ergonomisk 2-spline-system,
  rett senterlinje, front/rear stop og palm_swell_offset.
- **Komponenter:** blade_comp, handle_comp, scale_left, scale_right, wedge_body.

## 4. ManufacturingLayer
- **Navngitte flater:** spine_ground, bevel_primary, belly_transition,
  tip_zone, ricasso_face.
- **Prosessgrenser:** 3D-printer 220×220×250 mm; CNC 400×300×120 mm; dreibenk
  Ø180×300 mm; kappsag Ø216 mm.
- **Materialtilgjengelighet:** bjørk, syrin, svartor, rogn; stål 14C28N, 1095, O1.
- **Slipelogikk:** material_removal_mask skal tydeliggjøre hvor rå bredde reduseres
  til `blade_width_final` og hvor spine ground fjernes frem til `spine_thickness_final`.

## 5. Leveransefiler
- `GD66_Carver_v1.2.f3d`: eksportert Fusion 360-modell basert på parametrene over.
- `GD66_Carver_Drawing_v1.2.pdf`: teknisk tegning med navngitte flater og slipesoner.
- Dette dokumentet: sammenfatter arkitektur og parametre for revisjon v1.2.
