from flask import Flask, request, render_template, redirect, url_for, send_file, Response, abort, stream_with_context
import requests
import os

app = Flask(__name__)
# app.secret_key = 'your-secret-key'
FASTAPI_BASE_URL = os.environ.get("FASTAPI_BASE_URL", "http://localhost:8000")
VIDEO_DIR = os.environ.get("VIDEO_DIR", "/scratch/generated")

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/submit", methods=["GET", "POST"])
def submit_job_form():
    if request.method == "POST":
        prompt = request.form.get("prompt")
        response = requests.post(f"{FASTAPI_BASE_URL}/generate", json={"text": prompt})
        job_id = response.json()["job_id"]
        return redirect(url_for("job_status", job_id=job_id))
    
    # GET request: render blank form
    return render_template("index.html", job=None, prompt="")

@app.route("/status/<job_id>")
def job_status(job_id):
    response = requests.get(f"{FASTAPI_BASE_URL}/status/{job_id}")
    if response.status_code != 200:
        flash("Job not found!", "error")
        return redirect(url_for("submit_job_form"))

    job = response.json()
    # Let FastAPI serve the actual file
    if job["status"] == "completed":
        job["result_url"] = url_for("download", job_id=job["job_id"])
    return render_template("index.html", job=job, prompt=job.get("prompt", ""))

@app.route("/jobs")
def list_jobs():
    page = int(request.args.get("page", 1))
    per_page = 10

    response = requests.get(f"{FASTAPI_BASE_URL}/jobs")
    jobs = response.json()
    start = (page - 1) * per_page
    end = start + per_page

    paginated_jobs = jobs[start:end]
    has_next = len(jobs) > end

    return render_template("jobs.html", jobs=paginated_jobs, page=page, has_next=has_next)

@app.route("/download/<job_id>")
def download(job_id):
    fastapi_url = f"{FASTAPI_BASE_URL}/download/{job_id}"

    # Forward the Range header from browser (important for streaming)
    headers = {}
    if "Range" in request.headers:
        headers["Range"] = request.headers["Range"]

    try:
        r = requests.get(fastapi_url, stream=True, headers=headers, timeout=120)
        r.raise_for_status()

        # Collect important headers for browser playback
        response_headers = {
            "Content-Type": r.headers.get("Content-Type", "video/mp4"),
            "Content-Length": r.headers.get("Content-Length"),
        }

        # Forward Accept-Ranges and Content-Disposition if present
        if "Accept-Ranges" in r.headers:
            response_headers["Accept-Ranges"] = r.headers["Accept-Ranges"]
        if "Content-Disposition" in r.headers:
            response_headers["Content-Disposition"] = r.headers["Content-Disposition"]

        return Response(
            stream_with_context(r.iter_content(chunk_size=8192)),
            headers=response_headers,
            status=r.status_code
        )

    except requests.RequestException as e:
        print(f"[ERROR] Download failed from FastAPI: {e}")
        abort(500, description="Internal server error")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
