
FROM python:3.11-alpine

WORKDIR /

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

COPY . .

# CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--reload"]
