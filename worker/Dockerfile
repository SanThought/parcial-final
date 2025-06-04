# worker/Dockerfile
FROM python:3.11-slim
WORKDIR /app

# 1. Copy and install dependencies; if the first pip install
#    fails (e.g. DNS hiccup), retry once via the simple mirror.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
 || (echo "Primary PyPI failed—retrying via simple mirror…" \
     && pip install --no-cache-dir -i https://pypi.python.org/simple -r requirements.txt)

# 2. Copy the worker code
COPY worker.py .

# 3. Run the worker
CMD ["python", "worker.py"]

