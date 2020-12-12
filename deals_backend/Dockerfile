FROM python:3
ENV PYTHONUNBUFFERED=1
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir  -r requirements.txt
COPY . .
ENTRYPOINT ["/app/entrypoint.sh"]
EXPOSE 8080