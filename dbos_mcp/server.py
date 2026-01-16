"""DBOS Conductor MCP Server."""

from typing import Any

from mcp.server.fastmcp import FastMCP

from dbos_mcp import client

mcp = FastMCP(
    name="dbos-conductor",
    instructions="""MCP server for DBOS Conductor workflow introspection and management.

Call login first if not authenticated or if receiving auth-related errors.

IMPORTANT: Workflow operations (list_workflows, get_workflow, etc.) only work for applications with status "AVAILABLE". Use list_applications first to check application status.""",
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
        applications: Array of application objects, each containing:
            - application_id (string): Unique identifier
            - application_name (string): Name of the application
            - org_id (string): Organization ID
            - status (string): "AVAILABLE" or "UNAVAILABLE"
            - language (string, optional): Programming language of the application
            - gc_time_threshold_ms (int, optional): Garbage collection time threshold in milliseconds
            - gc_rows_threshold (int, optional): Garbage collection rows threshold (default 1000000)
            - global_timeout_ms (int, optional): Global workflow timeout in milliseconds
            - executor_timeout_secs (int): Seconds a disconnected executor can remain before being marked dead and having its workflows recovered (default 60)
        count: Number of applications returned
    """
    applications = await client.list_applications()
    return {
        "applications": applications,
        "count": len(applications),
    }


@mcp.tool()
async def list_workflows(
    application_name: str,
    workflow_uuids: list[str] | None = None,
    workflow_name: str | None = None,
    authenticated_user: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    status: str | None = None,
    application_version: str | None = None,
    forked_from: str | None = None,
    queue_name: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort_desc: bool | None = None,
    workflow_id_prefix: str | None = None,
    load_input: bool | None = None,
    load_output: bool | None = None,
    executor_id: str | None = None,
    queues_only: bool | None = None,
) -> dict[str, Any]:
    """List workflows from DBOS Conductor with optional filters.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_uuids (array of strings, optional): Filter to only these specific workflow IDs
        workflow_name (string, optional): Filter by workflow function name
        authenticated_user (string, optional): Filter by the user who started the workflow
        start_time (string, optional): Filter workflows created after this time (ISO 8601)
        end_time (string, optional): Filter workflows created before this time (ISO 8601)
        status (string, optional): Filter by status - PENDING, SUCCESS, ERROR, CANCELLED, ENQUEUED, or MAX_RECOVERY_ATTEMPTS_EXCEEDED
        application_version (string, optional): Filter by application version
        forked_from (string, optional): Filter to workflows forked from this workflow ID
        queue_name (string, optional): Filter by workflow queue name
        limit (int, optional): Maximum number of workflows to return
        offset (int, optional): Number of workflows to skip (for pagination)
        sort_desc (bool, optional): Sort by creation time descending (default: false, ascending)
        workflow_id_prefix (string, optional): Filter to workflow IDs starting with this prefix
        load_input (bool, optional): Include workflow input data in response (default: false)
        load_output (bool, optional): Include workflow output data in response (default: false)
        executor_id (string, optional): Filter by executor ID running the workflow
        queues_only (bool, optional): Only return workflows that are on a queue (default: false)

    Returns:
        workflows: Array of workflow objects, each containing:
            - WorkflowUUID (string): The workflow ID
            - Status (string): PENDING, SUCCESS, ERROR, CANCELLED, ENQUEUED, or MAX_RECOVERY_ATTEMPTS_EXCEEDED
            - WorkflowName (string): The name of the workflow function
            - WorkflowClassName (string, optional): The name of the workflow's class, if any
            - WorkflowConfigName (string, optional): The name with which the workflow's class instance was configured, if any
            - AuthenticatedUser (string, optional): The user who ran the workflow, if specified
            - AssumedRole (string, optional): The role with which the workflow ran, if specified
            - AuthenticatedRoles (string, optional): All roles which the authenticated user could assume (JSON array)
            - Input (string, optional): The workflow input (JSON string, only if load_input=true)
            - Output (string, optional): The workflow's output, if any (JSON string, only if load_output=true)
            - Error (string, optional): The error the workflow threw, if any
            - CreatedAt (string): Workflow start time as Unix epoch milliseconds
            - UpdatedAt (string): Last time the workflow status was updated as Unix epoch milliseconds
            - QueueName (string, optional): If this workflow was enqueued, on which queue
            - ApplicationVersion (string): The application version on which this workflow was started
            - ExecutorID (string, optional): The executor to most recently execute this workflow
            - WorkflowTimeoutMS (string, optional): The start-to-close timeout of the workflow in ms
            - WorkflowDeadlineEpochMS (string, optional): The deadline of the workflow, computed by adding its timeout to its start time (epoch ms)
            - DeduplicationID (string, optional): Unique ID for deduplication on a queue
            - Priority (string, optional): Priority of the workflow on the queue (1-2147483647, lower is higher priority)
            - QueuePartitionKey (string, optional): If this workflow is enqueued on a partitioned queue, its partition key
            - ForkedFrom (string, optional): If this workflow was forked from another, that workflow's ID
        count (int): Number of workflows returned
        application (string): Name of the application queried
    """
    workflows = await client.list_workflows(
        application_name=application_name,
        workflow_uuids=workflow_uuids,
        workflow_name=workflow_name,
        authenticated_user=authenticated_user,
        start_time=start_time,
        end_time=end_time,
        status=status,
        application_version=application_version,
        forked_from=forked_from,
        queue_name=queue_name,
        limit=limit,
        offset=offset,
        sort_desc=sort_desc,
        workflow_id_prefix=workflow_id_prefix,
        load_input=load_input,
        load_output=load_output,
        executor_id=executor_id,
        queues_only=queues_only,
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
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): UUID of the workflow to retrieve

    Returns:
        WorkflowUUID (string): The workflow ID
        Status (string): PENDING, SUCCESS, ERROR, CANCELLED, ENQUEUED, or MAX_RECOVERY_ATTEMPTS_EXCEEDED
        WorkflowName (string): The name of the workflow function
        WorkflowClassName (string, optional): The name of the workflow's class, if any
        WorkflowConfigName (string, optional): The name with which the workflow's class instance was configured, if any
        AuthenticatedUser (string, optional): The user who ran the workflow, if specified
        AssumedRole (string, optional): The role with which the workflow ran, if specified
        AuthenticatedRoles (string, optional): All roles which the authenticated user could assume (JSON array)
        Input (string, optional): The workflow input (JSON string)
        Output (string, optional): The workflow's output, if any (JSON string)
        Error (string, optional): The error the workflow threw, if any
        CreatedAt (string): Workflow start time as Unix epoch milliseconds
        UpdatedAt (string): Last time the workflow status was updated as Unix epoch milliseconds
        QueueName (string, optional): If this workflow was enqueued, on which queue
        ApplicationVersion (string): The application version on which this workflow was started
        ExecutorID (string, optional): The executor to most recently execute this workflow
        WorkflowTimeoutMS (string, optional): The start-to-close timeout of the workflow in ms
        WorkflowDeadlineEpochMS (string, optional): The deadline of the workflow, computed by adding its timeout to its start time (epoch ms)
        DeduplicationID (string, optional): Unique ID for deduplication on a queue
        Priority (string, optional): Priority of the workflow on the queue (1-2147483647, lower is higher priority)
        QueuePartitionKey (string, optional): If this workflow is enqueued on a partitioned queue, its partition key
        ForkedFrom (string, optional): If this workflow was forked from another, that workflow's ID
    """
    return await client.get_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
    )


