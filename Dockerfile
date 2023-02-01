FROM python:3

RUN mkdir /data
WORKDIR /data/

RUN apt-get update
RUN apt-get -y upgrade
RUN apt-get -y install wkhtmltopdf default-libmysqlclient-dev

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD [ "python", "-u", "app/routes.py" ]