FROM python:3

RUN mkdir /data
WORKDIR /data/

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD [ "python", "-u", "app/routes.py" ]