# STAGE 1: Build React Frontend
FROM node:18-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# STAGE 2: Build Python Backend
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies for ChromaDB/PDF processing
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all source code (including main.py and server.py)
COPY . .

# Move the React build output into the 'static' folder for FastAPI
COPY --from=build /app/dist ./static

# Cloud Run sets the PORT environment variable automatically
ENV PORT=8080
EXPOSE 8080

# The CMD must run the Python server, not Nginx
CMD ["python", "server.py"]