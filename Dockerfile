FROM python:3.11

# Set working directory
WORKDIR /app

# Install necessary build dependencies
RUN apt-get update && \
    apt-get install -y git cmake build-essential

# Clone AOM repository
RUN git clone --branch v3.8.1 https://aomedia.googlesource.com/aom

# Build AOM
WORKDIR /app/aom
RUN mkdir build && cd build && \
    cmake .. && \
    make && \
    make install

# Switch back to the app directory
WORKDIR /app

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy your application code
COPY . .

# Copy environment file
COPY .env /app/merge_integration/.env

# Expose the port your app runs on
EXPOSE 8000

# Command to run your application
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
