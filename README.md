# DBOS MCP Server

This repository contains a Model Context Protocol (MCP) server with tools that can analyze and manage your DBOS workflows.
It enables LLMs to retrieve information on your applications' workflows and steps, for example to help you debug issues in development or production.
To use this server, your application should be connected to [Conductor](https://docs.dbos.dev/production/conductor).

You may want to use this alongside a DBOS prompt ([Python](https://docs.dbos.dev/python/prompting), [TypeScript](https://docs.dbos.dev/typescript/prompting), [Go](https://docs.dbos.dev/golang/prompting), [Java](https://docs.dbos.dev/java/prompting)) so your model has the most up-to-date information on DBOS.

## Setup

### Install `uv`

Before using this MCP server, you must install `uv`.
For installation instructions, see the [`uv` installation docs](https://docs.astral.sh/uv/getting-started/installation/).

### Setup with Claude Code

To use this MCP server with Claude Code, first install it:

```bash
claude mcp add dbos-conductor -- uvx dbos-mcp
```

Then start Claude Code and ask it questions about your DBOS apps!
Claude will prompt you to log in by clicking the URL it offers and authenticating in the browser.

Credentials are stored in `~/.dbos-mcp/credentials`.

## Tools

#### Application Introspection
- `list_applications` - List all applications
- `list_executors` - List connected executors for an application

#### Workflow Introspection
- `list_workflows` - List/filter workflows
- `get_workflow` - Get workflow details
- `list_steps` - Get execution steps for a workflow

#### Workflow Management
- `cancel_workflow` - Cancel a running workflow
- `resume_workflow` - Resume a pending or failed workflow
- `fork_workflow` - Fork a workflow from a specific step

#### Authentication
- `login` - Start login flow (returns URL to login page)
- `login_complete` - Complete login after authenticating