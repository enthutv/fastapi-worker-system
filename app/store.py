import redis
import json

r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

def set_task(task_id, data):
    r.set(f"task:{task_id}", json.dumps(data))

def get_task(task_id):
    data = r.get(f"task:{task_id}")
    return json.loads(data) if data else None

def get_all_tasks():
    keys = r.keys("task:*")
    return [json.loads(r.get(k)) for k in keys]
