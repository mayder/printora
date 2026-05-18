FROM node:22-bookworm AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
ENV MAYDER_PRINT_LAB_DATA_DIR=/data
ENV MAYDER_PRINT_LAB_FRONTEND_DIST_DIR=/app/frontend/dist
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
RUN pip install --no-cache-dir -e ./backend
EXPOSE 8085
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8085"]
