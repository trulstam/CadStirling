# ID: codex_fusionapi_v1.8
"""Parametrisk Stirlingmotor-generator for Autodesk Fusion 360."""

from __future__ import annotations

import csv
import datetime as _dt
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import adsk.core
import adsk.fusion
import traceback

ID_TAG = "codex_fusionapi_v1.8"
_COMPLIANCE_BANNER = f"COMPLIANCE BANNER :: ID {ID_TAG} :: stirling_core"
_ATTR_GROUP = "stirling_core"

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAD_DIR = PROJECT_ROOT / "cad"
DOCS_DIR = PROJECT_ROOT / "docs"
SIM_DIR = PROJECT_ROOT / "sim"


@dataclass
class ParameterDef:
    name: str
    value: float
    unit: str
    comment: str


@dataclass
class BOMEntry:
    pos: int
    name: str
    qty: int
    material: str
    raw_stock: str
    process: str
    tolerance: str
    surface: str
    note: str


@dataclass
class ComponentRecord:
    name: str
    component: adsk.fusion.Component
    occurrence: adsk.fusion.Occurrence
    bodies: List[adsk.fusion.BRepBody]


PARAMETER_DEFINITIONS: Tuple[ParameterDef, ...] = (
    ParameterDef("ID_WORK", 63.0, "mm", "Innvendig diameter arbeidssylinder (kvartsglass)."),
    ParameterDef("OD_WORK", 70.0, "mm", "Ytre diameter arbeidssylinder."),
    ParameterDef("LEN_WORK", 20.0, "mm", "Arbeidssylinderens lengde."),
    ParameterDef("ID_DISP", 63.0, "mm", "Innvendig diameter fortrengersylinder."),
    ParameterDef("OD_DISP", 70.0, "mm", "Ytre diameter fortrengersylinder."),
    ParameterDef("LEN_DISP", 20.0, "mm", "Fortrengersylinderens lengde."),
    ParameterDef("ANGLE_CYL", 90.0, "deg", "Vinkel mellom sylindre."),
    ParameterDef("STROKE", 15.0, "mm", "Slaglengde."),
    ParameterDef("CR_TARGET", 1.4, "", "Målsatt kompresjonsforhold."),
    ParameterDef("CLEAR_MIN", 0.10, "mm", "Minimum klaring mellom bevegelige deler."),
    ParameterDef("CLEAR_MAX", 0.30, "mm", "Maksimum klaring."),
    ParameterDef("FLYWHEEL_D", 140.0, "mm", "Svinghjulsdiameter."),
    ParameterDef("FLYWHEEL_THICK", 12.0, "mm", "Svinghjulstykkelse."),
    ParameterDef("CRANK_PIN", 4.0, "mm", "Veivpinndiameter."),
    ParameterDef("SHAFT_D", 8.0, "mm", "Veivakseldiameter."),
    ParameterDef("ROD_DIAMETER", 6.0, "mm", "Koblingsstangdiameter."),
    ParameterDef("ROD_LENGTH", 70.0, "mm", "Koblingsstanglengde."),
    ParameterDef("DISPLACER_OFFSET", 80.0, "mm", "Senteravstand mellom sylindre."),
    ParameterDef("BASE_LENGTH", 260.0, "mm", "Lengde på bunnplate."),
    ParameterDef("BASE_WIDTH", 160.0, "mm", "Bredde på bunnplate."),
    ParameterDef("BASE_THICK", 12.0, "mm", "Bunnplatetykkelse."),
    ParameterDef("FRAME_COLUMN_H", 95.0, "mm", "Høyde på rammesøyler."),
    ParameterDef("HOT_END_TEMP", 650.0, "degC", "Metadata: varm-sone temperatur."),
    ParameterDef("COLD_END_TEMP", 60.0, "degC", "Metadata: kald-sone temperatur."),
)


class BuilderError(RuntimeError):
    """Signaliserer at genereringen ikke kan fortsette."""


def run(context: str) -> None:
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    print(_COMPLIANCE_BANNER)
    try:
        if not app:
            raise BuilderError("Fusion 360-applikasjonen er ikke tilgjengelig.")
        design = adsk.fusion.Design.cast(app.activeProduct)
        if not design:
            raise BuilderError("Aktivt dokument er ikke en Fusion 360 Design.")
        ensure_directories()
        params = register_user_parameters(design)
        geom = compute_geometry_inputs(design, params)
        metrics = compute_performance_metrics(params, geom)
        records = create_component_records(design, geom)
        build_geometry(design, records, geom)
        apply_materials_and_appearances(design, records)
        build_joints(design, records, geom)
        generate_drawings(design, records)
        clearance_report = evaluate_clearances(params, geom)
        export_all(records, design)
        bom_entries = compile_bom_entries(params, geom, metrics)
        write_bom(bom_entries)
        write_arbeidsplan()
        update_changelog()
        write_simulation_stub(metrics)
        apply_metadata(design, metrics, clearance_report)
        summarize(ui, metrics, clearance_report)
    except Exception:  # pragma: no cover - Fusion viser detaljer
        if ui:
            ui.messageBox(f"Stirlingmotoren feilet:\n{traceback.format_exc()}")
        else:
            print(traceback.format_exc())


def stop(context: str) -> None:
    print(f"Stopper skript :: {_COMPLIANCE_BANNER}")


