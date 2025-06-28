FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

USER non-root
RUN chown -R non-root:non-root /app
CMD ["python", "get_emails.py"]
