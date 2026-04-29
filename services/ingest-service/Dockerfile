FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Create user and switch to it (security best practice)
RUN addgroup --system app && adduser --system --ingroup app app

# Copy requirements.txt first to leverage Docker cache
COPY requirements.txt .

# Install dependencies from the requirements file
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code into the container
COPY app ./app

# Copy the .env file so that environment variables are available in the container
COPY .env .env

# Switch to the non-root user
USER app

# Expose the port your app will run on
EXPOSE 8002

# Command to run the app with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8002"]