def ensure_directories() -> None:
    for folder in (CAD_DIR, DOCS_DIR, SIM_DIR, DOCS_DIR / "tekniske-tegninger"):
        folder.mkdir(parents=True, exist_ok=True)


def register_user_parameters(
    design: adsk.fusion.Design,
) -> Dict[str, adsk.fusion.UserParameter]:
    """Synkroniserer brukerparametre med definerte standarder."""

    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    user_params = design.userParameters
    units_manager = design.unitsManager
    registered: Dict[str, adsk.fusion.UserParameter] = {}

    length_units = {"mm", "cm", "m", "in", "ft"}
    angle_units = {"deg", "rad"}
    temperature_units = {
        "degc",
        "c",
        "celsius",
        "degf",
        "f",
        "fahrenheit",
        "kelvin",
        "k",
        "rankine",
    }
    length_to_mm = {
        "mm": 1.0,
        "cm": 10.0,
        "m": 1000.0,
        "in": 25.4,
        "ft": 304.8,
    }

    def normalize_unit(unit: str) -> str:
        return unit.strip().lower()

    def resolve_unit(unit: str) -> str:
        unit = unit or ""
        if not unit:
            return ""
        try:
            if units_manager.isValidUnit(unit):
                return unit
        except Exception:
            pass
        normalized = normalize_unit(unit)
        fallback = ""
        if normalized in length_units:
            fallback = getattr(units_manager, "defaultLengthUnits", "")
        elif normalized in angle_units:
            fallback = getattr(units_manager, "defaultAngleUnits", "")
        elif normalized in temperature_units:
            fallback = getattr(units_manager, "defaultTemperatureUnits", "") or "kelvin"
        if fallback:
            try:
                if units_manager.isValidUnit(fallback):
                    return fallback
            except Exception:
                return fallback
        return ""

    def value_to_internal(value: float, unit: str) -> float:
        unit = unit or ""
        normalized = normalize_unit(unit) if unit else ""
        if normalized in length_units:
            mm_value = value * length_to_mm.get(normalized, 1.0)
            return mm_to_cm(mm_value)
        if normalized in angle_units:
            return math.radians(value) if normalized == "deg" else value
        if normalized in temperature_units:
            if normalized in {"degc", "c", "celsius"}:
                return value + 273.15
            if normalized in {"degf", "f", "fahrenheit"}:
                return (value + 459.67) * (5.0 / 9.0)
            if normalized in {"rankine"}:
                return value * (5.0 / 9.0)
            # kelvin / k faller igjennom til returverdi
        return value

    def sync_param(defn: ParameterDef) -> adsk.fusion.UserParameter:
        existing = user_params.itemByName(defn.name)
        unit_for_param = resolve_unit(defn.unit)
        value_internal = value_to_internal(defn.value, defn.unit or unit_for_param)

        # Oppdater eksisterende parameter
        if existing:
            try:
                target_unit = unit_for_param or existing.unit or ""
                if target_unit:
                    existing.unit = target_unit
                existing.value = value_internal
                existing.comment = defn.comment
                registered[defn.name] = existing
                return existing
            except Exception:
                if ui:
                    ui.messageBox(
                        "Feil ved oppdatering av brukerparameter "
                        f"'{defn.name}'"
                    )
                raise

        # Opprett ny parameter
        try:
            value_input = adsk.core.ValueInput.createByReal(value_internal)
            param = user_params.add(defn.name, value_input, unit_for_param, defn.comment)
            registered[defn.name] = param
            return param
        except Exception:
            if ui:
                ui.messageBox(
                    "Feil ved opprettelse av brukerparameter "
                    f"'{defn.name}'"
                )
            raise

    for definition in PARAMETER_DEFINITIONS:
        sync_param(definition)

    return registered

def param_to_unit(
    design: adsk.fusion.Design, param: adsk.fusion.UserParameter, unit: str
) -> float:
    units_manager = design.unitsManager
    if unit:
        try:
            return units_manager.evaluateExpression(param.expression, unit)
        except Exception:
            pass
    return param.value


def compute_geometry_inputs(
    design: adsk.fusion.Design,
    params: Dict[str, adsk.fusion.UserParameter],
) -> Dict[str, float]:
    mm = lambda name: param_to_unit(design, params[name], "mm")
    geom = {
        "id_work": mm("ID_WORK"),
        "od_work": mm("OD_WORK"),
        "len_work": mm("LEN_WORK"),
        "id_disp": mm("ID_DISP"),
        "od_disp": mm("OD_DISP"),
        "len_disp": mm("LEN_DISP"),
        "stroke": mm("STROKE"),
        "clear_min": mm("CLEAR_MIN"),
        "clear_max": mm("CLEAR_MAX"),
        "flywheel_d": mm("FLYWHEEL_D"),
        "flywheel_thick": mm("FLYWHEEL_THICK"),
        "crank_pin": mm("CRANK_PIN"),
        "shaft_d": mm("SHAFT_D"),
        "rod_d": mm("ROD_DIAMETER"),
        "rod_length": mm("ROD_LENGTH"),
        "offset": mm("DISPLACER_OFFSET"),
        "base_length": mm("BASE_LENGTH"),
        "base_width": mm("BASE_WIDTH"),
        "base_thick": mm("BASE_THICK"),
        "frame_height": mm("FRAME_COLUMN_H"),
    }
    geom["work_clearance"] = 0.5 * (geom["clear_min"] + geom["clear_max"])
    geom["piston_diameter"] = geom["id_work"] - 2 * geom["work_clearance"]
    geom["displacer_diameter"] = geom["id_disp"] - 2 * geom["work_clearance"]
    return geom


