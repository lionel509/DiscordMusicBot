# Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot source code
COPY . .

# Expose any ports if needed (e.g., if Ollama API is hosted in the container)
# EXPOSE 11434

# Start the bot
CMD ["python", "main.py"]
