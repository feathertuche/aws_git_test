FROM python:3.11
 
WORKDIR /app
 
COPY requirements.txt .
 
RUN pip install --no-cache-dir -r requirements.txt
 
COPY . .

COPY .env /app/merge_integration/.env

EXPOSE 8000
 
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]