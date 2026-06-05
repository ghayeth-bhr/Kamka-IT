FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.3.1+cpu
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/evaluation/

EXPOSE 7860

CMD ["python", "-m", "evaluation.evaluator"]
