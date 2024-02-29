FROM python:3.11
 
WORKDIR /app

# Install necessary build dependencies
RUN apt-get update && \
    apt-get install -y git cmake build-essential

# Clone AOM repository
RUN git clone https://aomedia.googlesource.com/aom

# Build AOM
WORKDIR /app/aom
RUN cmake .
RUN make

# Install AOM
RUN make install

COPY requirements.txt .
 
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

COPY .env /app/merge_integration/.env

EXPOSE 8000
 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]