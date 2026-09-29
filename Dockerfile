# 1. Base Image: Lightweight Python 3.11 Linux runtime
FROM python:3.11-slim

# 2. Set working directory inside the container
WORKDIR /app

# 3. Copy dependency requirements first (optimizes Docker layer caching)
COPY requirements.txt .

# 4. Install dependencies without caching build files
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy remaining application source code into container
COPY . .

# 6. Expose port 5000 (Documentation layer for container network)
EXPOSE 5000

# 7. Default execution command when container starts
CMD ["python", "app.py"]