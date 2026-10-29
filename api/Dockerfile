FROM python:3.11-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
# Install without parallel processing to avoid threading issues
RUN pip install --no-cache-dir --no-parallel -r requirements.txt

COPY . .

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
