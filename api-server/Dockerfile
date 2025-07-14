FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/app"

WORKDIR /app

# Install dependencies
COPY redis-req.txt .
RUN pip install --no-cache-dir -r redis-req.txt

# Copy API code + shared code
COPY main.py .
COPY data_model.py .
COPY worker.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
