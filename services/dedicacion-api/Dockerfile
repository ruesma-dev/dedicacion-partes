# Dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# .env excluido vía .dockerignore: la configuración llega por App Settings
EXPOSE 8090
CMD ["python", "main.py"]
