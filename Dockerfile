# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and source code
COPY requirements.txt ./
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port (adjust if your Flask app uses a different port)
EXPOSE 5000

# Set environment variables (optional)
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

# Run startup script
RUN chmod +x startup.sh
CMD ["./startup.sh"]
