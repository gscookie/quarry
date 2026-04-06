from __future__ import annotations

import json
from typing import Annotated, Any

import fastmcp
from pydantic import BeforeValidator

from . import store


def _coerce_str_list(v: Any) -> list[str] | None:
    if v is None:
        return None
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
        except (json.JSONDecodeError, ValueError):
            pass
    return v


def _coerce_dict_list(v: Any) -> list[dict] | None:
    if v is None:
        return None
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            parsed = json.loads(v)
            if isinstance(parsed, list):
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
    return v


OptStrList = Annotated[list[str] | None, BeforeValidator(_coerce_str_list)]
OptDictList = Annotated[list[dict] | None, BeforeValidator(_coerce_dict_list)]

mcp = fastmcp.FastMCP(
    name="Quarry",
    instructions=(
        "Rock tracker for open questions, commitments, and threads carried across sessions. "
        "Rocks are hierarchical: any rock can have children (sub-questions). "
        "Use rock_add to record something worth carrying. "
        "Use rock_list to see active rocks (optionally filtered by horizon, carried_by, parent). "
        "Use rock_children or rock_tree to navigate structure. "
        "Use rock_resolve when something closes — optionally spawning new rocks from the resolution."
    ),
)


@mcp.tool()
def rock_add(
    title: str,
    body: str,
    tags: OptStrList = None,
    parent_id: str | None = None,
    spawned_by: str | None = None,
    horizon: str = "month",
    carried_by: OptStrList = None,
    provenance: str | None = None,
) -> dict:
    """
    Add a new rock — an open question, commitment, or thread to carry across sessions.

    title: short name (one line).
    body: fuller description of what's being carried and why.
    tags: optional labels.
    parent_id: ID of parent rock (for structural grouping).
    spawned_by: ID of rock whose resolution opened this one (genealogical lineage).
    horizon: "session", "week", "month" (default), or "long".
    carried_by: list of agent names carrying this rock (e.g. ["epektasis", "wren"]).
    provenance: brief note on where this rock came from.

    Returns the created rock.
    """
    try:
        return store.create_rock(
            title=title,
            body=body,
            tags=tags or [],
            parent_id=parent_id,
            spawned_by=spawned_by,
            horizon=horizon,
            carried_by=carried_by or [],
            provenance=provenance,
        )
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool()
def rock_list(
    status: str | None = None,
    tags: OptStrList = None,
    roots_only: bool = False,
    horizon: str | None = None,
    carried_by: str | None = None,
) -> list[dict]:
    """
    List rocks, optionally filtered.

    status: "active", "resolved", or "suspended". Omit for all.
    tags: filter to rocks that have all the given tags.
    roots_only: if True, return only top-level rocks (no parent).
    horizon: filter by "session", "week", "month", or "long".
    carried_by: filter to rocks carried by a specific agent name.

    Returns rocks newest-first.
    """
    parent_id_filter = None if roots_only else "__unset__"
    return store.list_rocks(
        status=status,
        tags=tags,
        parent_id=parent_id_filter,
        horizon=horizon,
        carried_by=carried_by,
    )


@mcp.tool()
def rock_read(rock_id: str) -> dict | None:
    """
    Read a single rock by ID. Returns null if not found.
    """
    return store.get_rock(rock_id)


@mcp.tool()
def rock_children(rock_id: str) -> list[dict]:
    """
    Return the direct children of a rock (rocks with this rock as parent).
    """
    return store.get_children(rock_id)


@mcp.tool()
def rock_tree(rock_id: str) -> dict | None:
    """
    Return a rock and all its descendants as a nested tree.
    Each rock includes a "children" list containing its child rocks (recursively).
    Returns null if the root rock is not found.
    """
    return store.get_tree(rock_id)


@mcp.tool()
def rock_update(
    rock_id: str,
    title: str | None = None,
    body: str | None = None,
    tags: OptStrList = None,
    status: str | None = None,
    parent_id: str | None = None,
    horizon: str | None = None,
    carried_by: OptStrList = None,
    provenance: str | None = None,
) -> dict | None:
    """
    Update a rock's fields. Only provided fields are changed.

    status must be one of: active, resolved, suspended.
    horizon must be one of: session, week, month, long.
    To resolve with a resolution note and optionally spawn new rocks, prefer rock_resolve.

    Returns the updated rock, or null if not found.
    """
    try:
        return store.update_rock(
            rock_id,
            title=title,
            body=body,
            tags=tags,
            status=status,
            parent_id=parent_id,
            horizon=horizon,
            carried_by=carried_by,
            provenance=provenance,
        )
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool()
def rock_resolve(
    rock_id: str,
    resolution: str | None = None,
    spawns: OptDictList = None,
) -> dict:
    """
    Mark a rock as resolved, optionally spawning new rocks from the resolution.

    resolution: note on what closed it.
    spawns: list of rock specs to create as children of this resolution.
            Each spec is a dict with keys: title, body, tags, horizon, carried_by,
            provenance, parent_id (all optional except title and body).
            Each spawned rock will have spawned_by set to this rock's ID automatically.

    Returns: {rock: <resolved rock>, spawned: [<new rocks>]}
    """
    return store.resolve_rock(rock_id, resolution=resolution, spawns=spawns or [])


@mcp.tool()
def rock_drop(rock_id: str) -> dict:
    """
    Permanently delete a rock. Irreversible. Does not delete children.

    Returns {dropped: true} on success or {dropped: false} if not found.
    """
    return {"dropped": store.drop_rock(rock_id)}


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
