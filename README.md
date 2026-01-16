# DBOS MCP Server

MCP server for DBOS Conductor workflow introspection and management.

## Installation

```bash
claude mcp add dbos-conductor -- uvx dbos-mcp
```

Then start Claude Code and ask it questions about your DBOS apps!
Claude will prompt you to log in by clicking the URL it offers and authenticating in the browser.

Credentials are stored in `~/.dbos-mcp/credentials`.

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
