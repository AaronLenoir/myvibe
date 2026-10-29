FROM python:3.11-bookworm

WORKDIR /app

# Fix threading issues
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
