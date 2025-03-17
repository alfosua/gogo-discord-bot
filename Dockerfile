# Use an official Python runtime as a parent image
FROM python:3.13-slim-bookworm

# Set the working directory in the container to /app
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app

# Install any dependencies specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install FFMPEG
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg

# Copy the requirements file into the container at /app
COPY src/bot.py /app
COPY .env /app

# Make port 8080 available to the world outside this container
# EXPOSE 8080 #Uncomment if your bot uses a web server

# Run bot.py when the container launches
CMD ["python", "bot.py"]