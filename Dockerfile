FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt /app/

RUN groupadd -r non-root && useradd -r -g non-root non-root -m
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app

RUN chown -R non-root:non-root /app
RUN mkdir -p /home/non-root/.cache/pip /home/non-root/.local && chown -R non-root:non-root /home/non-root
USER non-root
CMD ["python", "get_emails.py"]
