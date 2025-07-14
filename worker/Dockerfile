FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

WORKDIR /app

# Install dependencies
COPY redis-req.txt .
RUN pip install --no-cache-dir -r redis-req.txt

# Copy shared + worker code
# COPY ../shared/ ./shared/
COPY worker.py .

CMD ["python", "worker.py"]
