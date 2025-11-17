# ID: codex_fusionapi_v1.1
"""Stub for Stirlingmotorens hovedkomponenter, vil senere generere geometri i Fusion 360."""
import adsk.core
import adsk.fusion
import traceback  # noqa: F401  # for fremtidig bruk ved utvidelser

_COMPLIANCE_BANNER = "COMPLIANCE BANNER :: ID codex_fusionapi_v1.1 :: stirling_core"


def run(context: str) -> None:
    app = adsk.core.Application.get()
    ui = app.userInterface if app else None
    print(_COMPLIANCE_BANNER)
    if ui:
        ui.messageBox(
            "Stub: Stirlingmotor-skriptet er riktig koblet opp, men ikke implementert ennå."
        )


def stop(context: str) -> None:
    print(f"Stopper skript :: {_COMPLIANCE_BANNER}")