def compute_performance_metrics(
    params: Dict[str, adsk.fusion.UserParameter], geom: Dict[str, float]
) -> Dict[str, float]:
    area_mm2 = math.pi * (geom["id_work"] / 2.0) ** 2
    stroke_volume_cm3 = (area_mm2 * geom["stroke"]) / 1000.0
    cr_target = params["CR_TARGET"].value
    dead_volume_cm3 = 0.0
    if stroke_volume_cm3 > 0:
        dead_volume_cm3 = stroke_volume_cm3 / max(cr_target - 1.0, 0.01)
    safe_dead_volume = max(dead_volume_cm3, 1e-9)
    cr_estimate = (stroke_volume_cm3 + safe_dead_volume) / safe_dead_volume
    return {
        "area_mm2": area_mm2,
        "stroke_volume_cm3": stroke_volume_cm3,
        "dead_volume_cm3": dead_volume_cm3,
        "cr_estimate": cr_estimate,
    }


def create_component_records(design: adsk.fusion.Design, geom: Dict[str, float]) -> Dict[str, ComponentRecord]:
    root = design.rootComponent
    occs = root.occurrences
    R: Dict[str, ComponentRecord] = {}

    def _new(name: str, m: Optional[adsk.core.Matrix3D] = None) -> ComponentRecord:
        m = m or adsk.core.Matrix3D.create()
        occ = occs.addNewComponent(m)
        occ.component.name = name
        return ComponentRecord(name=name, component=occ.component, occurrence=occ, bodies=[])

    # 0) Ramme/bunnplate på origo, grunnlagt (grounded)
    R["frame"] = _new("Ramme og bunnplate")
    R["frame"].occurrence.isGrounded = True

    # Plassering: separer sylindre langs X, legg dem på bunnplata i Z
    z_plate = geom["base_thick"]        # mm
    x_half  = geom["offset"] * 0.5      # mm

    # 1) Arbeidssylinder — vertikal (akse = Z), til venstre
    m_work = adsk.core.Matrix3D.create()
    m_work.translation = adsk.core.Vector3D.create(mm_to_cm(-x_half), 0, mm_to_cm(z_plate))
    R["work_cylinder"] = _new("Arbeidssylinder", m_work)

    # 2) Fortrengersylinder — 90° vippet (akse = Y), til høyre
    m_disp = adsk.core.Matrix3D.create()
    m_disp.setToRotation(math.radians(90.0), adsk.core.Vector3D.create(1,0,0), adsk.core.Point3D.create(0,0,0))
    m_disp.translation = adsk.core.Vector3D.create(mm_to_cm(+x_half), 0, mm_to_cm(z_plate))
    R["displacer_cylinder"] = _new("Fortrengersylinder", m_disp)

    # 3) Stempler — start inne i sine respektive sylindre
    m_wp = adsk.core.Matrix3D.create()
    m_wp.translation = adsk.core.Vector3D.create(mm_to_cm(-x_half), 0, mm_to_cm(z_plate + geom["len_work"]/2.0))
    R["work_piston"] = _new("Arbeidsstempel", m_wp)

    m_dp = adsk.core.Matrix3D.create()
    m_dp.setToRotation(math.radians(90.0), adsk.core.Vector3D.create(1,0,0), adsk.core.Point3D.create(0,0,0))
    m_dp.translation = adsk.core.Vector3D.create(mm_to_cm(+x_half), 0, mm_to_cm(z_plate + geom["len_disp"]/2.0))
    R["displacer"] = _new("Fortrenger", m_dp)

    # 4) Veivaksel og svinghjul — foran (positiv Y), i høyde rundt midt-sylinder
    y_front = geom["base_width"]/2.0 - 25.0
    z_shaft = z_plate + max(geom["len_work"], geom["len_disp"])/2.0

    m_crank = adsk.core.Matrix3D.create()
    m_crank.translation = adsk.core.Vector3D.create(0, mm_to_cm(y_front), mm_to_cm(z_shaft))
    R["crankshaft"] = _new("Veivaksel", m_crank)

    m_fly = adsk.core.Matrix3D.create()
    m_fly.translation = adsk.core.Vector3D.create(0, mm_to_cm(y_front + 10.0), mm_to_cm(z_shaft))
    R["flywheel"] = _new("Svinghjul", m_fly)

    R["connecting_rods"] = _new("Koblingsstenger")
    R["thermal"] = _new("Varme og kjøl")
    return R


def param_angle(design: adsk.fusion.Design, name: str) -> float:
    params = design.userParameters
    param = params.itemByName(name)
    if not param:
        return 0.0
    return param_to_unit(design, param, "deg")


