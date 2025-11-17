# ID: codex_fusionapi_v1.7

"""Eksempel: tegner en linje og ekstruderer profilen i Fusion 360.

Skriptet viser hvordan man bruker Fusion 360 APIet til å:
1. Opprette (eller bruke aktivt) design.
2. Lage en skisse med en linje i XY-planet.
3. Ekstrudere linjeprofilen til et solid.

Ved kjøring spør skriptet etter ønsket linjelengde og ekstruderingshøyde.
"""

import adsk.core
import adsk.fusion
import traceback

ID_TAG = "codex_fusionapi_v1.7"
_COMPLIANCE_BANNER = f"COMPLIANCE BANNER :: ID {ID_TAG} :: example_line_extrude"
_handlers = []  # Holder referanser dersom vi utvider med hendelser senere.


def _ensure_design(app: adsk.core.Application) -> adsk.fusion.Design:
    """Returnerer aktivt design, eller lager et nytt hvis ingen er aktive."""
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    if design:
        return design

    documents = app.documents
    new_doc = documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    return adsk.fusion.Design.cast(new_doc.products.item(0))


def _prompt_for_value(ui: adsk.core.UserInterface, prompt: str, default: str) -> str:
    """Henter tekstverdi via inputBox og håndterer avbrytelse."""
    value, is_canceled = ui.inputBox(prompt, "Parametere", default)
    if is_canceled:
        raise RuntimeError("Brukeren avbrøt parameterdialogen.")
    return value


def _create_line_and_extrude(design: adsk.fusion.Design, line_len_expr: str, extrude_height_expr: str) -> None:
    units_mgr = design.unitsManager
    line_len_cm = units_mgr.evaluateExpression(line_len_expr, "cm")
    extrude_height = adsk.core.ValueInput.createByString(extrude_height_expr)

    root = design.rootComponent
    sketches = root.sketches
    xy_plane = root.xYConstructionPlane

    sketch = sketches.add(xy_plane)
    lines = sketch.sketchCurves.sketchLines
    start_point = adsk.core.Point3D.create(0, 0, 0)
    end_point = adsk.core.Point3D.create(line_len_cm, 0, 0)
    lines.addByTwoPoints(start_point, end_point)

    profile = sketch.profiles.item(0)
    extrudes = root.features.extrudeFeatures
    extrude_input = extrudes.createInput(profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    extrude_input.setDistanceExtent(False, extrude_height)
    extrudes.add(extrude_input)


def run(context: str) -> None:
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None

    print(_COMPLIANCE_BANNER)

    try:
        if not app or not ui:
            raise RuntimeError("Fusion 360-appen/UI er ikke tilgjengelig.")

        design = _ensure_design(app)

        line_len_expr = _prompt_for_value(ui, "Linjelengde (f.eks. 5 cm)", "5 cm")
        extrude_height_expr = _prompt_for_value(ui, "Ekstruderingshøyde (f.eks. 2 cm)", "2 cm")

        _create_line_and_extrude(design, line_len_expr, extrude_height_expr)

        ui.messageBox("Ekstrudert linje er opprettet.")
    except RuntimeError as run_error:
        if ui:
            ui.messageBox(f"Kjøringsfeil: {run_error}")
        else:
            print(f"Kjøringsfeil: {run_error}")
    except Exception:
        error_text = traceback.format_exc()
        if ui:
            ui.messageBox(f"Uventet feil:\n{error_text}")
        else:
            print(error_text)


def stop(context: str) -> None:
    print(f"Stopper skript :: {_COMPLIANCE_BANNER}")
