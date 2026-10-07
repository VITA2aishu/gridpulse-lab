FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY telemetry_logs.py receiver.py gunicorn.conf.py ./
USER 65532:65532
CMD ["gunicorn", "--config", "gunicorn.conf.py", "receiver:application"]
