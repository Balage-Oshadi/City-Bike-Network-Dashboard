# Use slim Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /usr/src/app

# Install dependencies required by WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libssl-dev \
    libffi-dev \
    libxrender1 \
    libxext6 \
    libx11-dev \
    libjpeg-dev \
    libpng-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    fonts-liberation \
    fonts-dejavu \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Expose port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "DashBoardUi.py", "--server.port=8501", "--server.enableCORS=false"]
