import json
from pathlib import Path

import path_resolver


def current_json_valid(project_root, params):
    path = params.get("path")
    target = _resolve_path(project_root, path, "Workspace/Current.json")
    display_path = path_resolver.to_aiworkflow_relative(_display_path(project_root, target))
    if not target.exists():
        return {
            "status": "fail",
            "message": f"{display_path} does not exist.",
            "details": {"path": display_path},
        }

    data = json.loads(target.read_text(encoding=params.get("encoding", "utf-8-sig")))
    required = [
        "schemaVersion",
        "topic",
        "topicPath",
        "issue",
        "issuePath",
        "decisionPath",
        "resolutionPath",
        "currentIteration",
        "iterationPath",
        "updatedAt",
        "source",
    ]
    missing = [key for key in required if key not in data]
    if missing:
        return {
            "status": "fail",
            "message": f"{display_path} missing fields: {', '.join(missing)}.",
            "details": {"missing": missing},
        }
    aiworkflow_root = _aiworkflow_root()
    for key in ["topicPath", "issuePath", "decisionPath", "resolutionPath", "iterationPath"]:
        ref = path_resolver.resolve_aiworkflow_path(aiworkflow_root, data[key])
        if not ref.exists():
            return {
                "status": "fail",
                "message": f"{display_path} references missing {key}: {data[key]}.",
                "details": {"key": key, "path": data[key]},
            }
    return {
        "status": "pass",
        "message": f"{display_path} is valid.",
        "details": {"path": display_path},
    }


def _resolve_path(project_root, path, default_relative_to_aiworkflow):
    if path:
        target = Path(path)
        return target if target.is_absolute() else path_resolver.resolve_project_path(project_root, target)
    return _aiworkflow_root() / default_relative_to_aiworkflow


def _aiworkflow_root():
    return Path(__file__).resolve().parents[4]


def _display_path(project_root, target):
    try:
        return target.relative_to(project_root).as_posix()
    except ValueError:
        return target.as_posix()
