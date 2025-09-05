FROM python:3.11-slim

# Install dependencies
RUN pip install --no-cache-dir telethon requests

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Run script
CMD ["python", "main.py"]
