FROM python:3

RUN apt-get update && apt-get upgrade -y
RUN pip install --upgrade pip setuptools

ARG root_dir=/jarxiv

WORKDIR $root_dir
COPY . $root_dir

RUN pip install -r requirements.txt

CMD ["python", "./run.py"]
