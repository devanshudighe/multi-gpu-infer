import os
import requests
import redis
from rq import Worker, Queue

import sys
sys.stdout.reconfigure(line_buffering=True)

# Redis connection
redis_conn = redis.Redis(host="redis", port=6379, decode_responses=False)
queue_name = "video-jobs"

MODEL_SERVER_URL = "http://model-server-service:8000/submit"

def generate_video_job(job_id: str, prompt: str):
    print(f"[Worker] Starting job {job_id} with prompt: {prompt}")
    
    job_key = f"job:{job_id}"
    try:
        redis_conn.hset(job_key, "status", "processing")
        
        response = requests.post(MODEL_SERVER_URL, json={"prompt": prompt}, timeout=600)
        response.raise_for_status()

        result_path = response.json().get("video_path", "")
        if not result_path:
            raise Exception("No video_path in model-server response")

        redis_conn.hset(job_key, mapping={
            "status": "completed",
            "result_path": result_path,
            "error": ""
        })
        print(f"[Worker] Job {job_id} completed. Output: {result_path}")

    except Exception as e:
        error_msg = str(e)
        redis_conn.hset(job_key, mapping={
            "status": "failed",
            "error": error_msg
        })
        print(f"[Worker] Job {job_id} failed: {error_msg}")

# Worker bootstrap
if __name__ == "__main__":
    queue = Queue(name=queue_name, connection=redis_conn)
    worker = Worker(queues=[queue], connection=redis_conn)
    print("[Worker] Waiting for jobs...")
    worker.work()
