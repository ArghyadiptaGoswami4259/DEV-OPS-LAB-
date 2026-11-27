# DevOps Lab 4 Application Image
# Student: Arghyadipta Goswami | Roll: 2301010192 | Section: C
# Subject: DEV OPS AUTOMATION | Year: 2023-2027

FROM python:3.14-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
EXPOSE 5004
CMD ["python", "app.py"]
