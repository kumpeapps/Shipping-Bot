FROM python:3.11-slim-bookworm
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/

# Note: If additional files required for dependency installation (e.g., setup.py, pyproject.toml) are needed,
# copy them here to maintain efficient caching.
RUN pip install --no-cache-dir -r requirements.txt
RUN service cron start
COPY . /app
RUN /app/get_emails.py
