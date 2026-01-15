"""DBOS Conductor API client."""

import os
from typing import Any

import httpx

CONDUCTOR_URL = "https://cloud.dbos.dev/conductor/v1alpha1"

CONDUCTOR_TOKEN = os.environ.get("DBOS_CONDUCTOR_TOKEN")
if not CONDUCTOR_TOKEN:
    raise RuntimeError("DBOS_CONDUCTOR_TOKEN environment variable is required")

CONDUCTOR_ORG_ID = os.environ.get("DBOS_CONDUCTOR_ORG_ID")
if not CONDUCTOR_ORG_ID:
    raise RuntimeError("DBOS_CONDUCTOR_ORG_ID environment variable is required")


def _headers() -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if CONDUCTOR_TOKEN:
        headers["Authorization"] = f"Bearer {CONDUCTOR_TOKEN}"
    return headers


def _applications_url(path: str = "") -> str:
    base = f"{CONDUCTOR_URL}/api/{CONDUCTOR_ORG_ID}/applications"
    return f"{base}/{path}" if path else base


def _workflows_url(app: str, path: str = "") -> str:
    base = f"{_applications_url(app)}/workflows"
    return f"{base}/{path}" if path else base


async def list_applications() -> list[dict[str, Any]]:
    """List all applications."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _applications_url(),
            headers=_headers(),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


async def list_workflows(
    application_name: str,
    status: str | None = None,
    workflow_name: str | None = None,
    workflow_uuids: list[str] | None = None,
    authenticated_user: str | None = None,
    start_time: str | None = None,
    end_time: str | None = None,
    application_version: str | None = None,
    limit: int | None = None,
    offset: int | None = None,
    sort_desc: bool | None = None,
    load_input: bool | None = None,
    load_output: bool | None = None,
) -> list[dict[str, Any]]:
    """List workflows with optional filters."""
    body: dict[str, Any] = {}

    if status is not None:
        body["status"] = status
    if workflow_name is not None:
        body["workflow_name"] = workflow_name
    if workflow_uuids is not None:
        body["workflow_uuids"] = workflow_uuids
    if authenticated_user is not None:
        body["authenticated_user"] = authenticated_user
    if start_time is not None:
        body["start_time"] = start_time
    if end_time is not None:
        body["end_time"] = end_time
    if application_version is not None:
        body["application_version"] = application_version
    if limit is not None:
        body["limit"] = limit
    if offset is not None:
        body["offset"] = offset
    if sort_desc is not None:
        body["sort_desc"] = sort_desc
    if load_input is not None:
        body["load_input"] = load_input
    if load_output is not None:
        body["load_output"] = load_output

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{_workflows_url(application_name)}/",
            json=body,
            headers=_headers(),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


async def get_workflow(
    application_name: str,
    workflow_id: str,
) -> dict[str, Any]:
    """Get a specific workflow by ID."""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _workflows_url(application_name, workflow_id),
            headers=_headers(),
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()
