FROM python:3.11-slim

WORKDIR /app
COPY frontend /app/frontend

EXPOSE 8501

CMD ["python", "/app/frontend/web_server.py"]
