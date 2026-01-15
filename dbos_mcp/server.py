"""DBOS Conductor MCP Server."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from dbos_mcp import client

mcp = FastMCP(
    name="dbos-conductor",
    instructions="MCP server for DBOS Conductor workflow introspection and management. Call login first if not authenticated.",
)


@mcp.tool()
async def login() -> dict[str, Any]:
    """Start DBOS Cloud login flow.

    Returns a URL that the user must open in their browser to authenticate.
    After authenticating, call login_complete to finish the login process.

    Returns:
        Dictionary with url to visit and instructions.
    """
    return await client.login()


@mcp.tool()
async def login_complete() -> dict[str, Any]:
    """Complete DBOS Cloud login after authenticating in browser.

    Call this after you have opened the login URL and authenticated.

    Returns:
        Dictionary with userName and organization on success.
    """
    result = await client.login_complete()
    return {
        "message": f"Successfully logged in as {result['userName']}",
        "userName": result["userName"],
        "organization": result["organization"],
    }


@mcp.tool()
async def list_applications() -> dict[str, Any]:
    """List all applications registered with DBOS Conductor.

    Returns:
        Dictionary containing list of applications with details:
        - application_id: Unique identifier
        - application_name: Name of the application
        - status: AVAILABLE or UNAVAILABLE
        - executor_timeout_secs: Executor timeout setting
    """
    applications = await client.list_applications()
    return {
        "applications": applications,
        "count": len(applications),
    }


@mcp.tool()
async def list_workflows(
    application_name: str,
    status: str | None = None,
    workflow_name: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort_desc: bool | None = None,
    load_input: bool | None = None,
    load_output: bool | None = None,
) -> dict[str, Any]:
    """List workflows from DBOS Conductor with optional filters.

    Args:
        application_name: Name of the DBOS application
        status: Filter by workflow status (PENDING, RUNNING, SUCCESS, FAILURE, CANCELLED, ENQUEUED)
        workflow_name: Filter by workflow name
        start_time: Filter by start time (ISO 8601 format)
        end_time: Filter by end time (ISO 8601 format)
        limit: Maximum number of workflows to return
        offset: Offset for pagination
        sort_desc: Sort in descending order by creation time
        load_input: Include workflow input in response
        load_output: Include workflow output in response

    Returns:
        Dictionary containing list of workflows and metadata
    """
    workflows = await client.list_workflows(
        application_name=application_name,
        status=status,
        workflow_name=workflow_name,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
        sort_desc=sort_desc,
        load_input=load_input,
        load_output=load_output,
    )

    return {
        "workflows": workflows,
        "count": len(workflows),
        "application": application_name,
    }


@mcp.tool()
async def get_workflow(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Get details of a specific workflow from DBOS Conductor.

    Args:
        application_name: Name of the DBOS application
        workflow_id: UUID of the workflow to retrieve

    Returns:
        Dictionary containing workflow details including:
        - WorkflowUUID: Unique identifier
        - Status: Current status (PENDING, RUNNING, SUCCESS, FAILURE, CANCELLED, ENQUEUED)
        - WorkflowName: Name of the workflow function
        - Input/Output: Workflow input and output data
        - CreatedAt/UpdatedAt: Timestamps
        - Error: Error message if failed
    """
    return await client.get_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
    )


def main():
    mcp.run()


if __name__ == "__main__":
    main()
