# Use slim Python for backend + static
FROM python:3.11-slim

# Install dependencies
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend /app/backend
# Copy frontend static assets
COPY frontend /app/frontend

# Expose port and set env defaults
ENV PORT=8080
EXPOSE 8080

# Launch uvicorn, serving FastAPI app in backend/main.py
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8080"]
