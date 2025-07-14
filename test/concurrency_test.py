import uuid
import json
import random

# Define a set of diverse, concurrency-safe prompts
prompts = [
    "a serene waterfall in a forest",
    "a cat playing with a ball of yarn",
    "robots dancing in a futuristic city",
    "a spaceship landing on Mars",
    "a medieval knight riding a dragon",
    "a timelapse of flowers blooming",
    "a group of penguins sliding on ice",
    "a sunrise over the mountains",
    "a painter creating art on a giant canvas",
    "a street market in Tokyo at night"
]

with open("concurrent_job_test.sh", "w") as f:
    for prompt in prompts:
        payload = json.dumps({"text": prompt})
        f.write(f"curl -X POST http://localhost:8000/generate -H 'Content-Type: application/json' -d '{payload}'\n")