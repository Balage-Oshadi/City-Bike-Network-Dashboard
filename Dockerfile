# Use slim Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /usr/src/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your app code
COPY . .

# Expose port
EXPOSE 8501

# Run Streamlit app
CMD ["streamlit", "run", "DashBoardUi.py", "--server.port=8501", "--server.enableCORS=false"]
