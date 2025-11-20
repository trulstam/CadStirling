# ID: codex_fusionapi_v1.2
"""Parametrisk arkitekturstub for GD66 Carver v1.2.

Skriptet etablerer tre-lags kontrakten (ParameterLayer/GeometryLayer/ManufacturingLayer)
og oppretter nødvendige brukerparametere uten å modellere geometri direkte.
"""
import math
from dataclasses import dataclass
from typing import Dict, List, Sequence

import adsk.core
import adsk.fusion

from scripts.shared.config_loader import load_machine_park, load_material_catalog

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
    components = ", ".join(GEOMETRY_CONTRACT["components"])
    return (
        f"GD66 Carver v1.2 parametre opprettet.\n"
        f"Blade sketch: {blade_features}.\n"
        f"Handle sketch: {handle_features}.\n"
        f"Komponenter: {components}.\n"
        f"Navngitte flater: {required_faces}."
    )


def _get_param_value(design: adsk.fusion.Design, name: str) -> float:
    user_param = design.userParameters.itemByName(name)
    if not user_param:
        raise ValueError(f"Mangler brukerparameter: {name}")
    return float(user_param.value)


def _ensure_component(
    root: adsk.fusion.Component, name: str
) -> adsk.fusion.Component:
    occurrences = root.occurrences
    for occ in occurrences:
        if occ.component.name == name:
            return occ.component

    transform = adsk.core.Matrix3D.create()
    occ = occurrences.addNewComponent(transform)
    occ.component.name = name
    return occ.component


def _ensure_sketch(
    sketches: adsk.fusion.Sketches, plane: adsk.core.Base, name: str
) -> adsk.fusion.Sketch:
    for sketch in sketches:
        if sketch.name == name:
            return sketch

    sketch = sketches.add(plane)
    sketch.name = name
    return sketch


def _draw_blade_profile(design: adsk.fusion.Design, sketch: adsk.fusion.Sketch) -> None:
    blade_length = _get_param_value(design, "blade_length")
    blade_width_raw = _get_param_value(design, "blade_width_raw")
    blade_width_final = _get_param_value(design, "blade_width_final")
    taper_ratio = _get_param_value(design, "taper_ratio")
    tip_height = _get_param_value(design, "tip_height")
    ricasso_length = _get_param_value(design, "ricasso_length")
    bevel_angle = _get_param_value(design, "bevel_angle_deg")

    lines = sketch.sketchCurves.sketchLines
    splines = sketch.sketchCurves.sketchFittedSplines

    spine_raw_end_y = blade_width_raw * taper_ratio
    spine_raw = lines.addByTwoPoints(
        adsk.core.Point3D.create(0, blade_width_raw, 0),
        adsk.core.Point3D.create(blade_length, spine_raw_end_y, 0),
    )
    spine_raw.isConstruction = True

    spine_final_end_y = max(tip_height, blade_width_final * taper_ratio)
    spine_final = lines.addByTwoPoints(
        adsk.core.Point3D.create(ricasso_length, blade_width_final, 0),
        adsk.core.Point3D.create(blade_length, spine_final_end_y, 0),
    )
    spine_final.isConstruction = True

    edge_line = lines.addByTwoPoints(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(blade_length, tip_height, 0),
    )

    ricasso = lines.addCenterPointRectangle(
        adsk.core.Point3D.create(ricasso_length / 2, blade_width_raw / 2, 0),
        adsk.core.Point3D.create(ricasso_length, blade_width_raw, 0),
    )
    for seg in ricasso:
        seg.isConstruction = True

    hollow_mid_x = blade_length * 0.55
    hollow_start = adsk.core.Point3D.create(ricasso_length * 1.05, blade_width_final * 0.6, 0)
    hollow_mid = adsk.core.Point3D.create(hollow_mid_x, blade_width_final * 0.45, 0)
    hollow_end = adsk.core.Point3D.create(blade_length * 0.9, spine_final_end_y * 0.6, 0)
    hollow_arc = splines.add(
        adsk.core.ObjectCollection.create()
    )
    for pt in (hollow_start, hollow_mid, hollow_end):
        hollow_arc.fitPoints.add(pt)

    material_mask = lines.addTwoPointRectangle(
        adsk.core.Point3D.create(0, blade_width_final, 0),
        adsk.core.Point3D.create(blade_length, blade_width_raw, 0),
    )
    for seg in material_mask:
        seg.isConstruction = True

    tip_guide = lines.addByTwoPoints(
        adsk.core.Point3D.create(blade_length * 0.95, tip_height, 0),
        adsk.core.Point3D.create(blade_length, spine_final_end_y, 0),
    )
    tip_guide.isConstruction = True

    bevel_height = math.tan(math.radians(bevel_angle)) * _get_param_value(
        design, "spine_thickness_final"
    )
    bevel_anchor = adsk.core.Point3D.create(blade_length * 0.25, bevel_height, 0)
    bevel_line = lines.addByTwoPoints(bevel_anchor, adsk.core.Point3D.create(blade_length * 0.5, 0, 0))
    bevel_line.isConstruction = True


