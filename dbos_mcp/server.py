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
            - private_mode (bool): If true, Conductor never loads application data such as workflow inputs/outputs or schedule contexts
            - dbos_cloud (bool): Whether the application was provisioned by DBOS Cloud
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
    workflow_name: str | list[str] | None = None,
    authenticated_user: str | list[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    completed_after: str | None = None,
    completed_before: str | None = None,
    dequeued_after: str | None = None,
    dequeued_before: str | None = None,
    status: str | list[str] | None = None,
    application_version: str | list[str] | None = None,
    forked_from: str | list[str] | None = None,
    parent_workflow_id: str | list[str] | None = None,
    queue_name: str | list[str] | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort_desc: bool | None = None,
    workflow_id_prefix: str | list[str] | None = None,
    load_input: bool | None = None,
    load_output: bool | None = None,
    executor_id: str | list[str] | None = None,
    queues_only: bool | None = None,
    was_forked_from: bool | None = None,
    has_parent: bool | None = None,
) -> dict[str, Any]:
    """List workflows from DBOS Conductor with optional filters.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_uuids (array of strings, optional): Filter to only these specific workflow IDs
        workflow_name (string or array of strings, optional): Filter by workflow function name
        authenticated_user (string or array of strings, optional): Filter by the user who started the workflow
        start_time (string, optional): Filter workflows created after this time (ISO 8601)
        end_time (string, optional): Filter workflows created before this time (ISO 8601)
        completed_after (string, optional): Filter workflows completed after this time (ISO 8601)
        completed_before (string, optional): Filter workflows completed before this time (ISO 8601)
        dequeued_after (string, optional): Filter workflows dequeued after this time (ISO 8601)
        dequeued_before (string, optional): Filter workflows dequeued before this time (ISO 8601)
        status (string or array of strings, optional): Filter by status - PENDING, SUCCESS, ERROR, CANCELLED, ENQUEUED, DELAYED, or MAX_RECOVERY_ATTEMPTS_EXCEEDED
        application_version (string or array of strings, optional): Filter by application version
        forked_from (string or array of strings, optional): Filter to workflows forked from this workflow ID
        parent_workflow_id (string or array of strings, optional): Filter to child workflows of this parent workflow ID
        queue_name (string or array of strings, optional): Filter by workflow queue name
        limit (int, optional): Maximum number of workflows to return
        offset (int, optional): Number of workflows to skip (for pagination)
        sort_desc (bool, optional): Sort by creation time descending (default: false, ascending)
        workflow_id_prefix (string or array of strings, optional): Filter to workflow IDs starting with this prefix
        load_input (bool, optional): Include workflow input data in response (default: false; always false for private-mode applications)
        load_output (bool, optional): Include workflow output data in response (default: false; always false for private-mode applications)
        executor_id (string or array of strings, optional): Filter by executor ID running the workflow
        queues_only (bool, optional): Only return workflows that are on a queue (default: false)
        was_forked_from (bool, optional): If true, only return forked workflows. If false, only return non-forked workflows.
        has_parent (bool, optional): If true, only return child workflows. If false, only return workflows without a parent.

    Returns:
        workflows: Array of workflow objects, each containing:
            - WorkflowUUID (string): The workflow ID
            - Status (string): PENDING, SUCCESS, ERROR, CANCELLED, ENQUEUED, DELAYED, or MAX_RECOVERY_ATTEMPTS_EXCEEDED
            - WorkflowName (string): The name of the workflow function
            - WorkflowClassName (string, optional): The name of the workflow's class, if any
            - WorkflowConfigName (string, optional): The name with which the workflow's class instance was configured, if any
            - AuthenticatedUser (string, optional): The user who ran the workflow, if specified
            - AssumedRole (string, optional): The role with which the workflow ran, if specified
            - AuthenticatedRoles (string, optional): All roles which the authenticated user could assume (JSON array)
            - Input (string, optional): The workflow input, in a human-readable representation (only if load_input=true)
            - Output (string, optional): The workflow's output, if any, in a human-readable representation (only if load_output=true)
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
            - ParentWorkflowID (string, optional): If this is a child workflow, the ID of the parent workflow that started it
            - DequeuedAt (string, optional): When this workflow was dequeued from its queue (Unix epoch milliseconds)
            - WasForkedFrom (bool): Whether this workflow was forked from another workflow
            - DelayUntilEpochMS (string, optional): If this workflow has a delayed start, the epoch ms timestamp until which it is delayed
            - CompletedAt (string, optional): When this workflow completed (Unix epoch milliseconds)
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
        completed_after=completed_after,
        completed_before=completed_before,
        dequeued_after=dequeued_after,
        dequeued_before=dequeued_before,
        status=status,
        application_version=application_version,
        forked_from=forked_from,
        parent_workflow_id=parent_workflow_id,
        queue_name=queue_name,
        limit=limit,
        offset=offset,
        sort_desc=sort_desc,
        workflow_id_prefix=workflow_id_prefix,
        load_input=load_input,
        load_output=load_output,
        executor_id=executor_id,
        queues_only=queues_only,
        was_forked_from=was_forked_from,
        has_parent=has_parent,
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
        workflow_id (string, required): ID of the workflow to retrieve

    Returns:
        WorkflowUUID (string): The workflow ID
        Status (string): PENDING, SUCCESS, ERROR, CANCELLED, ENQUEUED, DELAYED, or MAX_RECOVERY_ATTEMPTS_EXCEEDED
        WorkflowName (string): The name of the workflow function
        WorkflowClassName (string, optional): The name of the workflow's class, if any
        WorkflowConfigName (string, optional): The name with which the workflow's class instance was configured, if any
        AuthenticatedUser (string, optional): The user who ran the workflow, if specified
        AssumedRole (string, optional): The role with which the workflow ran, if specified
        AuthenticatedRoles (string, optional): All roles which the authenticated user could assume (JSON array)
        Input (string, optional): The workflow input, in a human-readable representation
        Output (string, optional): The workflow's output, if any, in a human-readable representation
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
        ParentWorkflowID (string, optional): If this is a child workflow, the ID of the parent workflow that started it
        DequeuedAt (string, optional): When this workflow was dequeued from its queue (Unix epoch milliseconds)
        WasForkedFrom (bool): Whether this workflow was forked from another workflow
        DelayUntilEpochMS (string, optional): If this workflow has a delayed start, the epoch ms timestamp until which it is delayed
        CompletedAt (string, optional): When this workflow completed (Unix epoch milliseconds)
    """
    return await client.get_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
    )


