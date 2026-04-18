from threading import Lock
from typing import Any, Optional


class TaskRegistry:
    """
    In-memory task registry for Phase 1.

    Structure:
    {
        task_id: {
            "status": "pending" | "running" | "completed" | "failed",
            "result": Any | None,
            "error": str | None
        }
    }
    """

    def __init__(self) -> None:
        self._tasks: dict[str, dict[str, Any]] = {}
        self._lock = Lock()

    def create_task(self, task_id: str) -> None:
        with self._lock:
            self._tasks[task_id] = {
                "status": "pending",
                "result": None,
                "error": None,
            }

    def set_running(self, task_id: str) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "running"

    def set_completed(self, task_id: str, result: Any) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "completed"
                self._tasks[task_id]["result"] = result
                self._tasks[task_id]["error"] = None

    def set_failed(self, task_id: str, error: str) -> None:
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id]["status"] = "failed"
                self._tasks[task_id]["error"] = error
                self._tasks[task_id]["result"] = None

    def get_task(self, task_id: str) -> Optional[dict[str, Any]]:
        with self._lock:
            task = self._tasks.get(task_id)
            if task is None:
                return None
            return dict(task)