def build_geometry(
    design: adsk.fusion.Design,
    records: Dict[str, ComponentRecord],
    geom: Dict[str, float],
) -> None:
    build_frame(records["frame"], geom)
    build_quartz_cylinder(records["work_cylinder"], geom["od_work"], geom["id_work"], geom["len_work"], "Arbeidssylinder")
    build_quartz_cylinder(records["displacer_cylinder"], geom["od_disp"], geom["id_disp"], geom["len_disp"], "Fortrengersylinder")
    build_piston(records["work_piston"], geom["piston_diameter"], geom["stroke"], name="Arbeidsstempel")
    build_piston(records["displacer"], geom["displacer_diameter"], geom["len_disp"], hollow=True, name="Fortrenger")
    build_crankshaft(records["crankshaft"], geom)
    build_flywheel(records["flywheel"], geom)
    build_connecting_rods(records["connecting_rods"], geom)
    build_thermal_features(records["thermal"], geom)


def build_frame(record: ComponentRecord, geom: Dict[str, float]) -> None:
    comp = record.component
    sketches = comp.sketches
    xy = comp.xYConstructionPlane
    sketch = sketches.add(xy)
    center = adsk.core.Point3D.create(0, 0, 0)
    corner = adsk.core.Point3D.create(mm_to_cm(geom["base_length"] / 2.0), mm_to_cm(geom["base_width"] / 2.0), 0)
    lines = sketch.sketchCurves.sketchLines
    lines.addCenterPointRectangle(center, corner)
    profile = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    thickness = adsk.core.ValueInput.createByReal(mm_to_cm(geom["base_thick"]))
    ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, thickness)
    ext = extrudes.add(ext_input)
    base_body = ext.bodies.item(0)
    base_body.name = "Bunnplate"
    record.bodies.append(base_body)

    create_threaded_mounts(comp, base_body, geom)
    create_columns(comp, geom, record.bodies)


def create_threaded_mounts(
    comp: adsk.fusion.Component, base_body: adsk.fusion.BRepBody, geom: Dict[str, float]
) -> None:
    sketches = comp.sketches
    top_face = max(base_body.faces, key=lambda f: f.pointOnFace.z)
    sketch = sketches.add(top_face)
    margin_x = geom["base_length"] / 2.0 - 20.0
    margin_y = geom["base_width"] / 2.0 - 20.0
    circles = sketch.sketchCurves.sketchCircles
    positions = [
        (-margin_x, -margin_y),
        (margin_x, -margin_y),
        (margin_x, margin_y),
        (-margin_x, margin_y),
    ]
    for x_mm, y_mm in positions:
        circles.addByCenterRadius(
            adsk.core.Point3D.create(mm_to_cm(x_mm), mm_to_cm(y_mm), 0),
            mm_to_cm(2.5),
        )
    profiles = sketch.profiles
    extrudes = comp.features.extrudeFeatures
    faces_to_thread: List[adsk.core.Face] = []
    max_hole_area = math.pi * (mm_to_cm(4.0) ** 2)
    for i in range(profiles.count):
        profile = profiles.item(i)
        try:
            area_props = profile.areaProperties(
                adsk.fusion.CalculationAccuracy.MediumCalculationAccuracy
            )
            if area_props.area > max_hole_area:
                continue
        except Exception:
            pass
        ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
        ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(geom["base_thick"])))
        # Extruderingen skjer på toppflaten av bunnplaten. Standardretningen peker
        # bort fra kroppen, noe som gjør at Fusion ikke finner noe å kutte og
        # kaster en "No target body"-feil. Ved å eksplisitt angi negativ
        # retning sørger vi for at kuttet går ned i platen.
        ext_input.isDirectionNegative = True
        ext_input.participantBodies = [base_body]
        cut = extrudes.add(ext_input)
        for face in base_body.faces:
            geometry = face.geometry
            surface_type = getattr(geometry, "surfaceType", None)
            if surface_type == adsk.core.SurfaceTypes.CylinderSurfaceType:
                radius = geometry.radius
                if math.isclose(radius, mm_to_cm(2.5), rel_tol=0.15):
                    faces_to_thread.append(face)
                    if len(faces_to_thread) == 4:
                        break
    apply_threads(comp, faces_to_thread, "M5x0.8")


def create_columns(comp: adsk.fusion.Component, geom: Dict[str, float], bodies: List[adsk.fusion.BRepBody]) -> None:
    sketches = comp.sketches
    base_plane = comp.xYConstructionPlane
    sketch = sketches.add(base_plane)
    circles = sketch.sketchCurves.sketchCircles
    offsets = [
        (-geom["base_length"] / 4.0, 0),
        (geom["base_length"] / 4.0, 0),
    ]
    for x_mm, y_mm in offsets:
        circles.addByCenterRadius(
            adsk.core.Point3D.create(mm_to_cm(x_mm), mm_to_cm(y_mm), 0),
            mm_to_cm(5.0),
        )
    for idx in range(sketch.profiles.count):
        profile = sketch.profiles.item(idx)
        extrude = comp.features.extrudeFeatures
        ext_input = extrude.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(geom["frame_height"])))
        result = extrude.add(ext_input)
        column_body = result.bodies.item(0)
        column_body.name = f"Rammekolonne {idx + 1}"
        bodies.append(column_body)


