FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PILE_METER_ROOT=/workspace

WORKDIR /workspace

COPY backend /workspace/backend
RUN python -m pip install --no-cache-dir "/workspace/backend[api]"

RUN mkdir -p /workspace/runtime /workspace/models

EXPOSE 8000

CMD ["uvicorn", "pile_meter.interfaces.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
