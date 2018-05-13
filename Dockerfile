FROM python:3.6.3

RUN mkdir -p /app/app /app/packages
WORKDIR /app/app

# copy app
COPY . /app/app/
COPY requirements.txt /app/app/
RUN pip install --src /app/packages --no-cache-dir -r requirements.txt
EXPOSE 5000

CMD ["./run_app.sh"]