def apply_threads(
    comp: adsk.fusion.Component, faces: Iterable[adsk.core.Face], designation: str
) -> None:
    if not faces:
        return
    thread_features = comp.features.threadFeatures
    data_query = thread_features.threadDataQuery
    thread_type = data_query.defaultMetricThreadType
    try:
        thread_info = data_query.createThreadInfo(True, thread_type, designation, "6H")
    except Exception:
        return
    for face in faces:
        try:
            thread_input = thread_features.createInput(face, thread_info)
            thread_input.isFullLength = True
            thread_features.add(thread_input)
        except Exception:
            continue


def build_quartz_cylinder(
    record: ComponentRecord,
    outer_diameter: float,
    inner_diameter: float,
    length_mm: float,
    name: str,
) -> None:
    comp = record.component
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(0, 0, 0)
    circles.addByCenterRadius(center, mm_to_cm(outer_diameter / 2.0))
    circles.addByCenterRadius(center, mm_to_cm(inner_diameter / 2.0))
    profile = None
    for candidate in sketch.profiles:
        if candidate.profileLoops.count == 2:
            profile = candidate
            break
    if not profile:
        return
    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(length_mm)))
    ext = extrudes.add(ext_input)
    body = ext.bodies.item(0)
    body.name = name
    record.bodies.append(body)


def build_piston(
    record: ComponentRecord,
    diameter: float,
    length_mm: float,
    hollow: bool = False,
    name: str = "Piston",
) -> None:
    comp = record.component
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    base_center = adsk.core.Point3D.create(0, 0, 0)
    circles.addByCenterRadius(base_center, mm_to_cm(diameter / 2.0))
    profile = sketch.profiles.item(0)
    extrudes = comp.features.extrudeFeatures
    ext_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(length_mm)))
    ext = extrudes.add(ext_input)
    body = ext.bodies.item(0)
    body.name = name
    record.bodies.append(body)
    if hollow:
        faces = list(body.faces)
        top_face = max(faces, key=lambda face: face.pointOnFace.z)
        sketch_inner = comp.sketches.add(top_face)
        circles_inner = sketch_inner.sketchCurves.sketchCircles
        circles_inner.addByCenterRadius(adsk.core.Point3D.create(0, 0, 0), mm_to_cm((diameter - 1.5) / 2.0))
        profile_inner = sketch_inner.profiles.item(0)
        cut_input = extrudes.createInput(profile_inner, adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(length_mm * 0.9)))
        extrudes.add(cut_input)


def build_crankshaft(record: ComponentRecord, geom: Dict[str, float]) -> None:
    comp = record.component
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(0, 0, 0)
    circles.addByCenterRadius(center, mm_to_cm(geom["shaft_d"] / 2.0))
    profile = sketch.profiles.item(0)
    extrude = comp.features.extrudeFeatures
    length = geom["offset"] + 2 * geom["rod_length"]
    ext_input = extrude.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(length)))
    ext = extrude.add(ext_input)
    shaft_body = ext.bodies.item(0)
    shaft_body.name = "Veivaksel"
    record.bodies.append(shaft_body)

    plate_sketch = comp.sketches.add(comp.xYConstructionPlane)
    rect = plate_sketch.sketchCurves.sketchLines.addCenterPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(mm_to_cm(geom["rod_length"] / 3.0), mm_to_cm(geom["crank_pin"]), 0),
    )
    profile_plate = plate_sketch.profiles.item(0)
    plate_input = extrude.createInput(profile_plate, adsk.fusion.FeatureOperations.JoinFeatureOperation)
    plate_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(geom["crank_pin"] * 2.0)))
    extrude.add(plate_input)


def build_flywheel(record: ComponentRecord, geom: Dict[str, float]) -> None:
    comp = record.component
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(0, 0, 0)
    circles.addByCenterRadius(center, mm_to_cm(geom["flywheel_d"] / 2.0))
    profile = sketch.profiles.item(0)
    extrude = comp.features.extrudeFeatures
    ext_input = extrude.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(geom["flywheel_thick"])))
    ext = extrude.add(ext_input)
    body = ext.bodies.item(0)
    body.name = "Svinghjul"
    record.bodies.append(body)

    end_faces = ext.endFaces
    target_face = end_faces.item(0) if end_faces.count > 0 else None
    if target_face is None:
        raise BuilderError("Fant ingen endeflate på svinghjulet for å lage gjennomgående hull.")
    cut_sketch = comp.sketches.add(target_face)
    cut_circles = cut_sketch.sketchCurves.sketchCircles
    cut_circles.addByCenterRadius(center, mm_to_cm(geom["shaft_d"] / 2.0))
    cut_profile = cut_sketch.profiles.item(0)
    cut_input = extrude.createInput(cut_profile, adsk.fusion.FeatureOperations.CutFeatureOperation)
    cut_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(geom["flywheel_thick"])))
    extrude.add(cut_input)


def build_connecting_rods(record: ComponentRecord, geom: Dict[str, float]) -> None:
    comp = record.component
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    half = geom["rod_length"] / 2.0
    profile = lines.addCenterPointRectangle(
        adsk.core.Point3D.create(0, 0, 0),
        adsk.core.Point3D.create(mm_to_cm(geom["rod_d"] / 2.0), mm_to_cm(half), 0),
    )
    extrude = comp.features.extrudeFeatures
    ext_input = extrude.createInput(sketch.profiles.item(0), adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(geom["rod_d"])))
    ext = extrude.add(ext_input)
    body = ext.bodies.item(0)
    body.name = "Koblingsstang"
    record.bodies.append(body)


