FROM python:3

RUN mkdir /data
WORKDIR /data/

RUN apt-get update && apt-get -y upgrade && apt-get install -y wkhtmltopdf default-libmysqlclient-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# COPY ./app ./app

CMD [ "python", "-u", "app/run.py" ]
