import os

import uvicorn
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from . import events as events_lib
from .backend import PythonModelService, TritonService
from .models import ChoiceEvent, CompletionRequest, CompletionResponse

app = FastAPI(
    title="TabbyServer",
    description="TabbyServer is the backend for tabby, serving code completion requests from code editor / IDE.",
    docs_url="/",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL_NAME = os.environ.get("MODEL_NAME")
MODEL_BACKEND = os.environ.get("MODEL_BACKEND", "python")

if MODEL_BACKEND == "triton":
    model_backend = TritonService(
        tokenizer_name=MODEL_NAME,
        host=os.environ.get("TRITON_HOST", "triton"),
        port=os.environ.get("TRITON_PORT", "8001"),
    )
else:
    model_backend = PythonModelService(MODEL_NAME)

LOGS_DIR = os.environ.get("LOGS_DIR", None)
if LOGS_DIR is not None:
    events_lib.setup_logging(os.path.join(LOGS_DIR, "tabby-server"))


@app.post("/v1/completions")
async def completions(request: CompletionRequest) -> CompletionResponse:
    response = model_backend(request)
    events_lib.log_completion(request, response)
    return response


@app.post("/v1/events")
async def events(e: ChoiceEvent) -> JSONResponse:
    events_lib.log_event(e)
    return JSONResponse(content="ok")
