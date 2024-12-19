FROM python:3.13-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt


EXPOSE 8100

ENV FLASK_APP=main.py
CMD ["flask", "run", "--host=0.0.0.0", "--port=8100"]
