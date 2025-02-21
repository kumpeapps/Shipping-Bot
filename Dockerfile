FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/
COPY crontab_file /etc/cron.d/my_cron
RUN apt-get update && apt-get install -y cron
RUN apt-get clean
# Note: If additional files required for dependency installation (e.g., setup.py, pyproject.toml) are needed,
# copy them here to maintain efficient caching.
RUN pip install --no-cache-dir -r requirements.txt
RUN service cron start
COPY . /app
RUN chmod 0644 /etc/cron.d/my_cron
RUN crontab /etc/cron.d/my_cron

CMD [ "cron", "-f" ]