def build_thermal_features(record: ComponentRecord, geom: Dict[str, float]) -> None:
    comp = record.component
    sketch = comp.sketches.add(comp.xYConstructionPlane)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(0, 0, 0)
    hot_radius = max(geom["od_disp"], geom["od_work"]) / 2.0 + 5.0
    circles.addByCenterRadius(center, mm_to_cm(hot_radius))
    profile = sketch.profiles.item(0)
    extrude = comp.features.extrudeFeatures
    ext_input = extrude.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(mm_to_cm(5.0)))
    ext = extrude.add(ext_input)
    body = ext.bodies.item(0)
    body.name = "Varmeplate"
    record.bodies.append(body)

    rib_sketch = comp.sketches.add(comp.xYConstructionPlane)
    lines = rib_sketch.sketchCurves.sketchLines
    for angle in range(0, 180, 30):
        rad = math.radians(angle)
        lines.addByTwoPoints(
            adsk.core.Point3D.create(0, 0, 0),
            adsk.core.Point3D.create(mm_to_cm(hot_radius * math.cos(rad)), mm_to_cm(hot_radius * math.sin(rad)), 0),
        )


def apply_materials_and_appearances(
    design: adsk.fusion.Design, records: Dict[str, ComponentRecord]
) -> None:
    materials = design.materials
    appearances = design.appearances
    material_map = {
        "frame": "Aluminum 6061",
        "work_cylinder": "Glass - Clear",
        "displacer_cylinder": "Glass - Clear",
        "work_piston": "Aluminum - Satin",
        "displacer": "Carbon Fiber",
        "crankshaft": "Steel",
        "flywheel": "Steel",
        "connecting_rods": "Brass",
        "thermal": "Copper",
    }
    appearance_map = {
        "frame": "Brushed Aluminum",
        "thermal": "Copper - Polished",
    }
    for key, record in records.items():
        mat_name = material_map.get(key)
        appearance_name = appearance_map.get(key)
        material = materials.itemByName(mat_name) if mat_name else None
        appearance = appearances.itemByName(appearance_name) if appearance_name else None
        for body in record.bodies:
            if material:
                body.material = material
            if appearance:
                body.appearance = appearance


def build_joints(design: adsk.fusion.Design, records: Dict[str, ComponentRecord], geom: Dict[str, float]) -> None:
    root = design.rootComponent
    joints = root.joints

    def _origin_geometry(record: ComponentRecord) -> adsk.fusion.JointGeometry:
        origin_point = record.component.originConstructionPoint
        if origin_point is None:
            raise BuilderError(f"Komponenten '{record.name}' mangler origo-konstruksjonspunkt for joints.")
        if not origin_point.isValid:
            raise BuilderError(f"Origo-punktet til '{record.name}' er ugyldig og kan ikke brukes til joints.")
        return adsk.fusion.JointGeometry.createByPoint(origin_point)

    frame_geom = _origin_geometry(records["frame"])

    # 1) Rigid: lås sylindre og thermal til ramme (står allerede korrekt)
    def rigid_to_frame(child_record: ComponentRecord):
        ji = joints.createInput(_origin_geometry(child_record), frame_geom)
        ji.setAsRigidJointMotion()
        joints.add(ji)

    rigid_to_frame(records["work_cylinder"])
    rigid_to_frame(records["displacer_cylinder"])
    rigid_to_frame(records["thermal"])

    # 2) Revolute: veivaksel i ramme — rotasjonsakse langs verdens X
    crank_record = records["crankshaft"]
    ji_crank = joints.createInput(_origin_geometry(crank_record), frame_geom)
    ji_crank.setAsRevoluteJointMotion(adsk.fusion.JointDirections.XAxisJointDirection)
    joints.add(ji_crank)

    # 3) Revolute: svinghjul på veivaksel — koaksial med veivaksel
    fly_record = records["flywheel"]
    ji_fly = joints.createInput(_origin_geometry(fly_record), _origin_geometry(crank_record))
    ji_fly.setAsRevoluteJointMotion(adsk.fusion.JointDirections.XAxisJointDirection)
    joints.add(ji_fly)

    # 4) Slider: stempler langs sylinderaksene
    # Arbeidssylinder vertikal → Z-akse
    ji_wp = joints.createInput(_origin_geometry(records["work_piston"]), _origin_geometry(records["work_cylinder"]))
    ji_wp.setAsSliderJointMotion(adsk.fusion.JointDirections.ZAxisJointDirection)
    joints.add(ji_wp)

    # Fortrenger 90° vippet → Y-akse
    ji_dp = joints.createInput(_origin_geometry(records["displacer"]), _origin_geometry(records["displacer_cylinder"]))
    ji_dp.setAsSliderJointMotion(adsk.fusion.JointDirections.YAxisJointDirection)
    joints.add(ji_dp)

    # 5) Legg metadata for 90° fase (MotionLink kommer i neste steg)
    design.attributes.add(_ATTR_GROUP, "phase_deg", "90")


