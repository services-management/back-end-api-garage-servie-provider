# ----------------------------------------------------
# 1. BASE IMAGE
# Use a slim, stable base image for your language.
# For Python, use python:3.11-slim-buster or similar.
FROM python:3.11-slim-bookworm

# ----------------------------------------------------
# 2. ENVIRONMENT
# Set environment variables, crucial for non-root users and locale
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /usr/src/app

# ----------------------------------------------------
# 3. WORK DIRECTORY
# Set the working directory inside the container
WORKDIR /usr/src/app

# ----------------------------------------------------
# 4. INSTALL DEPENDENCIES
# Copy requirements file first to take advantage of Docker layer caching.
# This keeps the image build fast if only the code changes, not dependencies.
COPY requirements.txt $APP_HOME/
# Install dependencies.
# psycopg2 (the library that caused your original error) often requires 
# postgres development libraries to be installed first.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get purge -y --auto-remove build-essential gcc && \
    rm -rf /var/lib/apt/lists/*

# ----------------------------------------------------
# 5. COPY APPLICATION CODE
# Copy the rest of your application source code into the container
COPY  . /usr/src/app
# ----------------------------------------------------
# 6. EXPOSE PORT
# Specify the port the application runs on (matches the port in docker-compose.yml)
EXPOSE 8000

# ----------------------------------------------------
# 7. COMMAND TO RUN THE APPLICATION
# Define the command to start your application.
# Replace 'gunicorn' or 'python app.py' with your specific startup command.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
# OR a simpler Python/Flask app:
# CMD ["python", "app.py"]