@mcp.tool()
async def list_steps(
    application_name: str,
    workflow_id: str,
    limit: int | None = None,
    offset: int | None = None,
) -> dict[str, Any]:
    """Get execution steps for a workflow from DBOS Conductor.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): ID of the workflow
        limit (int, optional): Maximum number of steps to return
        offset (int, optional): Number of steps to skip (for pagination)

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
        limit=limit,
        offset=offset,
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
            - host_id (string, optional): Host identifier of the executor
            - hostname (string, optional): Hostname of the executor
            - created_at (string): When the executor connected (Unix epoch milliseconds)
            - updated_at (string): Last heartbeat time (Unix epoch milliseconds)
            - language (string, optional): Programming language (e.g., "python", "typescript")
            - dbos_version (string, optional): Version of the DBOS library
            - executor_metadata (object, optional): Arbitrary metadata reported by the executor
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
    cancel_children: bool = False,
) -> dict[str, Any]:
    """Cancel a running workflow.

    Sets the workflow status to CANCELLED. The workflow will stop executing
    at the next step boundary.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): ID of the workflow to cancel
        cancel_children (bool, optional): Also cancel child workflows started by this workflow (default: false)

    Returns:
        message (string): Confirmation message
        workflow_id (string): The cancelled workflow ID
    """
    await client.cancel_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
        cancel_children=cancel_children,
    )
    return {
        "message": "Workflow cancelled",
        "workflow_id": workflow_id,
    }


@mcp.tool()
async def resume_workflow(
    application_name: str,
    workflow_id: str,
    queue_name: str | None = None,
) -> dict[str, Any]:
    """Resume a workflow.

    Resumes execution of a workflow that is in CANCELLED state.
    You can also use this on a workflow in the ENQUEUED state to immediately start it, bypassing its queue.
    You cannot resume a workflow in any other state.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): ID of the workflow to resume
        queue_name (string, optional): If provided, enqueue the resumed workflow onto this queue instead of running it immediately

    Returns:
        message (string): Confirmation message
        workflow_id (string): The resumed workflow ID
    """
    await client.resume_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
        queue_name=queue_name,
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
    queue_name: str | None = None,
    queue_partition_key: str | None = None,
) -> dict[str, Any]:
    """Fork a workflow from a specific step.

    Creates a new workflow that starts from a specific step of an existing workflow,
    reusing the recorded outputs of all prior steps. Useful for debugging, testing
    fixes, or replaying workflows from a specific point.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): ID of the workflow to fork from
        start_step (int, required): The step number to start from (use list_steps to find step IDs)
        application_version (string, optional): Application version for the new workflow (defaults to current version)
        new_workflow_id (string, optional): Custom ID for the new workflow (auto-generated if not specified)
        queue_name (string, optional): Enqueue the forked workflow onto this queue instead of running it immediately
        queue_partition_key (string, optional): Partition key for the queue

    Returns:
        workflow_id (string): The ID of the newly created forked workflow
        forked_from (string): The ID of the original workflow
        start_step (int): The step number the fork starts from
    """
    result = await client.fork_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
        start_step=start_step,
        application_version=application_version,
        new_workflow_id=new_workflow_id,
        queue_name=queue_name,
        queue_partition_key=queue_partition_key,
    )
    return {
        "workflow_id": result.get("workflow_id"),
        "forked_from": workflow_id,
        "start_step": start_step,
    }


@mcp.tool()
async def bulk_cancel_workflows(
    application_name: str,
    workflow_ids: list[str],
    cancel_children: bool = False,
) -> dict[str, Any]:
    """Cancel multiple workflows at once.

    Sets each workflow's status to CANCELLED. Each workflow will stop executing
    at its next step boundary.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_ids (array of strings, required): IDs of the workflows to cancel
        cancel_children (bool, optional): Also cancel child workflows started by these workflows (default: false)

    Returns:
        message (string): Confirmation message
        count (int): Number of workflows cancelled
    """
    await client.bulk_cancel_workflows(
        application_name=application_name,
        workflow_ids=workflow_ids,
        cancel_children=cancel_children,
    )
    return {
        "message": f"Cancelled {len(workflow_ids)} workflows",
        "count": len(workflow_ids),
    }


@mcp.tool()
async def bulk_resume_workflows(
    application_name: str,
    workflow_ids: list[str],
    queue_name: str | None = None,
) -> dict[str, Any]:
    """Resume multiple workflows at once.

    Resumes execution of workflows that are in CANCELLED state.
    You can also use this on workflows in ENQUEUED state to immediately start them, bypassing their queue.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_ids (array of strings, required): IDs of the workflows to resume
        queue_name (string, optional): If provided, enqueue the resumed workflows onto this queue instead of running them immediately

    Returns:
        message (string): Confirmation message
        count (int): Number of workflows resumed
    """
    await client.bulk_resume_workflows(
        application_name=application_name,
        workflow_ids=workflow_ids,
        queue_name=queue_name,
    )
    return {
        "message": f"Resumed {len(workflow_ids)} workflows",
        "count": len(workflow_ids),
    }


@mcp.tool()
async def bulk_delete_workflows(
    application_name: str,
    workflow_ids: list[str],
    delete_children: bool = False,
) -> dict[str, Any]:
    """Delete multiple workflows at once.

    Permanently deletes the workflows and their execution history.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_ids (array of strings, required): IDs of the workflows to delete
        delete_children (bool, optional): Also delete child workflows started by these workflows (default: false)

    Returns:
        message (string): Confirmation message
        count (int): Number of workflows deleted
    """
    await client.bulk_delete_workflows(
        application_name=application_name,
        workflow_ids=workflow_ids,
        delete_children=delete_children,
    )
    return {
        "message": f"Deleted {len(workflow_ids)} workflows",
        "count": len(workflow_ids),
    }


@mcp.tool()
async def fork_from_failure(
    application_name: str,
    workflow_ids: list[str],
    application_version: str | None = None,
    queue_name: str | None = None,
    queue_partition_key: str | None = None,
    from_last_failure: bool = False,
    from_last_step: bool = False,
    from_step: int | None = None,
    from_step_name: str | None = None,
) -> dict[str, Any]:
    """Fork multiple failed workflows from a specific point.

    Creates new workflows that re-execute from a chosen point, reusing the
    recorded outputs of all prior steps. Useful for retrying a batch of failed
    workflows after deploying a fix.

    IMPORTANT: You must set exactly one of from_last_failure, from_last_step, from_step, or from_step_name.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_ids (array of strings, required): IDs of the workflows to fork
        application_version (string, optional): Application version for the new workflows (defaults to current version)
        queue_name (string, optional): Enqueue the forked workflows onto this queue
        queue_partition_key (string, optional): Partition key for the queue
        from_last_failure (bool, optional): Fork from the last failed step (default: false)
        from_last_step (bool, optional): Fork from the last executed step (default: false)
        from_step (int, optional): Fork from this specific step number
        from_step_name (string, optional): Fork from the step with this function name

    Returns:
        workflow_ids (array of strings): IDs of the newly created forked workflows
        count (int): Number of workflows forked
    """
    new_ids = await client.fork_from_failure(
        application_name=application_name,
        workflow_ids=workflow_ids,
        application_version=application_version,
        queue_name=queue_name,
        queue_partition_key=queue_partition_key,
        from_last_failure=from_last_failure,
        from_last_step=from_last_step,
        from_step=from_step,
        from_step_name=from_step_name,
    )
    return {
        "workflow_ids": new_ids,
        "count": len(new_ids),
    }


@mcp.tool()
async def delete_workflow(
    application_name: str,
    workflow_id: str,
    delete_children: bool = False,
) -> dict[str, Any]:
    """Delete a workflow from DBOS Conductor.

    Permanently deletes a workflow and its execution history.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): ID of the workflow to delete
        delete_children (bool, optional): Also delete child workflows started by this workflow (default: false)

    Returns:
        message (string): Confirmation message
        workflow_id (string): The deleted workflow ID
    """
    await client.delete_workflow(
        application_name=application_name,
        workflow_id=workflow_id,
        delete_children=delete_children,
    )
    return {
        "message": "Workflow deleted",
        "workflow_id": workflow_id,
    }


@mcp.tool()
async def get_workflow_aggregates(
    application_name: str,
    group_by_status: bool = False,
    group_by_name: bool = False,
    group_by_queue_name: bool = False,
    group_by_executor_id: bool = False,
    group_by_application_version: bool = False,
    select_count: bool = False,
    select_min_created_at: bool = False,
    select_max_queue_wait_ms: bool = False,
    select_max_total_latency_ms: bool = False,
    status: list[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    completed_after: str | None = None,
    completed_before: str | None = None,
    dequeued_after: str | None = None,
    dequeued_before: str | None = None,
    name: list[str] | None = None,
    app_version: list[str] | None = None,
    executor_id: list[str] | None = None,
    queue_name: list[str] | None = None,
    workflow_id_prefix: list[str] | None = None,
    time_bucket_size_ms: int | None = None,
) -> dict[str, Any]:
    """Get workflow aggregate metrics from DBOS Conductor.

    Returns workflow aggregates grouped by one or more dimensions. Useful for
    dashboards and understanding workflow status at a glance (e.g., "how many
    workflows failed today?", "how many workflows are pending per queue?",
    "what's the worst queue-wait time per workflow name?").

    Select at least one select_* flag to populate aggregate values. At least
    one group_by_* flag is mandatory to break the results down by dimension;
    a query with no group_by_* will fail.

    Args:
        application_name (string, required): Name of the DBOS application
        group_by_status (bool, optional): Group results by workflow status (default: false)
        group_by_name (bool, optional): Group results by workflow name (default: false)
        group_by_queue_name (bool, optional): Group results by queue name (default: false)
        group_by_executor_id (bool, optional): Group results by executor ID (default: false)
        group_by_application_version (bool, optional): Group results by application version (default: false)
        select_count (bool, optional): Include count of workflows in each group (default: false)
        select_min_created_at (bool, optional): Include min created_at (epoch ms) in each group (default: false)
        select_max_queue_wait_ms (bool, optional): Include max queue wait time (ms) in each group (default: false)
        select_max_total_latency_ms (bool, optional): Include max end-to-end latency (ms) in each group (default: false)
        status (array of strings, optional): Filter to these statuses before aggregating
        start_time (string, optional): Filter workflows created after this time (ISO 8601)
        end_time (string, optional): Filter workflows created before this time (ISO 8601)
        completed_after (string, optional): Filter workflows completed after this time (ISO 8601)
        completed_before (string, optional): Filter workflows completed before this time (ISO 8601)
        dequeued_after (string, optional): Filter workflows dequeued after this time (ISO 8601)
        dequeued_before (string, optional): Filter workflows dequeued before this time (ISO 8601)
        name (array of strings, optional): Filter to these workflow names before aggregating
        app_version (array of strings, optional): Filter to these application versions
        executor_id (array of strings, optional): Filter to these executor IDs
        queue_name (array of strings, optional): Filter to these queue names
        workflow_id_prefix (array of strings, optional): Filter to workflow IDs starting with these prefixes
        time_bucket_size_ms (int, optional): Bucket aggregates into time windows of this many milliseconds

    Returns:
        aggregates: Array of aggregate objects, each containing:
            - group (object): Map of dimension names to values (e.g., {"status": "ERROR", "name": "processOrder"})
            - count (int, optional): Number of workflows matching this group (if select_count)
            - min_created_at (int, optional): Earliest created_at in epoch ms (if select_min_created_at)
            - max_queue_wait_ms (int, optional): Max queue wait time in ms (if select_max_queue_wait_ms)
            - max_total_latency_ms (int, optional): Max end-to-end latency in ms (if select_max_total_latency_ms)
        application (string): Name of the application queried
    """
    aggregates = await client.get_workflow_aggregates(
        application_name=application_name,
        group_by_status=group_by_status,
        group_by_name=group_by_name,
        group_by_queue_name=group_by_queue_name,
        group_by_executor_id=group_by_executor_id,
        group_by_application_version=group_by_application_version,
        select_count=select_count,
        select_min_created_at=select_min_created_at,
        select_max_queue_wait_ms=select_max_queue_wait_ms,
        select_max_total_latency_ms=select_max_total_latency_ms,
        status=status,
        start_time=start_time,
        end_time=end_time,
        completed_after=completed_after,
        completed_before=completed_before,
        dequeued_after=dequeued_after,
        dequeued_before=dequeued_before,
        name=name,
        app_version=app_version,
        executor_id=executor_id,
        queue_name=queue_name,
        workflow_id_prefix=workflow_id_prefix,
        time_bucket_size_ms=time_bucket_size_ms,
    )
    return {
        "aggregates": aggregates,
        "application": application_name,
    }


@mcp.tool()
async def get_workflow_events(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Get events received by a workflow from DBOS Conductor.

    Events are key-value signals sent between workflows using the events API.
    Each event has a string key and a value.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): ID of the workflow

    Returns:
        events: Array of event objects, each containing:
            - key (string): The event key
            - value (string): The event value, in a human-readable representation
        count (int): Number of events returned
        workflow_id (string): The workflow ID queried
    """
    events = await client.get_workflow_events(
        application_name=application_name,
        workflow_id=workflow_id,
    )
    return {
        "events": events,
        "count": len(events),
        "workflow_id": workflow_id,
    }