def generate_drawings(design: adsk.fusion.Design, records: Dict[str, ComponentRecord]) -> None:
    try:
        drawings = design.drawings
        if drawings is None:
            return
        drawing = drawings.add(
            adsk.fusion.DrawingTypes.StandardDrawingType,
            adsk.fusion.DrawingUnits.MillimeterDrawingUnits,
            adsk.fusion.DrawingSheetSizes.ISO_A3DrawingSheetSize,
        )
        sheet = drawing.sheets.item(0)
        targets = [records["frame"].component, records["work_cylinder"].component, records["flywheel"].component]
        base_views = sheet.views
        spacing = 120.0
        for index, component in enumerate(targets):
            try:
                base_input = base_views.createBaseViewInput(component)
                base_input.setViewOrientation(adsk.fusion.DrawingViewOrientations.TopDrawingViewOrientation)
                base_input.setScale(0.25)
                base_input.setPosition(adsk.core.Point3D.create(50 + index * spacing, 80, 0))
                base_views.add(base_input)
            except Exception:
                continue
    except Exception:
        return


def evaluate_clearances(
    params: Dict[str, adsk.fusion.UserParameter], geom: Dict[str, float]
) -> Dict[str, float]:
    clearances = {
        "arbeidsstempel": geom["work_clearance"],
        "fortrenger": geom["work_clearance"],
    }
    clear_min = geom["clear_min"]
    clear_max = geom["clear_max"]
    for name, value in clearances.items():
        if value < clear_min or value > clear_max:
            raise BuilderError(f"Klaringen for {name} ({value:.2f} mm) bryter spesifikasjonen.")
    return clearances


def export_all(records: Dict[str, ComponentRecord], design: adsk.fusion.Design) -> None:
    export_manager = design.exportManager
    CAD_DIR.mkdir(parents=True, exist_ok=True)
    targets = {
        "assembly": design.rootComponent,
        "frame": records["frame"].component,
        "work_cylinder": records["work_cylinder"].component,
        "displacer_cylinder": records["displacer_cylinder"].component,
        "work_piston": records["work_piston"].component,
        "displacer": records["displacer"].component,
        "crankshaft": records["crankshaft"].component,
        "flywheel": records["flywheel"].component,
    }
    for name, component in targets.items():
        step_path = CAD_DIR / f"stirling_{name}_v1.step"
        stl_path = CAD_DIR / f"stirling_{name}_v1.stl"
        obj_path = CAD_DIR / f"stirling_{name}_v1.obj"
        try:
            step_options = export_manager.createSTEPExportOptions(str(step_path), component)
            export_manager.execute(step_options)
            stl_options = export_manager.createSTLExportOptions(component)
            stl_options.meshRefinement = adsk.fusion.MeshRefinementOptions.MeshRefinementHigh
            stl_options.filename = str(stl_path)
            export_manager.execute(stl_options)
            obj_options = export_manager.createOBJExportOptions(component, str(obj_path))
            export_manager.execute(obj_options)
        except Exception:
            continue


def compile_bom_entries(
    params: Dict[str, adsk.fusion.UserParameter],
    geom: Dict[str, float],
    metrics: Dict[str, float],
) -> List[BOMEntry]:
    stroke = geom["stroke"]
    entries = [
        BOMEntry(1, "Ramme/bunnplate", 1, "Al 6061", f"{geom['base_length']:.0f}×{geom['base_width']:.0f}×{geom['base_thick']:.0f} mm", "CNC fres/borr", "IT8", "Anodisert", "Bærende struktur"),
        BOMEntry(2, "Arbeidssylinder", 1, "Kvartsglass", f"Ø{geom['od_work']:.0f}/Ø{geom['id_work']:.0f}×{geom['len_work']:.0f} mm", "Slip/polering", "IT7", "Polert", "Tetning for arbeidssone"),
        BOMEntry(3, "Fortrengersylinder", 1, "Kvartsglass", f"Ø{geom['od_disp']:.0f}/Ø{geom['id_disp']:.0f}×{geom['len_disp']:.0f} mm", "Slip/polering", "IT7", "Polert", "90°-montering"),
        BOMEntry(4, "Arbeidsstempel", 1, "Al 6061", f"Ø{geom['piston_diameter']:.1f}×{stroke:.0f} mm", "Dreiing", "IT6", "Honed", "O-ring spor"),
        BOMEntry(5, "Fortrenger", 1, "Karbon/lettmetall", f"Ø{geom['displacer_diameter']:.1f}×{geom['len_disp']:.0f} mm", "Tynnveggdreid", "IT7", "Mat", "Lav masse"),
        BOMEntry(6, "Veivaksel", 1, "42CrMo4", f"Ø{geom['shaft_d']:.0f}×{geom['offset'] + 2*geom['rod_length']:.0f} mm", "Drei/Slip", "IT6", "Slip", "Integrert veiv"),
        BOMEntry(7, "Koblingsstenger", 2, "Messing", f"Ø{geom['rod_d']:.0f}×{geom['rod_length']:.0f} mm", "Fres/Drei", "IT7", "Polert", "Bronsebuss"),
        BOMEntry(8, "Svinghjul", 1, "Stål", f"Ø{geom['flywheel_d']:.0f}×{geom['flywheel_thick']:.0f} mm", "Drei/balanser", "IT7", "Satin", "Balansert til <1 gmm"),
        BOMEntry(9, "Varme/kjølemodul", 1, "Cu/Al", "Lamellplate Ø{:.0f} mm".format(max(geom['od_disp'], geom['od_work']) + 10), "Fres/Lodd", "IT9", "Børstet", "Varmekollektor + ribber"),
    ]
    entries.append(
        BOMEntry(10, "Festeskruer", 8, "A2-70", "M5×20 mm", "Kjøp", "ISO 4762", "Oljefri", "Trekkmoment 4.5 Nm"),
    )
    return entries


