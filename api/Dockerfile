FROM python:3.11-bookworm

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_PROGRESS_BAR=off

COPY requirements.txt .
# Install packages one at a time to avoid threading issues
RUN pip install --no-cache-dir fastapi==0.109.0 && \
    pip install --no-cache-dir uvicorn[standard]==0.27.0 && \
    pip install --no-cache-dir sqlalchemy==2.0.25 && \
    pip install --no-cache-dir asyncpg==0.29.0 && \
    pip install --no-cache-dir python-jose[cryptography]==3.3.0 && \
    pip install --no-cache-dir passlib[bcrypt]==1.7.4 && \
    pip install --no-cache-dir authlib==1.3.0 && \
    pip install --no-cache-dir httpx==0.26.0 && \
    pip install --no-cache-dir python-dateutil==2.8.2

COPY . .

RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
