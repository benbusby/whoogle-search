FROM python:3.8-slim

WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y build-essential libcurl4-openssl-dev libssl-dev
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x ./whoogle-search

EXPOSE 5000

CMD ["./whoogle-search"]
