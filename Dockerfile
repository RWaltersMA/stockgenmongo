FROM python:3

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py ./
COPY *.txt ./

ENTRYPOINT ["python", "./stockgen.py"]
CMD [ "-s","5", "-c", "mongodb://mongo1:27017/?replicaSet=rs0" ]
