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
        return json.loads(CREDENTIALS_PATH.read_text())
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
        PENDING_LOGIN_PATH.write_text(json.dumps({
            "device_code": device_data["device_code"],
            "interval": device_data.get("interval", 5),
            "expires_at": time.time() + device_data.get("expires_in", 900),
        }))

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
    creds = _get_credentials()
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
            f"{CONDUCTOR_URL}/api/{creds['organization']}/applications/{application_name}/workflows/",
            json=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {creds['token']}",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


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
        return response.json()
