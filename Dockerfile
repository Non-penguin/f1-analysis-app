FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/ff1_cache

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
