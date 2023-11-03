FROM ubuntu:latest

RUN apt-get update && apt-get install -y cron python3 python3-pip

WORKDIR /app

COPY entrypoint.sh /app/

COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

COPY checkin.py /app/

RUN chmod +x /app/checkin.py
RUN chmod +x /app/entrypoint.sh

RUN apt-get clean

ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

ENTRYPOINT ["/app/entrypoint.sh"]
