# Stage 1: Build Vue frontend
FROM node:20-slim AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend + built frontend
FROM python:3.12-slim
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

COPY backend/requirements.txt ./
RUN uv pip install --system --no-cache -r requirements.txt

COPY backend/ ./
COPY --from=frontend-builder /frontend/dist ./static

RUN mkdir -p /app/data

EXPOSE 8888
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8888"]
