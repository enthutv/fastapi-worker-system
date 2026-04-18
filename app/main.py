import logging

import asyncio
from fastapi import WebSocket, WebSocketDisconnect

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.logging_config import setup_logging
from app.models import ScanRequest, TaskResponse, TaskStatusResponse
from app.tasks import run_scan
from app.celery_app import celery_app
from app.store import set_task
from app.store import get_all_tasks

setup_logging()
logger = logging.getLogger("app.main")


app = FastAPI(
    title="FastAPI Worker System",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 🔥 allow all for WebSocket dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    logger.info("Root endpoint called")
    return {"message": "FastAPI Worker System is running"}


@app.post("/scan")
async def start_scan(number: int):
    logger.info("Received /scan request number=%s", number)

    task = run_scan.delay(number)

    # 🔥 Initialize task in Redis (shared state)
    set_task(task.id, {
        "task_id": task.id,
        "status": "pending",
        "logs": [],
        "result": None,
        "error": None,
    })

    return {"task_id": task.id}


@app.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_status(task_id: str):
    logger.info("Received /status request task_id=%s", task_id)

    task = celery_app.AsyncResult(task_id)

    if task.state == "PENDING":
        return TaskStatusResponse(
            task_id=task_id,
            status="pending"
        )

    elif task.state == "STARTED":
        return TaskStatusResponse(
            task_id=task_id,
            status="running"
        )

    elif task.state == "SUCCESS":
        return TaskStatusResponse(
            task_id=task_id,
            status="completed",
            result=task.result
        )

    elif task.state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status="failed",
            error=str(task.result)
        )

    return TaskStatusResponse(task_id=task_id, status=task.state)


# WebSocket endpoint for monitoring task status
@app.websocket("/ws/task/{task_id}")
async def websocket_task_status(websocket: WebSocket, task_id: str):
    await websocket.accept()
    logger.info("WebSocket connected task_id=%s", task_id)

    try:
        while True:
            task = celery_app.AsyncResult(task_id)

            # Map Celery state to unified structure
            if task.state == "PENDING":
                status = "pending"
                result = None
                error = None
            elif task.state == "STARTED":
                status = "running"
                result = None
                error = None
            elif task.state == "SUCCESS":
                status = "completed"
                result = task.result
                error = None
            elif task.state == "FAILURE":
                status = "failed"
                result = None
                error = str(task.result)
            else:
                status = task.state
                result = None
                error = None

            # 🔥 FIX: Read logs from Celery task meta (task.info)
            logs = task.info.get("logs", []) if task.info else []

            payload = {
                "task_id": task_id,
                "status": status,
                "result": result,
                "error": error,
                "logs": logs,
            }

            await websocket.send_json(payload)

            if status in ["completed", "failed"]:
                break

            await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected task_id=%s", task_id)

    except Exception as exc:
        logger.exception("WebSocket error task_id=%s error=%s", task_id, exc)
        try:
            await websocket.send_text(
                json.dumps(
                    {
                        "task_id": task_id,
                        "status": "failed",
                        "result": None,
                        "error": "WebSocket monitoring error",
                    }
                )
            )
        except Exception:
            pass

    finally:
        try:
            await websocket.close()
        except Exception:
            pass


# 🔥 NEW STABLE: Global WebSocket endpoint for ALL tasks (safe + non-crashing)

@app.websocket("/ws/tasks")
async def websocket_tasks(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connected (global tasks)")

    try:
        while True:
            try:
                # 🔥 Read all tasks from Redis (single source of truth)
                tasks_list = get_all_tasks() or []

                # 🔥 Send as plain array (frontend supports both formats)
                await websocket.send_json(tasks_list)

                # 🔥 Throttle loop to avoid CPU spikes
                await asyncio.sleep(1)

            except RuntimeError as send_error:
                logger.warning("Stopping global WebSocket send loop: %s", send_error)
                break
            except Exception as loop_error:
                logger.warning("[WS LOOP ERROR]: %s", loop_error)
                await asyncio.sleep(1)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected (global tasks)")

    except Exception as exc:
        logger.exception("Global WebSocket fatal error: %s", exc)

    finally:
        try:
            if websocket.client_state.name != "DISCONNECTED":
                await websocket.close()
        except Exception:
            pass