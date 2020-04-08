FROM python:3

WORKDIR /usr/src/app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 5000

CMD ["./run.sh"]
