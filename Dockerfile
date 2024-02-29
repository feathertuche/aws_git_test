FROM python:3.11
 
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    patch \
    && rm -rf /var/lib/apt/lists/*

# Download and apply the patch for the AOM library
RUN wget https://aomedia.googlesource.com/aom/+/7ae7bef246e85c8f349513d668b4571c79a43c5c && \
    patch -p0 < aom_patch.diff
 
COPY requirements.txt .
 
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .

COPY .env /app/merge_integration/.env

EXPOSE 8000
 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]