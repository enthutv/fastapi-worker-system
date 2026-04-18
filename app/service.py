from __future__ import annotations

import logging
import traceback
from concurrent.futures import Future, ProcessPoolExecutor
from typing import Optional
from uuid import uuid4

from app.registry import TaskRegistry
from worker.jobs import cpu_heavy_scan


logger = logging.getLogger("app.service")


class WorkerService:
    """
    Owns task submission, task tracking, and executor lifecycle.
    """

    def __init__(self) -> None:
        self.registry = TaskRegistry()
        self.executor: Optional[ProcessPoolExecutor] = None

    def start(self) -> None:
        if self.executor is not None:
            logger.info("WorkerService already started")
            return

        self.executor = ProcessPoolExecutor()
        logger.info("ProcessPoolExecutor started")

    def shutdown(self) -> None:
        if self.executor is None:
            logger.info("WorkerService shutdown skipped: executor not initialized")
            return

        logger.info("Shutting down ProcessPoolExecutor")
        self.executor.shutdown(wait=True, cancel_futures=False)
        self.executor = None
        logger.info("ProcessPoolExecutor shutdown complete")

    def submit_scan(self, number: int) -> str:
        if self.executor is None:
            raise RuntimeError("WorkerService is not started")

        task_id = str(uuid4())
        self.registry.create_task(task_id)
        self.registry.set_running(task_id)

        logger.info("Submitting task_id=%s number=%s", task_id, number)

        future = self.executor.submit(cpu_heavy_scan, number)
        future.add_done_callback(self._build_done_callback(task_id))

        return task_id

    def get_task(self, task_id: str) -> Optional[dict]:
        return self.registry.get_task(task_id)

    def _build_done_callback(self, task_id: str):
        def _on_done(completed_future: Future) -> None:
            try:
                result = completed_future.result()
                self.registry.set_completed(task_id, result)
                logger.info("Task completed task_id=%s", task_id)
            except Exception as exc:
                error_message = str(exc)
                trace = traceback.format_exc()

                self.registry.set_failed(task_id, error_message)

                logger.error("Task failed task_id=%s error=%s", task_id, error_message)
                logger.error("Task traceback task_id=%s\n%s", task_id, trace)

        return _on_done


worker_service = WorkerService()