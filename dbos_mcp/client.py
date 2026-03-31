"""DBOS Conductor API client."""

import json
import time
from pathlib import Path
from typing import Any

import httpx

# Auth0 configuration (production)
AUTH0_DOMAIN = "login.dbos.dev"
AUTH0_CLIENT_ID = "6p7Sjxf13cyLMkdwn14MxlH7JdhILled"
AUTH0_AUDIENCE = "dbos-cloud-api"

# DBOS Cloud API
DBOS_CLOUD_URL = "https://cloud.dbos.dev"
CONDUCTOR_URL = f"{DBOS_CLOUD_URL}/conductor/v1alpha1"

# Storage
CREDENTIALS_DIR = Path.home() / ".dbos-mcp"
CREDENTIALS_PATH = CREDENTIALS_DIR / "credentials"
PENDING_LOGIN_PATH = CREDENTIALS_DIR / "pending_login"


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


def _get_credentials() -> dict[str, str]:
    """Get credentials or raise if not logged in."""
    creds = _load_credentials()
    if not creds or "token" not in creds or "organization" not in creds:
        raise RuntimeError("Not logged in. Please call the login tool first.")
    return creds


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
            f"{DBOS_CLOUD_URL}/v1alpha1/user/profile",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        response.raise_for_status()
        profile = response.json()

        # Save credentials and clean up
        credentials = {
            "token": access_token,
            "userName": profile.get("Name", ""),
            "organization": profile.get("Organization", ""),
        }
        _save_credentials(credentials)
        PENDING_LOGIN_PATH.unlink(missing_ok=True)

        return {
            "userName": credentials["userName"],
            "organization": credentials["organization"],
        }


async def list_applications() -> list[dict[str, Any]]:
    """List all applications."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json()
        return result


async def list_workflows(
    application_name: str,
    workflow_uuids: list[str] | None = None,
    workflow_name: str | list[str] | None = None,
    authenticated_user: str | list[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
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
) -> list[dict[str, Any]]:
    """List workflows with optional filters."""
    creds = _get_credentials()
    body: dict[str, Any] = {}

    if workflow_uuids is not None:
        body["workflow_uuids"] = workflow_uuids
    if workflow_name is not None:
        body["workflow_name"] = workflow_name
    if authenticated_user is not None:
        body["authenticated_user"] = authenticated_user
    if start_time is not None:
        body["start_time"] = start_time
    if end_time is not None:
        body["end_time"] = end_time
    if status is not None:
        body["status"] = status
    if application_version is not None:
        body["application_version"] = application_version
    if forked_from is not None:
        body["forked_from"] = forked_from
    if parent_workflow_id is not None:
        body["parent_workflow_id"] = parent_workflow_id
    if queue_name is not None:
        body["queue_name"] = queue_name
    if limit is not None:
        body["limit"] = limit
    if offset is not None:
        body["offset"] = offset
    if sort_desc is not None:
        body["sort_desc"] = sort_desc
    if workflow_id_prefix is not None:
        body["workflow_id_prefix"] = workflow_id_prefix
    if load_input is not None:
        body["load_input"] = load_input
    if load_output is not None:
        body["load_output"] = load_output
    if executor_id is not None:
        body["executor_id"] = executor_id
    if queues_only is not None:
        body["queues_only"] = queues_only
    if was_forked_from is not None:
        body["was_forked_from"] = was_forked_from

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json()
        return result


async def get_workflow(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Get a specific workflow by ID."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


async def list_steps(
    application_name: str,
    workflow_id: str,
) -> list[dict[str, Any]]:
    """Get execution steps for a workflow."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}/steps",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json()
        return result


async def list_executors(
    application_name: str,
) -> list[dict[str, Any]]:
    """List executors for an application."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/executors",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result: list[dict[str, Any]] = response.json()
        return result


async def cancel_workflow(
    application_name: str,
    workflow_id: str,
) -> None:
    """Cancel a workflow."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}/cancel",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


async def resume_workflow(
    application_name: str,
    workflow_id: str,
) -> None:
    """Resume a workflow."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}/resume",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


async def fork_workflow(
    application_name: str,
    workflow_id: str,
    start_step: int,
    application_version: str | None = None,
    new_workflow_id: str | None = None,
) -> dict[str, Any]:
    """Fork a workflow from a specific step."""
    creds = _get_credentials()
    body: dict[str, Any] = {"start_step": start_step}
    if application_version is not None:
        body["application_version"] = application_version
    if new_workflow_id is not None:
        body["new_workflow_id"] = new_workflow_id

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}/fork",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


async def bulk_cancel_workflows(
    application_name: str,
    workflow_ids: list[str],
) -> None:
    """Cancel multiple workflows."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/cancel",
            json={"workflow_ids": workflow_ids},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


async def bulk_resume_workflows(
    application_name: str,
    workflow_ids: list[str],
    queue_name: str | None = None,
) -> None:
    """Resume multiple workflows."""
    creds = _get_credentials()
    body: dict[str, Any] = {"workflow_ids": workflow_ids}
    if queue_name is not None:
        body["queue_name"] = queue_name

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/resume",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


