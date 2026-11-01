FROM python:3.11-alpine

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache gcc musl-dev libpq-dev postgresql-dev

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies
RUN apk del gcc musl-dev libpq-dev postgresql-dev

# Copy application code
COPY . .

EXPOSE 8000

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
