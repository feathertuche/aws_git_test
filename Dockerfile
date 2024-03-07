FROM python:3.10

# Set environment variables
ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

# Set working directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Copy environment file
COPY .env /app/.env

# Expose the port your app runs on
EXPOSE 8000

# Command to run your application
CMD ["gunicorn", "--reload", "--bind", "0.0.0.0:8000", "merge_integration.wsgi:application"]
#CMD ["python", "manage.py", "runserver" , "0.0.0.0:8000"]



