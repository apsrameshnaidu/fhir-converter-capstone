"""MCP server exposing the FHIR Converter API (api/app.py) as tools.

By default the tools call the FastAPI app in-process, so the HTTP server does not
need to be running. Set FHIR_API_URL (e.g. http://127.0.0.1:8000) to call a running
instance started with `python run_api.py` instead.

Registered for this project in .mcp.json. Run manually with:
    python mcp_server.py
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Literal, Optional, Union

import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))

from api.app import app as fastapi_app  # noqa: E402

API_URL = os.environ.get("FHIR_API_URL")

mcp = MCPServer(
    name="fhir-converter",
    instructions=(
        "Tools for converting healthcare documents to FHIR R4. Call list_templates "
        "first to find a valid template_name, then convert_ccda (C-CDA XML) or "
        "convert_stu3 (FHIR STU3 JSON)."
    ),
)


def _client() -> httpx.AsyncClient:
    if API_URL:
        return httpx.AsyncClient(base_url=API_URL, timeout=60)
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=fastapi_app), base_url="http://fhir-api", timeout=60
    )


async def _call(method: str, path: str, json: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    async with _client() as client:
        try:
            response = await client.request(method, path, json=json)
        except httpx.HTTPError as e:
            raise ToolError(f"Could not reach the FHIR Converter API: {e}") from e
    if response.is_error:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        raise ToolError(f"API returned {response.status_code}: {detail}")
    return response.json()


def _resolve_path(file_path: str) -> Path:
    path = Path(file_path)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.is_file():
        raise ToolError(f"File not found: {path}")
    return path


@mcp.tool()
async def health_check() -> Dict[str, Any]:
    """Check that the FHIR Converter API is up. Calls GET /health."""
    return await _call("GET", "/health")


@mcp.tool()
async def list_templates(source_format: Literal["ccda", "stu3"]) -> Dict[str, Any]:
    """List the root templates available for a source format. Calls GET /templates/{source_format}.

    Args:
        source_format: "ccda" for C-CDA XML documents, "stu3" for FHIR STU3 resources.
    """
    return await _call("GET", f"/templates/{source_format}")


@mcp.tool()
async def convert_ccda(
    template_name: str = "CCD",
    data: Optional[str] = None,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a C-CDA XML document to a FHIR R4 Bundle. Calls POST /convert/ccda.

    Provide either `data` (the XML as a string) or `file_path` (a path to a .ccda/.xml
    file, absolute or relative to the project root, e.g. data/sample/ccda/CCD.ccda).

    Args:
        template_name: Root C-CDA template, e.g. CCD, DischargeSummary, ProgressNote.
        data: The C-CDA XML document.
        file_path: Path to a C-CDA file to read instead of passing `data`.
    """
    if (data is None) == (file_path is None):
        raise ToolError("Provide exactly one of `data` or `file_path`.")
    if file_path is not None:
        data = _resolve_path(file_path).read_text(encoding="utf-8")
    return await _call("POST", "/convert/ccda", {"template_name": template_name, "data": data})


@mcp.tool()
async def convert_stu3(
    template_name: str,
    data: Optional[Union[Dict[str, Any], str]] = None,
    file_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Convert a FHIR STU3 resource to FHIR R4. Calls POST /convert/stu3.

    Provide either `data` (the resource as a JSON object or string) or `file_path`
    (a path to a .json file, absolute or relative to the project root).

    Args:
        template_name: STU3 resource template matching the resourceType, e.g. Patient.
        data: The STU3 resource.
        file_path: Path to a STU3 JSON file to read instead of passing `data`.
    """
    if (data is None) == (file_path is None):
        raise ToolError("Provide exactly one of `data` or `file_path`.")
    if file_path is not None:
        data = _resolve_path(file_path).read_text(encoding="utf-8")
    return await _call("POST", "/convert/stu3", {"template_name": template_name, "data": data})


if __name__ == "__main__":
    mcp.run()
