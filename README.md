# dbos-mcp

MCP server for DBOS Conductor.

## Setup

```bash
uv sync
```

## Run

```bash
uv run dbos-mcp
```

## Claude Code

```bash
claude mcp add dbos-conductor -- uv run --directory /path/to/dbos-mcp dbos-mcp
```

Then in Claude Code:
```
You: "Login to DBOS"
→ Returns a URL
→ You click the URL and authenticate in browser

You: "Complete the login"
→ "Successfully logged in as you@example.com"

You: "List my applications"
→ Works
```

## Tools

- `login` - Start login flow (returns URL to visit)
- `login_complete` - Complete login after authenticating
- `list_applications` - List all applications
- `list_workflows` - List/filter workflows
- `get_workflow` - Get workflow details
- `list_steps` - Get execution steps for a workflow
- `list_executors` - List connected executors for an application
- `cancel_workflow` - Cancel a running workflow
- `resume_workflow` - Resume a pending or failed workflow
- `fork_workflow` - Fork a workflow from a specific step

Credentials stored in `~/.dbos-mcp/credentials`.
