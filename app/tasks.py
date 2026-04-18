from app.celery_app import celery_app
from worker.jobs import cpu_heavy_scan
from app.store import set_task, get_task  # 🔥 Redis-backed state
import time
from datetime import datetime


@celery_app.task(bind=True)
def run_scan(self, number: int):
    """
    Celery task wrapper with real-time logs
    """

    task_id = self.request.id

    # 🔥 Initialize task in Redis
    set_task(task_id, {
        "task_id": task_id,
        "status": "running",
        "logs": [],
        "result": None,
        "error": None,
        "updated_at": datetime.utcnow().isoformat(),
    })

    logs = []
    self.update_state(state="STARTED", meta={"logs": list(logs)})

    def emit_log(message: str):
        timestamp = time.strftime("%H:%M:%S")
        log_line = f"[{timestamp}] {message}"

        logs.append(log_line)

        # 🔥 sync logs to Redis
        task = get_task(task_id)
        if task:
            task["logs"].append(log_line)
            task["status"] = "running"
            task["updated_at"] = datetime.utcnow().isoformat()
            set_task(task_id, task)

        self.update_state(
            state="STARTED",
            meta={"logs": list(logs)}
        )

        time.sleep(0.05)

    try:
        emit_log("Initializing scan...")
        result = cpu_heavy_scan(number, emit_log=emit_log)
        emit_log("Finalizing computation...")
        emit_log("Task completed successfully")

        # 🔥 mark completed in Redis
        task = get_task(task_id)
        if task:
            task["status"] = "completed"
            task["updated_at"] = datetime.utcnow().isoformat()
            task["result"] = {
                "input": number,
                "result": result,
                "message": f"Scan completed for number={number}",
            }
            set_task(task_id, task)

        return task["result"] if task else None

    except Exception as e:
        timestamp = time.strftime("%H:%M:%S")
        error_msg = f"[{timestamp}] ERROR: {str(e)}"
        logs.append(error_msg)

        # 🔥 sync failure to Redis
        task = get_task(task_id)
        if task:
            task["status"] = "failed"
            task["updated_at"] = datetime.utcnow().isoformat()
            task["error"] = str(e)
            task["logs"].append(error_msg)
            set_task(task_id, task)

        self.update_state(
            state="FAILURE",
            meta={"logs": list(logs)}
        )

        raise
