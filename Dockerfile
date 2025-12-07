# 1. Base Image
# Use a Python base image (adjust version if needed)
FROM python:3.11-slim

# 2. Set Working Directory
# This is where your code will live inside the container
WORKDIR /usr/src/app

# 3. Copy and Install Dependencies
# Copy only the requirements file first to utilize Docker's build cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy Application Code
# Copy the rest of your project files
COPY . .

# 5. Define Startup Command
# Replace 'python app.py' with your application's actual startup command
CMD ["python", "main.py"]