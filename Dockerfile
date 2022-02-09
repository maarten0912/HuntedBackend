FROM python:3.10

WORKDIR /usr/src/app

COPY requirements.txt ./requirements.txt

RUN python -m pip install -r requirements.txt

COPY . .

CMD ["python", "app.py"]