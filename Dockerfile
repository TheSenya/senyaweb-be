# Use official Python runtime as base image
# python:3.11-slim is a lightweight version with only essential packages
FROM python:3.11-slim

# Set working directory inside the container
# All subsequent commands will run from this directory
WORKDIR /app

# Copy requirements.txt from your local machine to the container
# This file should list all your Python dependencies
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces image size by not storing pip cache
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application code into the container
# The . means copy everything from current directory
COPY . .

# Expose port 8000 (FastAPI's default port)
# This documents which port the app uses (doesn't actually open it)
EXPOSE 8000

# Command to run when the container starts
# uvicorn is the ASGI server that runs FastAPI
# 0.0.0.0 means listen on all network interfaces
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]