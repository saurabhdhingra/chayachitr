# Deploying Chayachitr to AWS

This guide outlines how to deploy the Chayachitr image processing service to AWS.

## Prerequisites

- AWS account
- AWS CLI installed and configured
- Docker installed

## 1. Set Up AWS Resources

### 1.1 Create an EC2 Instance

1. Go to AWS Console → EC2
2. Click "Launch Instance"
3. Choose Amazon Linux 2023
4. Select an instance type (t2.micro for testing, t2.medium or larger for production)
5. Configure your security group to allow:
   - SSH (port 22)
   - HTTP (port 80)
   - HTTPS (port 443)
   - Custom TCP (port 8080) - our application port
6. Launch the instance with a new or existing key pair
7. Wait for the instance to be in "running" state

### 1.2 Set Up MongoDB Atlas (Alternative to self-hosting)

1. Create an account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a new cluster (free tier is sufficient for testing)
3. Set up network access to allow connections from your EC2 instance
4. Create a database user
5. Get the connection string

### 1.3 Set Up S3 Bucket (Alternative to MinIO)

1. Go to AWS Console → S3
2. Create a bucket with a unique name
3. Configure permissions to allow your application to access the bucket
4. Create an IAM user with programmatic access and S3 permissions
5. Save the access key and secret key

## 2. Prepare the EC2 Instance

1. SSH into your EC2 instance:

```
ssh -i your-key.pem ec2-user@your-ec2-public-ip
```

2. Update the system:

```
sudo yum update -y
```

3. Install Docker:

```
sudo yum install -y docker
sudo systemctl start docker
sudo systemctl enable docker
sudo usermod -aG docker ec2-user
```

4. Install Docker Compose:

```
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

5. Log out and log back in to apply the docker group changes:

```
exit
ssh -i your-key.pem ec2-user@your-ec2-public-ip
```

## 3. Deploy the Application

### 3.1 Clone and Configure the Repository

1. Install Git:

```
sudo yum install -y git
```

2. Clone the repository:

```
git clone https://github.com/yourname/chayachitr.git
cd chayachitr
```

3. Create or update the .env file with your production settings:

```
# Server Configuration
PORT=8080
ENV=production

# MongoDB Configuration (use Atlas if set up)
MONGO_URI=mongodb+srv://username:password@cluster.mongodb.net/chayachitr
DB_NAME=chayachitr

# JWT Configuration
JWT_SECRET=your_secure_secret_key
JWT_EXPIRATION=24h

# AWS S3 Configuration (if using S3 instead of MinIO)
S3_ACCESS_KEY=your_aws_access_key
S3_SECRET_KEY=your_aws_secret_key
S3_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

### 3.2 Update Storage Implementation for S3 (Optional)

If you're using S3 instead of MinIO, update your storage implementation to use the AWS SDK for S3.

### 3.3 Deploy with Docker Compose

1. Update your `docker-compose.yml` file if necessary
2. Build and start the containers:

```
docker-compose up -d
```

### 3.4 Alternative: Deploy Using Elastic Container Service (ECS)

For a more managed approach, consider using ECS:

1. Create an Elastic Container Registry (ECR) repository
2. Build and push your Docker image to ECR
3. Create an ECS cluster
4. Define a task definition
5. Create a service to run your task

## 4. Set Up Domain and SSL

### 4.1 Register a Domain (if you don't have one)

1. Use Route 53 or any domain registrar to register a domain

### 4.2 Configure DNS

1. Create a new record in Route 53 or your DNS provider
2. Point the record to your EC2 instance's public IP

### 4.3 Set Up SSL with Let's Encrypt

1. Install Certbot:

```
sudo amazon-linux-extras install epel
sudo yum install -y certbot
```

2. Obtain a certificate:

```
sudo certbot certonly --standalone -d your-domain.com
```

### 4.4 Set Up Nginx as a Reverse Proxy

1. Install Nginx:

```
sudo yum install -y nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

2. Configure Nginx:

```
sudo nano /etc/nginx/conf.d/chayachitr.conf
```

3. Add the following configuration:

```
server {
    listen 80;
    server_name your-domain.com;

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

4. Test and reload Nginx:

```
sudo nginx -t
sudo systemctl reload nginx
```

## 5. Set Up Monitoring

### 5.1 Set Up CloudWatch Monitoring

1. Install CloudWatch agent:

```
sudo yum install -y amazon-cloudwatch-agent
```

2. Configure the agent:

```
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-config-wizard
```

3. Start the agent:

```
sudo systemctl start amazon-cloudwatch-agent
sudo systemctl enable amazon-cloudwatch-agent
```

### 5.2 Set Up Application Logging

1. Configure your application to log to a file
2. Configure CloudWatch to monitor the log file

## 6. Set Up Backup Strategy

### 6.1 MongoDB Backup

1. Set up automated MongoDB backups
   - If using Atlas, this is configured in the Atlas console
   - If self-hosting, set up a cron job to run mongodump

### 6.2 S3/MinIO Backup

1. Set up S3 bucket versioning and lifecycle policies
2. Consider cross-region replication for disaster recovery

## 7. Set Up CI/CD Pipeline

### 7.1 Using GitHub Actions

1. Create `.github/workflows/deploy.yml` file in your repository
2. Configure the workflow to:
   - Build and test your application
   - Build and push Docker images
   - Deploy to your EC2 instance or ECS

Example workflow:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Go
        uses: actions/setup-go@v2
        with:
          go-version: 1.21

      - name: Test
        run: go test -v ./...

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Login to Amazon ECR
        id: login-ecr
        uses: aws-actions/amazon-ecr-login@v1

      - name: Build and push Docker image
        env:
          ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
          ECR_REPOSITORY: chayachitr
          IMAGE_TAG: ${{ github.sha }}
        run: |
          docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
          docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

      - name: Deploy to EC2
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.EC2_HOST }}
          username: ec2-user
          key: ${{ secrets.EC2_SSH_KEY }}
          script: |
            cd chayachitr
            git pull
            docker-compose down
            docker-compose up -d
```

## 8. Post-Deployment Checks

1. Verify the application is running:

```
curl http://your-domain.com/health
```

2. Monitor logs:

```
docker-compose logs -f
```

3. Test the API endpoints:

```
# Register a user
curl -X POST https://your-domain.com/register -d '{"username":"test","password":"password123"}'

# Login
curl -X POST https://your-domain.com/login -d '{"username":"test","password":"password123"}'
```

## 9. Scaling Considerations

### 9.1 Horizontal Scaling

1. Set up an Auto Scaling Group in EC2
2. Use an Application Load Balancer (ALB) to distribute traffic
3. Make sure your application is stateless or uses a central session store

### 9.2 Vertical Scaling

1. Upgrade your EC2 instance type as needed
2. Monitor resource usage to determine when to scale

## 10. Maintenance

1. Set up regular security updates:

```
sudo yum install -y yum-cron
sudo systemctl enable yum-cron
sudo systemctl start yum-cron
```

2. Implement a backup rotation strategy
3. Monitor application performance and optimize as needed
