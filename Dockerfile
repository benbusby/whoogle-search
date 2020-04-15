FROM python:3

WORKDIR /usr/src/app
COPY . .

RUN pip install --no-cache-dir -r config/requirements.txt

CMD ["./run"]
