# Use a slim Python image
FROM python:3.9-slim

WORKDIR /app

# Install FFmpeg for audio handling
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Command to run the bot
CMD ["python", "main.py"]
