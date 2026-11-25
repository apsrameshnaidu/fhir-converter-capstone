"""FastAPI server exposing the FHIR converter over HTTP.

Run with:
    uvicorn api.main:app --reload

Interactive docs are served at http://127.0.0.1:8000/docs
"""

import json
from importlib.resources import files
from typing import Any, Dict, List, Literal, Union

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from fhir_converter.exceptions import RenderingError
from fhir_converter.renderers import CcdaRenderer, Stu3FhirRenderer

app = FastAPI(
    title="FHIR Converter API",
    description="Convert C-CDA and FHIR STU3 documents to FHIR R4.",
    version="0.1.0",
)

# Renderers are created once so their template caches are reused across requests.
ccda_renderer = CcdaRenderer()
stu3_renderer = Stu3FhirRenderer()

SourceFormat = Literal["ccda", "stu3"]


class CcdaConvertRequest(BaseModel):
    template_name: str = Field("CCD", description="Root C-CDA template, e.g. CCD")
    data: str = Field(..., description="The C-CDA XML document as a string")


class Stu3ConvertRequest(BaseModel):
    template_name: str = Field(..., description="STU3 resource template, e.g. Patient")
    data: Union[Dict[str, Any], str] = Field(
        ..., description="The STU3 resource as a JSON object or JSON string"
    )


class HealthResponse(BaseModel):
    status: str


class TemplatesResponse(BaseModel):
    format: SourceFormat
    templates: List[str]


def _root_templates(source_format: SourceFormat) -> List[str]:
    """List the top-level .liquid templates bundled for a source format."""
    template_dir = files("fhir_converter.templates").joinpath(source_format)
    return sorted(
        entry.name[: -len(".liquid")]
        for entry in template_dir.iterdir()
        if entry.is_file() and entry.name.endswith(".liquid")
    )


def _render(renderer, template_name: str, data: str) -> Dict[str, Any]:
    try:
        return dict(renderer.render_to_fhir(template_name, data))
    except RenderingError as e:
        detail = f"{e}: {e.__cause__}" if e.__cause__ else str(e)
        raise HTTPException(status_code=422, detail=detail)


@app.get("/health", response_model=HealthResponse, tags=["system"])
def health() -> HealthResponse:
    """Liveness check."""
    return HealthResponse(status="ok")


@app.get("/templates/{source_format}", response_model=TemplatesResponse, tags=["templates"])
def list_templates(source_format: SourceFormat) -> TemplatesResponse:
    """List the root templates available for a source format (ccda or stu3)."""
    return TemplatesResponse(format=source_format, templates=_root_templates(source_format))


@app.post("/convert/ccda", tags=["convert"])
def convert_ccda(request: CcdaConvertRequest) -> Dict[str, Any]:
    """Convert a C-CDA XML document to a FHIR R4 Bundle."""
    if request.template_name not in _root_templates("ccda"):
        raise HTTPException(status_code=404, detail=f"Unknown C-CDA template '{request.template_name}'")
    return _render(ccda_renderer, request.template_name, request.data)


@app.post("/convert/stu3", tags=["convert"])
def convert_stu3(request: Stu3ConvertRequest) -> Dict[str, Any]:
    """Convert a FHIR STU3 resource to FHIR R4."""
    if request.template_name not in _root_templates("stu3"):
        raise HTTPException(status_code=404, detail=f"Unknown STU3 template '{request.template_name}'")
    data = request.data if isinstance(request.data, str) else json.dumps(request.data)
    return _render(stu3_renderer, request.template_name, data)