async def bulk_delete_workflows(
    application_name: str,
    workflow_ids: list[str],
    delete_children: bool = False,
) -> None:
    """Delete multiple workflows."""
    creds = _get_credentials()
    body: dict[str, Any] = {"workflow_ids": workflow_ids}
    if delete_children:
        body["delete_children"] = True

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/delete",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


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
    creds = _get_credentials()
    body: dict[str, Any] = {"workflow_ids": workflow_ids}
    if application_version is not None:
        body["application_version"] = application_version
    if queue_name is not None:
        body["queue_name"] = queue_name
    if queue_partition_key is not None:
        body["queue_partition_key"] = queue_partition_key
    if from_last_failure:
        body["from_last_failure"] = True
    if from_last_step:
        body["from_last_step"] = True
    if from_step is not None:
        body["from_step"] = from_step
    if from_step_name is not None:
        body["from_step_name"] = from_step_name

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/fork-from-failure",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        result: list[str] = data.get("workflow_ids", [])
        return result


async def delete_workflow(
    application_name: str,
    workflow_id: str,
    delete_children: bool = False,
) -> None:
    """Delete a workflow."""
    creds = _get_credentials()
    params: dict[str, Any] = {}
    if delete_children:
        params["delete_children"] = "true"

    async with httpx.AsyncClient() as client:
        response = await client.delete(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}",
            params=params,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


async def get_workflow_aggregates(
    application_name: str,
    group_by_status: bool = False,
    group_by_name: bool = False,
    group_by_queue_name: bool = False,
    group_by_executor_id: bool = False,
    group_by_application_version: bool = False,
    status: list[str] | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    name: list[str] | None = None,
    app_version: list[str] | None = None,
    executor_id: list[str] | None = None,
    queue_name: list[str] | None = None,
    workflow_id_prefix: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Get workflow aggregates (counts grouped by dimensions)."""
    creds = _get_credentials()
    body: dict[str, Any] = {
        "group_by_status": group_by_status,
        "group_by_name": group_by_name,
        "group_by_queue_name": group_by_queue_name,
        "group_by_executor_id": group_by_executor_id,
        "group_by_application_version": group_by_application_version,
    }
    if status is not None:
        body["status"] = status
    if start_time is not None:
        body["start_time"] = start_time
    if end_time is not None:
        body["end_time"] = end_time
    if name is not None:
        body["name"] = name
    if app_version is not None:
        body["app_version"] = app_version
    if executor_id is not None:
        body["executor_id"] = executor_id
    if queue_name is not None:
        body["queue_name"] = queue_name
    if workflow_id_prefix is not None:
        body["workflow_id_prefix"] = workflow_id_prefix

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/aggregates",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        result: list[dict[str, Any]] = data.get("output", [])
        return result


async def get_workflow_events(
    application_name: str,
    workflow_id: str,
) -> list[dict[str, Any]]:
    """Get events for a workflow."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}/events",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        result: list[dict[str, Any]] = data.get("events", [])
        return result


async def get_workflow_notifications(
    application_name: str,
    workflow_id: str,
) -> list[dict[str, Any]]:
    """Get notifications for a workflow."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/{workflow_id}/notifications",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        result: list[dict[str, Any]] = data.get("notifications", [])
        return result


async def list_schedules(
    application_name: str,
    status: str | list[str] | None = None,
    workflow_name: str | list[str] | None = None,
    schedule_name_prefix: str | list[str] | None = None,
    load_context: bool | None = None,
) -> list[dict[str, Any]]:
    """List schedules for an application."""
    creds = _get_credentials()
    body: dict[str, Any] = {}
    if status is not None:
        body["status"] = status
    if workflow_name is not None:
        body["workflow_name"] = workflow_name
    if schedule_name_prefix is not None:
        body["schedule_name_prefix"] = schedule_name_prefix
    if load_context is not None:
        body["load_context"] = load_context

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/schedules/list",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        result: list[dict[str, Any]] = data.get("output", [])
        return result


async def get_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Get a specific schedule by name."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/schedules/{schedule_name}",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        result: dict[str, Any] = data.get("output", {})
        return result


async def pause_schedule(
    application_name: str,
    schedule_name: str,
) -> None:
    """Pause a schedule."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/schedules/{schedule_name}/pause",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


async def resume_schedule(
    application_name: str,
    schedule_name: str,
) -> None:
    """Resume a paused schedule."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/schedules/{schedule_name}/resume",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()


async def trigger_schedule(
    application_name: str,
    schedule_name: str,
) -> dict[str, Any]:
    """Trigger a schedule to run immediately."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/schedules/{schedule_name}/trigger",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result: dict[str, Any] = response.json()
        return result


async def list_application_versions(
    application_name: str,
) -> list[dict[str, Any]]:
    """List versions for an application."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/versions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        data = response.json()
        result: list[dict[str, Any]] = data.get("output", [])
        return result


async def set_latest_application_version(
    application_name: str,
    version_name: str,
) -> None:
    """Set the latest application version."""
    creds = _get_credentials()
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/versions/set-latest",
            json={"version_name": version_name},
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
