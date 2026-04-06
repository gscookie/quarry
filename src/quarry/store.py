from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path


QUARRY_DIR = Path.home() / ".synthetic-see" / "quarry"

VALID_STATUSES = {"active", "resolved", "suspended"}
VALID_HORIZONS = {"session", "week", "month", "long"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _quarry_dir() -> Path:
    QUARRY_DIR.mkdir(parents=True, exist_ok=True)
    return QUARRY_DIR


def _rock_path(rock_id: str) -> Path:
    return _quarry_dir() / f"{rock_id}.json"


def _read_rock(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _all_rocks() -> list[dict]:
    rocks = []
    for path in sorted(_quarry_dir().glob("*.json")):
        rock = _read_rock(path)
        if rock is not None:
            rocks.append(rock)
    return rocks


def create_rock(
    title: str,
    body: str,
    tags: list[str],
    parent_id: str | None = None,
    spawned_by: str | None = None,
    horizon: str = "month",
    carried_by: list[str] | None = None,
    provenance: str | None = None,
) -> dict:
    if horizon not in VALID_HORIZONS:
        raise ValueError(f"horizon must be one of {VALID_HORIZONS}")
    rock_id = str(uuid.uuid4())
    now = _now()
    rock = {
        "id": rock_id,
        "title": title,
        "body": body,
        "status": "active",
        "tags": tags,
        "parent_id": parent_id,
        "spawned_by": spawned_by,
        "horizon": horizon,
        "carried_by": carried_by or [],
        "provenance": provenance,
        "created_at": now,
        "updated_at": now,
        "resolved_at": None,
        "resolution": None,
    }
    _rock_path(rock_id).write_text(json.dumps(rock, indent=2))
    return rock


def get_rock(rock_id: str) -> dict | None:
    path = _rock_path(rock_id)
    if not path.exists():
        return None
    return _read_rock(path)


def list_rocks(
    status: str | None = None,
    tags: list[str] | None = None,
    parent_id: str | None = "__unset__",  # sentinel: unset means no filter
    horizon: str | None = None,
    carried_by: str | None = None,
) -> list[dict]:
    rocks = _all_rocks()
    result = []
    for rock in rocks:
        if status and rock.get("status") != status:
            continue
        if tags:
            rock_tags = set(rock.get("tags", []))
            if not all(t in rock_tags for t in tags):
                continue
        if parent_id != "__unset__":
            if rock.get("parent_id") != parent_id:
                continue
        if horizon and rock.get("horizon") != horizon:
            continue
        if carried_by and carried_by not in rock.get("carried_by", []):
            continue
        result.append(rock)
    result.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return result


def get_children(rock_id: str) -> list[dict]:
    """Return direct children of a rock (rocks with parent_id == rock_id)."""
    rocks = _all_rocks()
    children = [r for r in rocks if r.get("parent_id") == rock_id]
    children.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return children


def get_tree(rock_id: str) -> dict | None:
    """Return a rock and all its descendants as a nested tree."""
    rock = get_rock(rock_id)
    if rock is None:
        return None
    children = get_children(rock_id)
    rock["children"] = [get_tree(c["id"]) for c in children]
    return rock


def update_rock(
    rock_id: str,
    title: str | None = None,
    body: str | None = None,
    tags: list[str] | None = None,
    status: str | None = None,
    parent_id: str | None = None,
    horizon: str | None = None,
    carried_by: list[str] | None = None,
    provenance: str | None = None,
) -> dict | None:
    rock = get_rock(rock_id)
    if rock is None:
        return None
    if status and status not in VALID_STATUSES:
        raise ValueError(f"status must be one of {VALID_STATUSES}")
    if horizon and horizon not in VALID_HORIZONS:
        raise ValueError(f"horizon must be one of {VALID_HORIZONS}")
    if title is not None:
        rock["title"] = title
    if body is not None:
        rock["body"] = body
    if tags is not None:
        rock["tags"] = tags
    if status is not None:
        rock["status"] = status
    if parent_id is not None:
        rock["parent_id"] = parent_id
    if horizon is not None:
        rock["horizon"] = horizon
    if carried_by is not None:
        rock["carried_by"] = carried_by
    if provenance is not None:
        rock["provenance"] = provenance
    rock["updated_at"] = _now()
    _rock_path(rock_id).write_text(json.dumps(rock, indent=2))
    return rock


def resolve_rock(
    rock_id: str,
    resolution: str | None = None,
    spawns: list[dict] | None = None,
) -> dict:
    """
    Resolve a rock. Optionally spawn new rocks from it.

    spawns: list of dicts with keys matching rock_add parameters.
            Each spawned rock will have spawned_by set to rock_id.
    Returns: {rock: <resolved rock>, spawned: [<new rocks>]}
    """
    rock = get_rock(rock_id)
    if rock is None:
        return {"error": f"Rock {rock_id} not found"}
    now = _now()
    rock["status"] = "resolved"
    rock["resolved_at"] = now
    rock["updated_at"] = now
    rock["resolution"] = resolution
    _rock_path(rock_id).write_text(json.dumps(rock, indent=2))

    spawned = []
    for spec in (spawns or []):
        new_rock = create_rock(
            title=spec.get("title", ""),
            body=spec.get("body", ""),
            tags=spec.get("tags", []),
            parent_id=spec.get("parent_id"),
            spawned_by=rock_id,
            horizon=spec.get("horizon", "month"),
            carried_by=spec.get("carried_by", []),
            provenance=spec.get("provenance"),
        )
        spawned.append(new_rock)

    return {"rock": rock, "spawned": spawned}


def drop_rock(rock_id: str) -> bool:
    path = _rock_path(rock_id)
    if not path.exists():
        return False
    path.unlink()
    return True
