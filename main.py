from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator

import repository


@asynccontextmanager
async def lifespan(app: FastAPI):
    repository.init_db()  # table + seed rows are created on first start only
    yield


app = FastAPI(title="Task API", version="3.0", lifespan=lifespan)


# --- models (unchanged from Assignments 1 and 2) --------------------------------

class TaskCreate(BaseModel):
    title: str

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("title must not be empty")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("title must not be empty")
        return v


def not_found(task_id: int) -> HTTPException:
    return HTTPException(status_code=404, detail=f"Task {task_id} not found")


# --- root & health ---------------------------------------------------------------

@app.get("/")
def root():
    return {"name": "Task API", "version": "3.0", "endpoints": ["/tasks"]}


@app.get("/health")
def health():
    return {"status": "ok"}


# --- error handling (same JSON shape as before) ------------------------------------

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    field = ".".join(str(p) for p in first_error["loc"] if p != "body")
    return JSONResponse(status_code=400, content={"error": f"{field}: {first_error['msg']}"})


# --- read (SELECT) -------------------------------------------------------------------

@app.get("/tasks")
def list_tasks(done: Optional[bool] = None, search: Optional[str] = None):
    return repository.list_tasks(done, search)


@app.get("/tasks/{task_id}")
def get_task(task_id: int):
    task = repository.get_task(task_id)
    if task is None:
        raise not_found(task_id)
    return task


# --- create, update, delete (INSERT / UPDATE / DELETE) ----------------------------------

@app.post("/tasks", status_code=201)
def create_task(payload: TaskCreate):
    return repository.create_task(payload.title)


@app.put("/tasks/{task_id}")
def update_task(task_id: int, payload: TaskUpdate):
    if repository.get_task(task_id) is None:
        raise not_found(task_id)
    if payload.title is None and payload.done is None:
        raise HTTPException(status_code=400, detail="Provide at least title or done")
    return repository.update_task(task_id, payload.title, payload.done)


@app.delete("/tasks/{task_id}", status_code=204)
def delete_task(task_id: int):
    if not repository.delete_task(task_id):
        raise not_found(task_id)
    return None
