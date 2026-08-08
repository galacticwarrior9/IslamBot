FROM python:3.10-slim

WORKDIR /app

# Ensure we have essential tools if any python package requires compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run unbuffered so logs output instantly to docker
CMD ["python", "-u", "main.py"]
