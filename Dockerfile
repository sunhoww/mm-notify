FROM docker.io/python:3.12-alpine

WORKDIR /app
COPY requirements.txt app.py /app/
RUN pip install -r requirements.txt

CMD [ "python", "app.py" ]
