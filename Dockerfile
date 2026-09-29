FROM node:22.22.0-bookworm AS frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
COPY frontend/.npmrc ./
COPY frontend/scripts/validate-node-version.mjs ./scripts/
RUN npm install --global npm@11.7.0 \
    && npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
ENV PRINTORA_DATA_DIR=/data
ENV PRINTORA_FRONTEND_DIST_DIR=/app/frontend/dist
COPY backend/ ./backend/
COPY --from=frontend-build /app/frontend/dist ./frontend/dist
RUN pip install --no-cache-dir -e ./backend
EXPOSE 8069
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8069"]