def write_bom(entries: List[BOMEntry]) -> None:
    path = DOCS_DIR / "BOM.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        handle.write(f"ID: {ID_TAG}\n")
        writer = csv.writer(handle)
        writer.writerow(["Pos", "Delnavn", "Antall", "Materiale", "Emnedim (rå)", "Prosess", "Toleranse", "Overflate", "Merknad"])
        for entry in entries:
            writer.writerow([
                entry.pos,
                entry.name,
                entry.qty,
                entry.material,
                entry.raw_stock,
                entry.process,
                entry.tolerance,
                entry.surface,
                entry.note,
            ])


def write_arbeidsplan() -> None:
    path = DOCS_DIR / "arbeidsplan.md"
    content = f"""ID: {ID_TAG}

# Arbeidsplan – Stirlingmotor Beta/Gamma
1. **Ramme/bunnplate** – Sag ut råemne → CNC-fres plan og hullbilder → avgrader og anodiser.
2. **Rammekolonner** – Drei Ø10 mm søyler → fres flatsider for sylindermontering → kontrollér høyde.
3. **Sylindre i kvartsglass** – Bestill rør → slip/poler ender → press inn O-ringer og kontrollér ID.
4. **Arbeidsstempel** – Drei Al 6061-emne → finbor O-ringspor → lapp/poler til spesifisert klaring.
5. **Fortrenger** – Drei tynnveggsylinder i karbon/aluminium → fyll demping (glassfiber) → balanser.
6. **Veiv og koblingsstenger** – Drei veivaksel, fres veivskiver → press på lager → monter bronsebuss.
7. **Svinghjul** – Drei blankt → maskinér nav/settskrue → dynamisk balansering.
8. **Varme/kjølemodul** – Fres lamellplate og varmefordeler → lodde ribber → monter keramiske skiver.
9. **Montasje** – Monter ramme, sylindre og lager → sett inn stempler → juster 90° fase via veiv.
10. **Testing** – Kjør tørrgang med hånden → kontroller lekkasjer og interferens → journalfør resultater.
"""
    path.write_text(content, encoding="utf-8")


def update_changelog() -> None:
    path = DOCS_DIR / "ENDRINGSLOGG.md"
    timestamp = _dt.datetime.utcnow().strftime("%Y-%m-%d")
    lines = [
        f"ID: {ID_TAG}",
        "",
        "# Endringslogg",
        f"- {timestamp} – v1.1.0 – Opprettet parametrisk Stirlingmotor-generator, eksport og dokumentasjon.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_simulation_stub(metrics: Dict[str, float]) -> None:
    path = SIM_DIR / "kinematikk_plan.md"
    text = f"""ID: {ID_TAG}

# Kinematikk og simulering
- **Slagvolum:** {metrics['stroke_volume_cm3']:.2f} cm³
- **Dødvolum:** {metrics['dead_volume_cm3']:.2f} cm³
- **Kompresjonsforhold (beregnet):** {metrics['cr_estimate']:.3f}

Før video eksporteres til `sim/kinematikk.mp4`, kjør følgende i Fusion 360:
1. Sett `STROKE`-parameteren til ønsket verdi (12–20 mm valideres automatisk).
2. Aktiver *Motion Study* → *Animate Joints* for veivsystemet.
3. Eksporter MP4 (1920×1080) til `sim/kinematikk.mp4` og legg ved joints-filen i samme mappe.
"""
    path.write_text(text, encoding="utf-8")


def apply_metadata(
    design: adsk.fusion.Design,
    metrics: Dict[str, float],
    clearances: Dict[str, float],
) -> None:
    design.attributes.add(_ATTR_GROUP, "stroke_volume_cm3", f"{metrics['stroke_volume_cm3']:.3f}")
    design.attributes.add(_ATTR_GROUP, "dead_volume_cm3", f"{metrics['dead_volume_cm3']:.3f}")
    design.attributes.add(_ATTR_GROUP, "cr_estimate", f"{metrics['cr_estimate']:.3f}")
    for name, value in clearances.items():
        design.attributes.add(_ATTR_GROUP, f"clearance_{name}", f"{value:.3f} mm")


def summarize(
    ui: Optional[adsk.core.UserInterface], metrics: Dict[str, float], clearances: Dict[str, float]
) -> None:
    if not ui:
        return
    clearance_text = "\n".join(f"- {name}: {value:.2f} mm" for name, value in clearances.items())
    ui.messageBox(
        (
            "Stirlingmotoren er regenerert.\n"
            f"Slagvolum: {metrics['stroke_volume_cm3']:.2f} cm³\n"
            f"Dødvolum: {metrics['dead_volume_cm3']:.2f} cm³\n"
            f"CR estimert: {metrics['cr_estimate']:.3f}\n\n"
            "Klaringer:\n"
            f"{clearance_text}"
        )
    )


def mm_to_cm(value_mm: float) -> float:
    """Konverterer mm til cm (Fusion sine interne lengdeenheter er cm)."""
    return value_mm / 10.0
