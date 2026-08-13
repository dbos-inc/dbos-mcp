"""DBOS Conductor API client (Conductor API v2)."""

import json
import time
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx

# Auth0 configuration (production)
AUTH0_DOMAIN = "login.dbos.dev"
AUTH0_CLIENT_ID = "6p7Sjxf13cyLMkdwn14MxlH7JdhILled"
AUTH0_AUDIENCE = "dbos-cloud-api"

# DBOS Cloud API
DBOS_CLOUD_URL = "https://cloud.dbos.dev"
CONDUCTOR_URL = f"{DBOS_CLOUD_URL}/conductor/v2"

# Storage
CREDENTIALS_DIR = Path.home() / ".dbos-mcp"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials"
PENDING_LOGIN_PATH = CREDENTIALS_DIR / "pending_login"

TIMEOUT = 30.0


def _load_credentials() -> dict[str, str] | None:
    """Load stored credentials."""
    if not CREDENTIALS_PATH.exists():
        return None
    try:
        result: dict[str, str] = json.loads(CREDENTIALS_PATH.read_text())
        return result
    except (json.JSONDecodeError, IOError):
        return None


def _save_credentials(credentials: dict[str, str]) -> None:
    """Save credentials to file."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.write_text(json.dumps(credentials, indent=2))


def _path(param: str) -> str:
    """Percent-encode a URL path parameter (workflow IDs may contain /, ?, #, etc.)."""
    return quote(param, safe="")


def _get_credentials() -> dict[str, str]:
    """Get credentials or raise if not logged in."""
    creds = _load_credentials()
    if not creds or "token" not in creds or "organization" not in creds:
        raise RuntimeError("Not logged in. Please call the login tool first.")
    return creds


def _as_list(value: str | list[str] | None) -> list[str] | None:
    """Normalize a scalar-or-list filter to the list form the v2 API expects.

    Empty strings are dropped, and a filter left with no values is omitted
    entirely. No workflow ID, name, status, or queue is ever the empty string,
    so filtering on one could only ever match nothing -- and the API would
    answer with a perfectly ordinary "0 results" rather than an error. Treating
    a blank as absent keeps that from silently reading as "nothing exists", and
    matches how v2's query-parameter endpoints already ignore blank filters.
    """
    if value is None:
        return None
    items = [value] if isinstance(value, str) else value
    return [v for v in items if v != ""] or None


def _strip_schema(data: Any) -> Any:
    """Drop the `$schema` key the v2 API adds to single-object responses."""
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k != "$schema"}
    if isinstance(data, list):
        return [_strip_schema(item) for item in data]
    return data


def _compact(**fields: Any) -> dict[str, Any]:
    """Build a request body from the fields that were actually supplied."""
    return {k: v for k, v in fields.items() if v is not None}


async def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    """Send an authenticated request to the Conductor v2 API under the caller's org."""
    creds = _get_credentials()
    url = f"{CONDUCTOR_URL}/orgs/{_path(creds['organization'])}{path}"
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            url,
            params=params or None,
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        if response.status_code == 204 or not response.content:
            return None
        return _strip_schema(response.json())


async def _app_request(
    method: str,
    application_name: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    body: dict[str, Any] | None = None,
) -> Any:
    """Send an authenticated request scoped to a single application."""
    return await _request(
        method,
        f"/apps/{_path(application_name)}{path}",
        params=params,
        body=body,
    )


