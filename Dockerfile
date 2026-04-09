# Use an official lightweight Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install dependencies required for the project
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Set default port (Railway overrides this with its own dynamically assigned port)
ENV PORT=8000

# Expose the default port (useful for local development)
EXPOSE 8000

# Run the FastAPI application using the main.py entry point. 
# It correctly falls back to utilizing the PORT environment variable via os.environ.get("PORT") 
CMD ["python", "main.py"]
