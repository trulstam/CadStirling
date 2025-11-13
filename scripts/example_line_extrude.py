# ID: codex_fusionapi_v1.0
name: Codex×Fusion360
id: codex_fusionapi_v1.0
version: 1.0.0
owner: Truls Tambs-Lyche


description: >
Codex×Fusion360: bruk alltid siste Fusion360 API (Python/C++). Kode/dokumentasjon skal samsvare
med oppdatert objektmodell/navnerom/metodestruktur. Sjekk syntaks mot offisielle kilder.
Alle prompter og svar skal inneholde en unik ID-tag (codex_fusionapi_vX.Y/hash) for sporbarhet
mellom Codex og denne chatten.


references:
- API Manual: https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-7B5A90C8-E94C-48DA-B16B-430729B734DC
- Basic Concepts: https://help.autodesk.com/cloudhelp/ENU/Fusion-360-API/files/BasicConcepts_UM.htm
- Dev Portal: https://aps.autodesk.com/developer/overview/autodesk-fusion-api
- GitHub Samples: https://github.com/AutodeskFusion360
- Forum: https://forums.autodesk.com/t5/fusion-360-api-and-scripts/bd-p/1229
- Add-ins Guide: https://help.autodesk.com/view/fusion360/ENU/?guid=GUID-C1545D80-D804-4CF3-886D-9B5C54B2D7A2


policy:
enforce_latest_api: true
require_id_in_prompts: true
require_id_in_code: true
reject_outdated_calls: true