# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the application code and database files into the container
COPY . /app

# Install required Python packages
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Expose the application port (as defined in app.py)
EXPOSE 7432

# Run the application
CMD ["python", "app.py"]
