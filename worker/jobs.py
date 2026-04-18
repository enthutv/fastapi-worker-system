from time import sleep


FAILURE_TRIGGER_NUMBER = 13


def cpu_heavy_scan(number: int, emit_log=None) -> dict:
    """
    Simulate a CPU-bound scan job.

    Failure path:
    - If number == FAILURE_TRIGGER_NUMBER, raise a RuntimeError so we can
      validate worker failure handling, task status updates, and logging.
    """
    def log(msg: str):
        if emit_log:
            emit_log(msg)

    log("Starting CPU-heavy scan job")

    if number < 0:
        raise ValueError("number must be >= 0")

    if number == FAILURE_TRIGGER_NUMBER:
        log("Failure condition triggered")
        raise RuntimeError(
            "Intentional worker failure triggered for testing"
        )

    log(f"Processing {number} iterations")
    total = 0

    # 🔥 Use 1-based steps for correct progress display
    for i in range(1, number + 1):
        total += (i - 1) * (i - 1)

        # Emit log at intervals + first + last
        if (
            i == 1
            or i == number
            or i % max(1, number // 10) == 0
        ):
            log(f"step {i}/{number}")
            sleep(0.3)  # allow UI to stream updates

    log("Finalizing computation")
    sleep(2)

    log("Job completed successfully")
    return {
        "input": number,
        "total": total,
        "message": f"Scan completed for number={number}",
    }