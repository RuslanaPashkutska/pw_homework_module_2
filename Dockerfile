FROM python:3.11-slim
LABEL authors="ruslana"
WORKDIR /app
COPY . .
RUN pip install  --no-cache-dir -r requirements.txt || true

ENTRYPOINT ["python", "homework_module_2.py"]