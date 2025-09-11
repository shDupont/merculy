# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and source code
COPY requirements.txt ./
COPY . .


# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt \
	&& python -m nltk.downloader punkt

# Expose port (adjust if your Flask app uses a different port)
EXPOSE 5000

# Make sure startup.sh is executable
RUN chmod +x startup.sh

# Run the startup script
CMD ["./startup.sh"]