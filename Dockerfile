FROM python:latest

WORKDIR /usr/src/app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY *.txt ./

ENTRYPOINT ["python", "./stockgen.py"]