def _draw_handle_profile(design: adsk.fusion.Design, sketch: adsk.fusion.Sketch) -> None:
    handle_length = _get_param_value(design, "handle_length")
    handle_thickness = _get_param_value(design, "handle_thickness")
    palm_swell = _get_param_value(design, "palm_swell")
    choil_clearance = _get_param_value(design, "choil_clearance")

    lines = sketch.sketchCurves.sketchLines
    splines = sketch.sketchCurves.sketchFittedSplines

    centerline = lines.addByTwoPoints(
        adsk.core.Point3D.create(0, 0, 0), adsk.core.Point3D.create(handle_length, 0, 0)
    )
    centerline.isConstruction = True

    front_stop = lines.addByTwoPoints(
        adsk.core.Point3D.create(0, -handle_thickness / 2, 0),
        adsk.core.Point3D.create(0, handle_thickness / 2, 0),
    )
    rear_stop = lines.addByTwoPoints(
        adsk.core.Point3D.create(handle_length, -handle_thickness / 2, 0),
        adsk.core.Point3D.create(handle_length, handle_thickness / 2, 0),
    )
    for seg in (front_stop, rear_stop):
        seg.isConstruction = True

    ergonomic_points = adsk.core.ObjectCollection.create()
    ergonomic_points.add(adsk.core.Point3D.create(handle_length * 0.05, choil_clearance, 0))
    ergonomic_points.add(adsk.core.Point3D.create(handle_length * 0.3, handle_thickness * 0.45 + palm_swell, 0))
    ergonomic_points.add(adsk.core.Point3D.create(handle_length * 0.65, handle_thickness * 0.35 + palm_swell * 0.6, 0))
    ergonomic_points.add(adsk.core.Point3D.create(handle_length * 0.95, handle_thickness * 0.25, 0))
    spline = splines.add(ergonomic_points)

    pinch_points = adsk.core.ObjectCollection.create()
    pinch_points.add(adsk.core.Point3D.create(handle_length * 0.08, -handle_thickness * 0.2, 0))
    pinch_points.add(adsk.core.Point3D.create(handle_length * 0.25, -handle_thickness * 0.1, 0))
    pinch_points.add(adsk.core.Point3D.create(handle_length * 0.4, -handle_thickness * 0.15, 0))
    pinch_spline = splines.add(pinch_points)

    palm_offset = lines.addOffset(spline, palm_swell)
    for curve in palm_offset:
        curve.isConstruction = True

    pinch_spline.isConstruction = True


def _tag_named_faces(component: adsk.fusion.Component, faces: Sequence[str]) -> None:
    attribs = component.attributes
    for face_name in faces:
        attribs.add("ManufacturingLayer", face_name, "placeholder")


def _validate_material_and_process(design: adsk.fusion.Design) -> List[str]:
    errors: List[str] = []
    machine_cfg = load_machine_park()
    materials = load_material_catalog()
    catalog_codes = {str(entry.get("code", "")).upper() for entry in materials}

    cnc_cfg = machine_cfg.get("cnc_mill", {}).get("volume_mm", {})
    cnc_x = float(cnc_cfg.get("x", 400.0))
    cnc_y = float(cnc_cfg.get("y", 300.0))
    cnc_z = float(cnc_cfg.get("z", 120.0))

    printer_cfg = machine_cfg.get("printer", {}).get("volume_mm", {})
    printer_x = float(printer_cfg.get("x", 220.0))
    printer_y = float(printer_cfg.get("y", 220.0))
    printer_z = float(printer_cfg.get("z", 250.0))

    lathe_cfg = machine_cfg.get("lathe", {})
    lathe_swing = float(lathe_cfg.get("swing_diameter_mm", 180.0))

    blade_length = _get_param_value(design, "blade_length")
    blade_width_raw = _get_param_value(design, "blade_width_raw")
    spine_thickness_raw = _get_param_value(design, "spine_thickness_raw")
    handle_length = _get_param_value(design, "handle_length")
    handle_thickness = _get_param_value(design, "handle_thickness")

    if blade_length > cnc_x or blade_width_raw > cnc_y or spine_thickness_raw > cnc_z:
        errors.append(
            f"CNC-fresens arbeidsrom ({cnc_x}x{cnc_y}x{cnc_z} mm) overskrides av bladet."
        )
    if handle_length > printer_x or handle_thickness > printer_z:
        errors.append(
            f"3D-printerens volum ({printer_x}x{printer_y}x{printer_z} mm) overskrides av håndtaket."
        )
    if spine_thickness_raw > lathe_swing:
        errors.append(f"Dreibenkens Ø{lathe_swing} mm begrensning overskrides for ryggen.")

    required_codes = {"14C28N", "BIRCH"}
    missing = sorted(code for code in required_codes if code not in catalog_codes)
    if missing:
        errors.append("Manglende materialkoder i config: " + ", ".join(missing))

    return errors


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

    root = design.rootComponent
    xy_plane = root.xYConstructionPlane

    blade_sketch = _ensure_sketch(root.sketches, xy_plane, "blade_profile_sketch")
    handle_sketch = _ensure_sketch(root.sketches, xy_plane, "handle_profile_sketch")

    _draw_blade_profile(design, blade_sketch)
    _draw_handle_profile(design, handle_sketch)

    blade_comp = _ensure_component(root, "blade_comp")
    handle_comp = _ensure_component(root, "handle_comp")
    scale_left = _ensure_component(root, "scale_left")
    scale_right = _ensure_component(root, "scale_right")
    wedge_body = _ensure_component(root, "wedge_body")

    for comp in (blade_comp, handle_comp, scale_left, scale_right, wedge_body):
        _tag_named_faces(comp, MANUFACTURING_LAYER["named_faces"])

    validation_errors = _validate_material_and_process(design)

    if ui:
        status = _compose_status_message()
        if validation_errors:
            status += "\n\nValideringsfeil:\n" + "\n".join(validation_errors)
        else:
            status += "\n\nMaskin- og materialvalidering: OK"
        ui.messageBox(status)


def stop(context: str) -> None:
    print(f"Stopper skript :: {_COMPLIANCE_BANNER}")
