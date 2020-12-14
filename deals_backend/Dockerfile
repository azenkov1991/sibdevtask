FROM python:3
ENV PYTHONUNBUFFERED=1
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir  -r requirements.txt
COPY . .
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", ":8080", "--workers", "3", "config.wsgi:application"]
EXPOSE 8080