@mcp.tool()
async def list_steps(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Get execution steps for a workflow from DBOS Conductor.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): UUID of the workflow

    Returns:
        steps: Array of step objects, each containing:
            - function_id (int): The unique ID of the step in the workflow
            - function_name (string): The name of the step
            - output (string, optional): The step's output, if any
            - error (string, optional): The error the step threw, if any
            - child_workflow_id (string, optional): If the step starts or retrieves the result of a workflow, its ID
            - started_at_epoch_ms (string, optional): The Unix epoch timestamp at which this step started
            - completed_at_epoch_ms (string, optional): The Unix epoch timestamp at which this step completed
        count (int): Number of steps returned
        workflow_id (string): The workflow ID queried
    """
    steps = await client.list_steps(
        application_name=application_name,
        workflow_id=workflow_id,
    )
    return {
        "steps": steps,
        "count": len(steps),
        "workflow_id": workflow_id,
    }


@mcp.tool()
async def list_executors(
    application_name: str,
) -> dict[str, Any]:
    """List executors for an application from DBOS Conductor.

    Executors are running instances of your application connected to Conductor.

    Args:
        application_name (string, required): Name of the DBOS application

    Returns:
        executors: Array of executor objects, each containing:
            - executor_id (string): Unique identifier for this executor
            - application_id (string): The application ID
            - application_version (string): Version of the application running on this executor
            - status (string): HEALTHY, DISCONNECTED, or DEAD
            - hostname (string, optional): Hostname of the executor
            - created_at (string): When the executor connected (Unix epoch milliseconds)
            - updated_at (string): Last heartbeat time (Unix epoch milliseconds)
            - language (string, optional): Programming language (e.g., "python", "typescript")
            - dbos_version (string, optional): Version of the DBOS library
        count (int): Number of executors returned
        application (string): Name of the application queried
    """
    executors = await client.list_executors(application_name=application_name)
    return {
        "executors": executors,
        "count": len(executors),
        "application": application_name,
    }


@mcp.tool()
async def cancel_workflow(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Cancel a running workflow.

    Sets the workflow status to CANCELLED. The workflow will stop executing
    at the next step boundary.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): UUID of the workflow to cancel

    Returns:
        message (string): Confirmation message
        workflow_id (string): The cancelled workflow ID
    """
    await client.cancel_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
    )
    return {
        "message": "Workflow cancelled",
        "workflow_id": workflow_id,
    }


