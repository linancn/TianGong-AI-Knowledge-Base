FROM python:3.11.5-bullseye

# Set the working directory in the Docker image
WORKDIR /app

# Copy requirements.txt into /app/requirements.txt within the image
COPY requirements.txt requirements.txt

# Install packages using pip
RUN pip install -r requirements.txt

# Copy the current directory's content into /app in the image
COPY . .

# Execute the script
CMD ["streamlit", "run", "Home.py"]