async def login() -> dict[str, str]:
    """Start login flow - returns URL for user to visit."""
    async with httpx.AsyncClient() as http:
        response = await http.post(
            f"https://{AUTH0_DOMAIN}/oauth/device/code",
            data={
                "client_id": AUTH0_CLIENT_ID,
                "audience": AUTH0_AUDIENCE,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response.raise_for_status()
        device_data = response.json()

        # Save pending login info
        CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
        PENDING_LOGIN_PATH.write_text(
            json.dumps(
                {
                    "device_code": device_data["device_code"],
                    "interval": device_data.get("interval", 5),
                    "expires_at": time.time() + device_data.get("expires_in", 900),
                }
            )
        )

        return {
            "url": device_data["verification_uri_complete"],
            "message": "Please open this URL in your browser to log in, then call login_complete",
        }


async def login_complete() -> dict[str, str]:
    """Complete login after user has authenticated in browser."""
    if not PENDING_LOGIN_PATH.exists():
        raise RuntimeError("No pending login. Call login first.")

    pending = json.loads(PENDING_LOGIN_PATH.read_text())
    device_code = pending["device_code"]
    interval = pending["interval"]
    expires_at = pending["expires_at"]

    async with httpx.AsyncClient() as http:
        # Poll for token
        while time.time() < expires_at:
            response = await http.post(
                f"https://{AUTH0_DOMAIN}/oauth/token",
                data={
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "device_code": device_code,
                    "client_id": AUTH0_CLIENT_ID,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if response.status_code == 200:
                token_data = response.json()
                break
            # Auth pending, wait and retry
            time.sleep(interval)
        else:
            PENDING_LOGIN_PATH.unlink(missing_ok=True)
            raise RuntimeError("Login timed out. Please call login to start again.")

        # Get user profile
        access_token = token_data["access_token"]
        response = await http.get(
            f"{CONDUCTOR_URL}/users/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        profile = response.json()

        # Save credentials and clean up
        credentials = {
            "token": access_token,
            "userName": profile.get("name", ""),
            "organization": profile.get("orgName", ""),
        }
        _save_credentials(credentials)
        PENDING_LOGIN_PATH.unlink(missing_ok=True)

        return {
            "userName": credentials["userName"],
            "organization": credentials["organization"],
        }


async def list_applications() -> list[dict[str, Any]]:
    """List all applications."""
    result: list[dict[str, Any]] = await _request("GET", "/apps")
    return result


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
    schedule_name: str | list[str] | None = None,
) -> list[dict[str, Any]]:
    """List workflows with optional filters."""
    body = _compact(
        workflowIds=_as_list(workflow_uuids),
        workflowName=_as_list(workflow_name),
        user=_as_list(authenticated_user),
        startTime=start_time,
        endTime=end_time,
        completedAfter=completed_after,
        completedBefore=completed_before,
        dequeuedAfter=dequeued_after,
        dequeuedBefore=dequeued_before,
        status=_as_list(status),
        appVersion=_as_list(application_version),
        forkedFrom=_as_list(forked_from),
        parentWorkflowId=_as_list(parent_workflow_id),
        queueName=_as_list(queue_name),
        limit=limit,
        offset=offset,
        sortDesc=sort_desc,
        workflowIdPrefix=_as_list(workflow_id_prefix),
        loadInput=load_input,
        loadOutput=load_output,
        executorId=_as_list(executor_id),
        queuesOnly=queues_only,
        wasForkedFrom=was_forked_from,
        hasParent=has_parent,
        scheduleName=_as_list(schedule_name),
    )
    result: list[dict[str, Any]] = await _app_request(
        "POST", application_name, "/workflows/search", body=body
    )
    return result


async def get_workflow(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Get a specific workflow by ID."""
    result: dict[str, Any] = await _app_request(
        "GET", application_name, f"/workflows/{_path(workflow_id)}"
    )
    return result


async def list_steps(
    application_name: str,
    workflow_id: str,
    limit: int | None = None,
    offset: int | None = None,
) -> list[dict[str, Any]]:
    """Get execution steps for a workflow."""
    result: list[dict[str, Any]] = await _app_request(
        "GET",
        application_name,
        f"/workflows/{_path(workflow_id)}/steps",
        params=_compact(limit=limit, offset=offset),
    )
    return result


async def list_executors(
    application_name: str,
) -> list[dict[str, Any]]:
    """List executors for an application."""
    result: list[dict[str, Any]] = await _app_request(
        "GET", application_name, "/executors"
    )
    return result


async def cancel_workflow(
    application_name: str,
    workflow_id: str,
    cancel_children: bool = False,
) -> None:
    """Cancel a workflow."""
    await _app_request(
        "POST",
        application_name,
        f"/workflows/{_path(workflow_id)}/cancel",
        body={"cancelChildren": cancel_children},
    )


async def resume_workflow(
    application_name: str,
    workflow_id: str,
    queue_name: str | None = None,
) -> None:
    """Resume a workflow."""
    await _app_request(
        "POST",
        application_name,
        f"/workflows/{_path(workflow_id)}/resume",
        body=_compact(queueName=queue_name),
    )


async def fork_workflow(
    application_name: str,
    workflow_id: str,
    start_step: int,
    application_version: str | None = None,
    new_workflow_id: str | None = None,
    queue_name: str | None = None,
    queue_partition_key: str | None = None,
) -> dict[str, Any]:
    """Fork a workflow from a specific step."""
    body = _compact(
        startStep=start_step,
        appVersion=application_version,
        newWorkflowId=new_workflow_id,
        queueName=queue_name,
        queuePartitionKey=queue_partition_key,
    )
    result: dict[str, Any] = await _app_request(
        "POST", application_name, f"/workflows/{_path(workflow_id)}/fork", body=body
    )
    return result


async def bulk_cancel_workflows(
    application_name: str,
    workflow_ids: list[str],
    cancel_children: bool = False,
) -> None:
    """Cancel multiple workflows."""
    await _app_request(
        "POST",
        application_name,
        "/workflows/bulk-cancel",
        body={"workflowIds": workflow_ids, "cancelChildren": cancel_children},
    )


async def bulk_resume_workflows(
    application_name: str,
    workflow_ids: list[str],
    queue_name: str | None = None,
) -> None:
    """Resume multiple workflows."""
    await _app_request(
        "POST",
        application_name,
        "/workflows/bulk-resume",
        body=_compact(workflowIds=workflow_ids, queueName=queue_name),
    )


async def bulk_delete_workflows(
    application_name: str,
    workflow_ids: list[str],
    delete_children: bool = False,
) -> None:
    """Delete multiple workflows."""
    await _app_request(
        "POST",
        application_name,
        "/workflows/bulk-delete",
        body={"workflowIds": workflow_ids, "deleteChildren": delete_children},
    )


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
) -> list[str]:
    """Fork multiple workflows from their failure point."""
    body = _compact(
        workflowIds=workflow_ids,
        appVersion=application_version,
        queueName=queue_name,
        queuePartitionKey=queue_partition_key,
        fromLastFailure=from_last_failure or None,
        fromLastStep=from_last_step or None,
        fromStep=from_step,
        fromStepName=from_step_name,
    )
    data = await _app_request(
        "POST", application_name, "/workflows/bulk-fork-from-failure", body=body
    )
    result: list[str] = data.get("workflowIds", [])
    return result


async def delete_workflow(
    application_name: str,
    workflow_id: str,
    delete_children: bool = False,
) -> None:
    """Delete a workflow."""
    params: dict[str, Any] = {}
    if delete_children:
        params["deleteChildren"] = "true"

    await _app_request(
        "DELETE",
        application_name,
        f"/workflows/{_path(workflow_id)}",
        params=params,
    )


async def get_workflow_aggregates(
    application_name: str,
    group_by_status: bool = False,
    group_by_name: bool = False,
    group_by_queue_name: bool = False,
    group_by_executor_id: bool = False,
    group_by_application_version: bool = False,
    group_by_application_name: bool = False,
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
    schedule_name: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Get workflow aggregates (counts grouped by dimensions)."""
    body: dict[str, Any] = {
        "groupByStatus": group_by_status,
        "groupByWorkflowName": group_by_name,
        "groupByQueueName": group_by_queue_name,
        "groupByExecutorId": group_by_executor_id,
        "groupByAppVersion": group_by_application_version,
        "groupByApplicationName": group_by_application_name,
        "selectCount": select_count,
        "selectMinCreatedAt": select_min_created_at,
        "selectMaxQueueWaitMs": select_max_queue_wait_ms,
        "selectMaxTotalLatencyMs": select_max_total_latency_ms,
    }
    body.update(
        _compact(
            status=_as_list(status),
            startTime=start_time,
            endTime=end_time,
            completedAfter=completed_after,
            completedBefore=completed_before,
            dequeuedAfter=dequeued_after,
            dequeuedBefore=dequeued_before,
            workflowName=_as_list(name),
            appVersion=_as_list(app_version),
            executorId=_as_list(executor_id),
            queueName=_as_list(queue_name),
            workflowIdPrefix=_as_list(workflow_id_prefix),
            timeBucketSizeMs=time_bucket_size_ms,
            scheduleName=_as_list(schedule_name),
        )
    )

    result: list[dict[str, Any]] = await _app_request(
        "POST", application_name, "/workflows/aggregates", body=body
    )
    return result


async def get_workflow_events(
    application_name: str,
    workflow_id: str,
) -> list[dict[str, Any]]:
    """Get events for a workflow."""
    result: list[dict[str, Any]] = await _app_request(
        "GET", application_name, f"/workflows/{_path(workflow_id)}/events"
    )
    return result


async def get_workflow_notifications(
    application_name: str,
    workflow_id: str,
) -> list[dict[str, Any]]:
    """Get notifications for a workflow."""
    result: list[dict[str, Any]] = await _app_request(
        "GET", application_name, f"/workflows/{_path(workflow_id)}/notifications"
    )
    return result


async def list_schedules(
    application_name: str,
    status: str | None = None,
    workflow_name: str | None = None,
    schedule_name_prefix: str | None = None,
) -> list[dict[str, Any]]:
    """List schedules for an application."""
    result: list[dict[str, Any]] = await _app_request(
        "GET",
        application_name,
        "/schedules",
        params=_compact(
            status=status,
            workflowName=workflow_name,
            scheduleNamePrefix=schedule_name_prefix,
        ),
    )
    return result


async def get_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Get a specific schedule by name."""
    result: dict[str, Any] = await _app_request(
        "GET", application_name, f"/schedules/{_path(schedule_name)}"
    )
    return result


async def pause_schedule(
    application_name: str,
    schedule_name: str,
) -> None:
    """Pause a schedule."""
    await _app_request(
        "POST", application_name, f"/schedules/{_path(schedule_name)}/pause"
    )


async def resume_schedule(
    application_name: str,
    schedule_name: str,
) -> None:
    """Resume a paused schedule."""
    await _app_request(
        "POST", application_name, f"/schedules/{_path(schedule_name)}/resume"
    )


async def trigger_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Trigger a schedule to run immediately."""
    result: dict[str, Any] = await _app_request(
        "POST", application_name, f"/schedules/{_path(schedule_name)}/trigger"
    )
    return result


async def list_application_versions(
    application_name: str,
) -> list[dict[str, Any]]:
    """List versions for an application."""
    result: list[dict[str, Any]] = await _app_request(
        "GET", application_name, "/versions"
    )
    return result


async def set_latest_application_version(
    application_name: str,
    version_name: str,
) -> None:
    """Set the latest application version."""
    await _app_request(
        "PATCH",
        application_name,
        "/versions/latest",
        body={"versionName": version_name},
    )
