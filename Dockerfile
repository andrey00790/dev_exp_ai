FROM python:3.11-slim

# Установим системные зависимости
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    libpq-dev \
    python3-dev \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONPATH=/code
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
