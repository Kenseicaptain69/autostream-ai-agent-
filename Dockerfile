FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY Requirements.txt .
RUN pip install --no-cache-dir -r Requirements.txt

# Copy application code
COPY . .

# Expose ports: 8000 (FastAPI) + 8501 (Streamlit)
EXPOSE 8000 8501

# Default: run FastAPI backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
