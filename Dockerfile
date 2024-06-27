# Stage 1: Build the application
FROM python:3.10 AS builder

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Compile your application if needed (e.g., for Django)
# RUN python manage.py makemigrations && python manage.py migrate

# Stage 2: Setup the runtime environment
FROM python:3.10-slim AS runtime

# Create a non-root user
RUN useradd -ms /bin/bash appuser

# Switch to the non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Copy the application from the builder stage
COPY --from=builder /app /app

# Copy environment file
COPY .env /app/.env

# Expose the port your app runs on
EXPOSE 8000

# Command to run your application
CMD ["gunicorn", "--reload", "--bind", "0.0.0.0:8000", "merge_integration.wsgi:application"]
#CMD ["python", "manage.py", "runserver" , "0.0.0.0:8000"]
