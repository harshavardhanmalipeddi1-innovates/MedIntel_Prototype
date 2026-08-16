FROM python:3.12.13-slim@sha256:229a2c5bfa27522db7815ea81f9bed70af17ccb9de9fc7ad142b1877b5830d36

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

COPY backend/requirements.txt /app/backend/requirements.txt
COPY backend/constraints.txt /app/backend/constraints.txt

RUN pip install --no-cache-dir -r /app/backend/requirements.txt -c /app/backend/constraints.txt

COPY backend/app /app/backend/app
COPY backend/services /app/backend/services
COPY backend/knowledge /app/backend/knowledge
COPY backend/models /app/backend/models
COPY prompts /app/prompts

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]