# dbos-mcp

MCP server for DBOS Conductor.

## Setup

```bash
uv sync
```

## Configuration

```bash
export DBOS_CONDUCTOR_URL="http://localhost:8090"
export DBOS_CONDUCTOR_TOKEN="your-token"
export DBOS_CONDUCTOR_ORG_ID="default_id"
```

## Run

```bash
uv run dbos-mcp
```

## Claude Code

```bash
claude mcp add dbos-conductor -- uv run --directory /path/to/dbos-mcp dbos-mcp
```

## Tools

- `list_applications` - List all applications
- `list_workflows` - List/filter workflows
- `get_workflow` - Get workflow details
