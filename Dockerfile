FROM python:3.12-slim

# Evita file .pyc e logga subito su stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dipendenze prima (cache layer: rebuild più veloce se cambia solo il codice)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia il codice e i dati
COPY app ./app
COPY scripts ./scripts
COPY data ./data
COPY pytest.ini ./
COPY alembic.ini ./
COPY alembic ./alembic

EXPOSE 8000

# Avvio "prod-like" (niente reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
