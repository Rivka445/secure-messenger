# Dockerfile for Secure Messenger (FastAPI backend)
# Uses a slim Python image and installs requirements
FROM python:3.11-slim

# Prevents Python from writing pyc files to disk and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# system deps for some packages
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential libffi-dev gcc git \
    && rm -rf /var/lib/apt/lists/*

# copy requirements and install
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# copy app source
COPY . /app

# expose default uvicorn port
EXPOSE 8000

# default command
CMD ["uvicorn", "server.main:app", "--host", "0.0.0.0", "--port", "8000"]
