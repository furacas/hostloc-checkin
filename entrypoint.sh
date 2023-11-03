#!/bin/bash

RUN_CRON=${RUN_CRON:-"true"}

if [ "$RUN_CRON" = "true" ]; then
  CRON_SCHEDULE=${CRON_EXPRESSION:-"0 10 4 * *"}
  echo "$CRON_SCHEDULE /usr/bin/python3 /app/script.py >> /dev/stdout 2>&1" | crontab -
  cron -f
else
  /usr/bin/python3 /app/checkin.py
fi
