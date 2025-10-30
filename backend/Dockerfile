FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN python -m pip install --upgrade pip
RUN pip install gunicorn==20.1.0 --no-cache-dir
RUN pip install -r requirements.txt --no-cache-dir

# COPY ../docs/* /app/backend_static/docs
COPY . .
CMD ["sh", "entrypoint.sh"]