@mcp.tool()
async def resume_workflow(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Resume a workflow.

    Resumes execution of a workflow that is in CANCELLED state.
    You can also use this on a workflow in the ENQUEUED state to immediately start it, bypassing its queue.
    You cannot resume a workflow in any other state.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): UUID of the workflow to resume

    Returns:
        message (string): Confirmation message
        workflow_id (string): The resumed workflow ID
    """
    await client.resume_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
    )
    return {
        "message": "Workflow resumed",
        "workflow_id": workflow_id,
    }


@mcp.tool()
async def fork_workflow(
    application_name: str,
    workflow_id: str,
    start_step: int,
    application_version: str | None = None,
    new_workflow_id: str | None = None,
) -> dict[str, Any]:
    """Fork a workflow from a specific step.

    Creates a new workflow that starts from a specific step of an existing workflow,
    reusing the recorded outputs of all prior steps. Useful for debugging, testing
    fixes, or replaying workflows from a specific point.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): UUID of the workflow to fork from
        start_step (int, required): The step number to start from (use list_steps to find step IDs)
        application_version (string, optional): Application version for the new workflow (defaults to current version)
        new_workflow_id (string, optional): Custom UUID for the new workflow (auto-generated if not specified)

    Returns:
        workflow_id (string): The UUID of the newly created forked workflow
        forked_from (string): The UUID of the original workflow
        start_step (int): The step number the fork starts from
    """
    result = await client.fork_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
        start_step=start_step,
        application_version=application_version,
        new_workflow_id=new_workflow_id,
    )
    return {
        "workflow_id": result.get("workflow_id"),
        "forked_from": workflow_id,
        "start_step": start_step,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
