# ID: codex_fusionapi_v1.2
"""Parametrisk arkitekturstub for GD66 Carver v1.2.

Skriptet etablerer tre-lags kontrakten (ParameterLayer/GeometryLayer/ManufacturingLayer)
og oppretter nødvendige brukerparametere uten å modellere geometri direkte.
"""
from dataclasses import dataclass
from typing import Dict, List

import adsk.core
import adsk.fusion

ID_TAG = "codex_fusionapi_v1.2"
_COMPLIANCE_BANNER = f"COMPLIANCE BANNER :: ID {ID_TAG} :: knife_gd66_carver"


@dataclass
class ParameterSpec:
    """Representerer en brukerparameter med uttrykk og kommentar."""

    name: str
    expression: str
    comment: str


PARAMETER_LAYER: List[ParameterSpec] = [
    ParameterSpec("blade_length", "42 mm", "GD66 Carver bladlengde"),
    ParameterSpec("blade_width_raw", "20 mm", "Rå emnebredde før sliping"),
    ParameterSpec("blade_width_final", "14 mm", "Ferdig bredde etter hollow-removal"),
    ParameterSpec("spine_thickness_raw", "4.7 mm", "Rå ryggtykkelse før sliping"),
    ParameterSpec("spine_thickness_final", "3.6 mm", "Ferdig ryggtykkelse"),
    ParameterSpec("bevel_angle_deg", "26 deg", "Primærslipets vinkel"),
    ParameterSpec("taper_ratio", "0.65", "Lineær avsmalning mot tupp"),
    ParameterSpec("tip_height", "2.2 mm", "Tupphøyde for konturkontroll"),
    ParameterSpec("ricasso_length", "6 mm", "Låre/ricasso-lengde"),
    ParameterSpec("heel_radius", "2.0 mm", "Radius ved heel"),
    ParameterSpec("handle_length", "102 mm", "Totallengde for håndtak"),
    ParameterSpec("handle_thickness", "12 mm", "Maksimal håndtakstykkelse"),
    ParameterSpec("scale_thickness", "3.0 mm", "Tykkelse per skaftskala"),
    ParameterSpec("wedge_angle_deg", "4 deg", "Kilevinkel bak"),
    ParameterSpec("front_pin_offset", "6 mm", "Avstand fra front til første pinne"),
    ParameterSpec("rear_pin_offset", "78 mm", "Avstand fra front til bakre pinne"),
    ParameterSpec("palm_swell", "2.4 mm", "Ekstra tykkelse for palm swell"),
    ParameterSpec("choil_clearance", "1.8 mm", "Frigang foran pinch-grip"),
]


GEOMETRY_CONTRACT: Dict[str, List[str]] = {
    "blade_profile_sketch": [
        "spine_raw",
        "spine_final",
        "hollow_arc",
        "material_removal_mask",
        "edge_line",
        "ricasso",
        "tip_guide",
    ],
    "handle_profile_sketch": [
        "pinch_grip_profile",
        "ergonomic_splines",
        "centerline",
        "front_stop",
        "rear_stop",
        "palm_swell_offset",
    ],
    "components": [
        "blade_comp",
        "handle_comp",
        "scale_left",
        "scale_right",
        "wedge_body",
    ],
}


MANUFACTURING_LAYER: Dict[str, List[str]] = {
    "named_faces": [
        "spine_ground",
        "bevel_primary",
        "belly_transition",
        "tip_zone",
        "ricasso_face",
    ],
    "process_notes": [
        "3D-printer volum 220x220x250 mm",
        "CNC-fres 400x300x120 mm",
        "Dreibenk Ø180 mm / 300 mm",
        "Sagblad Ø216 mm for trearbeid",
    ],
    "materials": [
        "Bjørk", "Syrin", "Svartor", "Rogn", "14C28N", "1095", "O1",
    ],
}


def _apply_user_parameters(design: adsk.fusion.Design) -> None:
    """Oppretter eller oppdaterer alle brukerparametere i ParameterLayer."""

    user_params = design.userParameters
    for spec in PARAMETER_LAYER:
        param = user_params.itemByName(spec.name)
        value = adsk.core.ValueInput.createByString(spec.expression)
        if param:
            param.expression = spec.expression
            param.comment = spec.comment
        else:
            user_params.add(spec.name, value, "", spec.comment)


def _compose_status_message() -> str:
    """Returnerer kort status over kontrakten som er brukt."""

    required_faces = ", ".join(MANUFACTURING_LAYER["named_faces"])
    blade_features = ", ".join(GEOMETRY_CONTRACT["blade_profile_sketch"])
    handle_features = ", ".join(GEOMETRY_CONTRACT["handle_profile_sketch"])
    return (
        f"GD66 Carver v1.2 parametre opprettet.\n"
        f"Blade sketch: {blade_features}.\n"
        f"Handle sketch: {handle_features}.\n"
        f"Navngitte flater: {required_faces}."
    )


def run(context: str) -> None:
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    print(_COMPLIANCE_BANNER)
    if not app:
        return

    design = adsk.fusion.Design.cast(app.activeProduct)
    if not design:
        if ui:
            ui.messageBox("Ingen aktiv Fusion 360-design funnet. Åpne et design før kjøring.")
        return

    _apply_user_parameters(design)

    if ui:
        ui.messageBox(_compose_status_message())


def stop(context: str) -> None:
    print(f"Stopper skript :: {_COMPLIANCE_BANNER}")
