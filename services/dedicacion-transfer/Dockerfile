# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# .env excluido vía .dockerignore: la configuración llega por App Settings.
# En el Container App se fija LOG_DIR=/tmp/logs: el arranque escribe log de
# fichero (config/logging_config.py) y /app no tiene por qué ser escribible.
EXPOSE 8006
CMD ["python", "main.py"]