@mcp.tool()
async def get_workflow_notifications(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Get notifications received by a workflow from DBOS Conductor.

    Notifications are messages sent to a workflow on a specific topic.
    Unlike events, multiple notifications can be sent on the same topic.

    Args:
        application_name (string, required): Name of the DBOS application
        workflow_id (string, required): ID of the workflow

    Returns:
        notifications: Array of notification objects, each containing:
            - topic (string, optional): The notification topic
            - message (string): The notification message, in a human-readable representation
            - created_at_epoch_ms (int): When the notification was sent (Unix epoch milliseconds)
            - consumed (bool): Whether the notification has been consumed by the workflow
        count (int): Number of notifications returned
        workflow_id (string): The workflow ID queried
    """
    notifications = await client.get_workflow_notifications(
        application_name=application_name,
        workflow_id=workflow_id,
    )
    return {
        "notifications": notifications,
        "count": len(notifications),
        "workflow_id": workflow_id,
    }


@mcp.tool()
async def list_schedules(
    application_name: str,
    status: str | list[str] | None = None,
    workflow_name: str | list[str] | None = None,
    schedule_name_prefix: str | list[str] | None = None,
) -> dict[str, Any]:
    """List schedules for an application from DBOS Conductor.

    Schedules automatically trigger workflows on a cron-based schedule.

    Args:
        application_name (string, required): Name of the DBOS application
        status (string or array of strings, optional): Filter by schedule status (e.g., "ACTIVE", "PAUSED")
        workflow_name (string or array of strings, optional): Filter by the workflow function the schedule triggers
        schedule_name_prefix (string or array of strings, optional): Filter by schedule name prefix

    Returns:
        schedules: Array of schedule objects, each containing:
            - schedule_id (string): Unique identifier
            - schedule_name (string): Name of the schedule
            - workflow_name (string): The workflow function this schedule triggers
            - workflow_class_name (string, optional): The workflow's class name, if any
            - schedule (string): Cron expression defining the schedule
            - status (string): "ACTIVE" or "PAUSED"
            - context (string, optional): Schedule context, in a human-readable representation (omitted for private-mode applications)
            - last_fired_at (string, optional): When the schedule last triggered (ISO 8601)
            - automatic_backfill (bool): Whether missed runs are automatically backfilled
            - cron_timezone (string, optional): Timezone for the cron expression
        count (int): Number of schedules returned
        application (string): Name of the application queried
    """
    schedules = await client.list_schedules(
        application_name=application_name,
        status=status,
        workflow_name=workflow_name,
        schedule_name_prefix=schedule_name_prefix,
    )
    return {
        "schedules": schedules,
        "count": len(schedules),
        "application": application_name,
    }


@mcp.tool()
async def get_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Get details of a specific schedule from DBOS Conductor.

    Args:
        application_name (string, required): Name of the DBOS application
        schedule_name (string, required): Name of the schedule

    Returns:
        schedule_id (string): Unique identifier
        schedule_name (string): Name of the schedule
        workflow_name (string): The workflow function this schedule triggers
        workflow_class_name (string, optional): The workflow's class name, if any
        schedule (string): Cron expression defining the schedule
        status (string): "ACTIVE" or "PAUSED"
        context (string, optional): Schedule context, in a human-readable representation (omitted for private-mode applications)
        last_fired_at (string, optional): When the schedule last triggered (ISO 8601)
        automatic_backfill (bool): Whether missed runs are automatically backfilled
        cron_timezone (string, optional): Timezone for the cron expression
    """
    return await client.get_schedule(
        application_name=application_name,
        schedule_name=schedule_name,
    )


@mcp.tool()
async def pause_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Pause a schedule, stopping it from triggering new workflows.

    The schedule can be resumed later with resume_schedule.

    Args:
        application_name (string, required): Name of the DBOS application
        schedule_name (string, required): Name of the schedule to pause

    Returns:
        message (string): Confirmation message
        schedule_name (string): The paused schedule name
    """
    await client.pause_schedule(
        application_name=application_name,
        schedule_name=schedule_name,
    )
    return {
        "message": "Schedule paused",
        "schedule_name": schedule_name,
    }


@mcp.tool()
async def resume_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Resume a paused schedule, allowing it to trigger workflows again.

    Args:
        application_name (string, required): Name of the DBOS application
        schedule_name (string, required): Name of the schedule to resume

    Returns:
        message (string): Confirmation message
        schedule_name (string): The resumed schedule name
    """
    await client.resume_schedule(
        application_name=application_name,
        schedule_name=schedule_name,
    )
    return {
        "message": "Schedule resumed",
        "schedule_name": schedule_name,
    }


@mcp.tool()
async def trigger_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Manually trigger a schedule to run its workflow immediately.

    This does not affect the schedule's regular cron timing.

    Args:
        application_name (string, required): Name of the DBOS application
        schedule_name (string, required): Name of the schedule to trigger

    Returns:
        workflow_id (string, optional): The ID of the triggered workflow, if one was created
        schedule_name (string): The triggered schedule name
    """
    result = await client.trigger_schedule(
        application_name=application_name,
        schedule_name=schedule_name,
    )
    return {
        "workflow_id": result.get("workflow_id"),
        "schedule_name": schedule_name,
    }


@mcp.tool()
async def list_application_versions(
    application_name: str,
) -> dict[str, Any]:
    """List all versions of an application from DBOS Conductor.

    Each time an application connects with a new version string, a new version
    is recorded. Use set_latest_application_version to control which version
    is considered current.

    Args:
        application_name (string, required): Name of the DBOS application

    Returns:
        versions: Array of version objects, each containing:
            - version_id (string): Unique identifier for this version
            - version_name (string): The version string
            - version_timestamp (int): Version timestamp (Unix epoch milliseconds)
            - created_at (int): When this version was first seen (Unix epoch milliseconds)
        count (int): Number of versions returned
        application (string): Name of the application queried
    """
    versions = await client.list_application_versions(
        application_name=application_name,
    )
    return {
        "versions": versions,
        "count": len(versions),
        "application": application_name,
    }


@mcp.tool()
async def set_latest_application_version(
    application_name: str,
    version_name: str,
) -> dict[str, Any]:
    """Set the latest version for an application in DBOS Conductor.

    This controls which version is considered current. Useful for rolling
    back to a previous version or promoting a specific version.

    Args:
        application_name (string, required): Name of the DBOS application
        version_name (string, required): The version string to set as latest

    Returns:
        message (string): Confirmation message
        version_name (string): The version that was set as latest
    """
    await client.set_latest_application_version(
        application_name=application_name,
        version_name=version_name,
    )
    return {
        "message": f"Latest version set to {version_name}",
        "version_name": version_name,
    }


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
