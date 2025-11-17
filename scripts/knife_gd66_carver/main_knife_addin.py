# ID: codex_fusionapi_v1.1
"""Stub for GD66-baserte carver-knivens geometri, vil senere generere Fusion 360-modell."""
import adsk.core
import adsk.fusion
import traceback  # noqa: F401  # for fremtidig bruk ved utvidelser

_COMPLIANCE_BANNER = "COMPLIANCE BANNER :: ID codex_fusionapi_v1.1 :: knife_gd66_carver"


def run(context: str) -> None:
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    print(_COMPLIANCE_BANNER)
    if ui:
        ui.messageBox(
            "Stub: GD66 knivskriptet er riktig koblet opp, men ikke implementert ennå."
        )


def stop(context: str) -> None:
    print(f"Stopper skript :: {_COMPLIANCE_BANNER}")
