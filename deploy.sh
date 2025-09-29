#!/bin/bash
set -e

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
else
    echo ".env file not found. Please create one from .env.example"
    exit 1
fi

# Check required environment variables
required_vars=("DOCKER_REGISTRY" "DOCKER_IMAGE_NAME" "DOMAIN" "EMAIL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set in .env file"
        exit 1
    fi
done

# Build and push the Docker image
echo "Building Docker image..."
docker-compose -f docker-compose.prod.yml build

echo "Tagging and pushing image..."
docker tag ${DOCKER_IMAGE_NAME} ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG:-latest}
docker push ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG:-latest}

# Deploy to production server
echo "Deploying to production..."
ssh ${DEPLOY_USER}@${DEPLOY_HOST} << 'ENDSSH'
    cd ${DEPLOY_PATH}
    
    # Pull the latest changes
    git pull origin main
    
    # Stop and remove existing containers
    docker-compose -f docker-compose.prod.yml down
    
    # Get the latest image
    docker pull ${DOCKER_REGISTRY}/${DOCKER_IMAGE_NAME}:${DOCKER_TAG:-latest}
    
    # Start the services
    docker-compose -f docker-compose.prod.yml up -d
    
    # Run migrations
    docker-compose -f docker-compose.prod.yml exec web python manage.py migrate
    
    # Collect static files
    docker-compose -f docker-compose.prod.yml exec web python manage.py collectstatic --noinput
    
    # Restart the web service
    docker-compose -f docker-compose.prod.yml restart web
ENDSSH

echo "Deployment completed successfully!"
