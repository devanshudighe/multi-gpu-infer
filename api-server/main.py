from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from data_model import VideoGenerationRequest, JobStatusResponse, JobStatusEnum, JobSummary
import uuid
import os
import redis
import rq
import json
from worker import generate_video_job

REDIS_HOST = "redis"
REDIS_PORT = 6379

app = FastAPI()

MODEL_SERVER_URL = "http://model-server-service:8000/submit"
OUTPUT_DIR = "/scratch/generated"
os.makedirs(OUTPUT_DIR, exist_ok=True)

r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
queue = rq.Queue("video-jobs", connection=r, default_timeout=1200)

@app.post("/generate", response_model=dict)
async def submit_video_generation(request: VideoGenerationRequest):
    job_id = str(uuid.uuid4())
    queue.enqueue(generate_video_job, job_id, request.text)

    # Save job status in Redis hash
    r.hset(f"job:{job_id}", mapping={
        "status": JobStatusEnum.pending,
        "prompt": request.text,
        "result_path": "",
        "error": ""
    })

    return {"message": "Video Generation job submitted.", "job_id": job_id}

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def check_job_status(job_id: str):
    job_data = r.hgetall(f"job:{job_id}")
    if not job_data:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job_id,
        "status": job_data.get("status"),
        "result_url": f"/download/{job_id}" if job_data.get("status") == JobStatusEnum.completed else None,
        "error": job_data.get("error") or None,
    }

@app.get("/download/{job_id}")
async def download_video(job_id: str):
    job_data = r.hgetall(f"job:{job_id}")
    if not job_data or job_data.get("status") != JobStatusEnum.completed:
        raise HTTPException(status_code=400, detail="Video not available")

    return FileResponse(
        path=job_data["result_path"],
        media_type="video/mp4",
        filename=f"{job_id}.mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="{job_id}.mp4"'
        }
    )

@app.get("/jobs", response_model=list[JobSummary])
async def list_all_jobs():
    keys = r.keys("job:*")
    summaries = []
    for key in keys:
        job_id = key.split(":")[1]
        data = r.hgetall(key)
        summaries.append(JobSummary(job_id=job_id, status=data.get("status")))
    return summaries
