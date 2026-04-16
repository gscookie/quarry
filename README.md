# quarry

An MCP server for tracking open questions, commitments, and threads across sessions.

Rocks are the unit of work: anything worth carrying that shouldn't fall through the cracks — an open architectural question, a commitment made in a session, a research thread spanning multiple conversations. Rocks are hierarchical, have horizons, and are resolved rather than deleted.

---

## Requirements

- Python 3.11+

---

## Installation

```bash
uv tool install git+https://github.com/gscookie/quarry
```

Or from a local clone:

```bash
uv tool install /path/to/quarry
```

---

## Configuration

### Claude Code

Add to `~/.claude/settings.json`:

```json
{
  "mcpServers": {
    "quarry": {
      "command": "quarry"
    }
  }
}
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "quarry": {
      "command": "quarry"
    }
  }
}
```

---

## Tools

| Tool | Description |
|------|-------------|
| `rock_add(title, body, ...)` | Record a new rock. |
| `rock_list(status?, horizon?, tags?, carried_by?, roots_only?)` | List rocks with optional filters. Returns newest first. |
| `rock_read(rock_id)` | Fetch a single rock by ID. |
| `rock_children(rock_id)` | List direct children of a rock. |
| `rock_tree(rock_id)` | Fetch a rock and its full descendant tree. |
| `rock_update(rock_id, ...)` | Update fields on an active rock. |
| `rock_resolve(rock_id, resolution, spawns?)` | Mark a rock resolved. Optionally spawn new rocks from the resolution. |
| `rock_drop(rock_id)` | Permanently delete a rock. |

### `rock_add` fields

| Field | Description |
|-------|-------------|
| `title` | Short name (one line). |
| `body` | Fuller description of what's being carried and why. |
| `horizon` | Natural timescale: `session`, `week`, `month` (default), or `long`. |
| `parent_id` | Parent rock ID for structural grouping. |
| `spawned_by` | ID of the rock whose resolution generated this one (lineage tracking). |
| `carried_by` | Agents actively responsible for tracking and moving this rock. |
| `witnesses` | Agents who know about the rock but aren't carrying it. |
| `tags` | Optional labels. |
| `provenance` | Free-text source context (paper, session, exchange, etc.). |

---

## Storage

Rocks are stored in SQLite at `~/.quarry/quarry.db`. Override with the `QUARRY_DB` environment variable.

Resolved rocks are retained with their resolution text. Use `rock_drop` only for permanent deletion.

---

## License

CC0-1.0
