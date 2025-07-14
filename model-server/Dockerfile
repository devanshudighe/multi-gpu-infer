FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04

# Install system packages
RUN apt-get update && apt-get install -y \
    python3.10 python3-pip git \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Set Python 3.10 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.10 1

WORKDIR /app

COPY requirements.txt .

RUN pip3 install --no-cache-dir -r requirements.txt

COPY model-serve.py .

CMD ["uvicorn", "model-serve:app", "--host", "0.0.0.0", "--port", "8000"]