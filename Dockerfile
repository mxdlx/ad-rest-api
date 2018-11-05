FROM python:2.7.15-stretch
MAINTAINER aaraujo@protonmail.ch

RUN apt-get update && apt-get install -y libldap2-dev libsasl2-dev && rm -rf /var/cache/apt

WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . ./

CMD ["python", "./main.py"]
