FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

RUN groupadd -r non-root && useradd -r -g non-root non-root
RUN chown -R non-root:non-root /app
USER non-root
CMD ["python", "get_emails.py"]
