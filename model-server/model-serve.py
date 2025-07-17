from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import torch
import uuid
import os
import asyncio
from typing import Dict
from threading import Lock
from diffusers import DiffusionPipeline
from diffusers.utils import export_to_video

MODEL_PATH = "/app/mochi-1-preview"
OUTPUT_DIR = "/scratch/generated"
GPUS_PER_PIPE = 2  # Each replica gets 2 GPUs

class PromptRequest(BaseModel):
    prompt: str

app = FastAPI()

# GPU pipeline pool
pipeline_pool: Dict[int, DiffusionPipeline] = {}
pipeline_locks: Dict[int, Lock] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[Model-Serve] Starting up. Loading pipelines on available GPUs...")
    num_gpus = torch.cuda.device_count()
    if num_gpus == 0:
        print("[Model-Serve] No GPUs found. Exiting.")
        yield
        return

    for gpu_id in range(num_gpus):
        print(f"[Model-Serve] Loading pipeline on GPU {gpu_id}")
        try:
            pipe = DiffusionPipeline.from_pretrained(
                MODEL_PATH,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                local_files_only=True
            )
            pipe.to(f"cuda:{gpu_id}")
            pipeline_pool[gpu_id] = pipe
            pipeline_locks[gpu_id] = Lock()
        except Exception as e:
            print(f"[Model-Serve] Failed to load pipeline on GPU {gpu_id}: {e}")
    yield
    print("[Model-Serve] Shutting down. Cleaning up.")

app.router.lifespan_context = lifespan

def run_inference(prompt: str):
    for gpu_id, lock in pipeline_locks.items():
        if lock.acquire(blocking=False):
            try:
                print(f"[Model-Serve] Running inference on GPU {gpu_id}")
                pipe = pipeline_pool[gpu_id]
                result = pipe(prompt=prompt, num_frames=60)
                frames = result.frames[0] if hasattr(result, "frames") else result["frames"]
                return frames
            finally:
                lock.release()
    raise RuntimeError("All GPUs are currently busy. Please try again shortly.")

@app.post("/submit")
async def submit_video(req: PromptRequest):
    try:
        job_id = str(uuid.uuid4())
        output_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")
        frames = run_inference(req.prompt)
        export_to_video(frames, output_path, fps=8)
        return {"status": "success", "video_path": output_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
