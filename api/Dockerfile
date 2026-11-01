FROM python:3.11-alpine

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_PROGRESS_BAR=off

# Install build dependencies
RUN apk add --no-cache --virtual .build-deps gcc musl-dev libpq-dev postgresql-dev

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to save space
RUN apk del .build-deps

COPY . .

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["alembic", "upgrade", "head", "&", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
