# AWS Deployment Guide for FinSolve AI Assistant 🚀

This guide provides **detailed step-by-step instructions** for deploying the FinSolve AI Assistant on AWS while staying within the **free tier** (< $10 budget).

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [AWS Account Setup](#aws-account-setup)
3. [Budget Protection (CRITICAL!)](#budget-protection-critical)
4. [Architecture Overview](#architecture-overview)
5. [Option A: Serverless (Lambda + API Gateway)](#option-a-serverless-lambda--api-gateway)
6. [Option B: Container (ECS Fargate)](#option-b-container-ecs-fargate)
7. [Frontend Deployment (Streamlit)](#frontend-deployment-streamlit)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Cost Breakdown](#cost-breakdown)
10. [Troubleshooting](#troubleshooting)
11. [Cleanup (Avoid Charges!)](#cleanup-avoid-charges)

---

## Prerequisites

Before starting, make sure you have:

1. **AWS Account** (new accounts get 12 months free tier)
2. **AWS CLI** installed and configured
3. **Docker** installed (for containerization)
4. **Python 3.10+** installed
5. **Groq API Key** (free from https://console.groq.com/keys)

### Install AWS CLI

```bash
# macOS
brew install awscli

# Linux
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Windows
# Download from: https://aws.amazon.com/cli/
```

### Configure AWS CLI

```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Get from IAM console
- **AWS Secret Access Key**: Get from IAM console
- **Default region**: `us-east-1` (best free tier coverage)
- **Default output format**: `json`

---

## AWS Account Setup

### Step 1: Create AWS Account

1. Go to https://aws.amazon.com/
2. Click **"Create an AWS Account"**
3. Enter email and choose account name
4. **Account type**: Personal (unless for business)
5. Add payment method (required but won't be charged within free tier)
6. Verify phone number
7. Choose **Basic Support** (free)

### Step 2: Create IAM User (Don't Use Root!)

**Why**: Root account has full access. Create a limited user for safety.

1. Go to **AWS Console** → Search "IAM"
2. Click **"Users"** in left sidebar
3. Click **"Add users"**

   ![IAM User Creation](https://docs.aws.amazon.com/images/IAM/latest/UserGuide/images/create-user-step1.console.png)

4. **User name**: `finsolve-developer`
5. Check ✅ **"Provide user access to the AWS Management Console"**
6. Select **"I want to create an IAM user"**
7. Auto-generate password or set custom
8. Click **"Next"**

9. **Set permissions**:
   - Select **"Attach policies directly"**
   - Search and check these policies:
     - ✅ `AmazonEC2ContainerRegistryFullAccess`
     - ✅ `AWSLambda_FullAccess`
     - ✅ `AmazonAPIGatewayAdministrator`
     - ✅ `AmazonS3FullAccess`
     - ✅ `CloudWatchFullAccess`
     - ✅ `AWSBudgetsActionsWithAWSResourceControlAccess`

10. Click **"Next"** → **"Create user"**

11. **Save credentials!** Download the CSV file.

### Step 3: Create Access Keys for CLI

1. Go to **IAM** → **Users** → Click your user name
2. Go to **"Security credentials"** tab
3. Click **"Create access key"**
4. Select **"Command Line Interface (CLI)"**
5. Confirm and click **"Create access key"**
6. **Download the CSV file immediately** (you can't see the secret again!)

Now configure AWS CLI with these keys:
```bash
aws configure
# Enter the Access Key ID and Secret from the CSV
```

---

## Budget Protection (CRITICAL!)

**⚠️ DO THIS BEFORE DEPLOYING ANYTHING**

AWS can charge unexpected amounts. Set up budget alerts to protect yourself.

### Step 1: Create a Budget

1. Go to **AWS Console** → Search **"Budgets"**
2. Click **"Create a budget"**
3. Choose **"Use a template"**
4. Select **"Zero spend budget"** (alerts on ANY spending)

   OR for more control, select **"Monthly cost budget"**:
   - Budget amount: `$10`

5. **Email recipients**: Your email address
6. Click **"Create budget"**

### Step 2: Create $5 Warning Alert

1. In Budgets, click your budget
2. Click **"Add alert"**
3. **Threshold**: 50%
4. **Trigger**: Actual
5. **Email**: Your email

### Step 3: Enable Cost Anomaly Detection

1. Search **"Cost Anomaly Detection"**
2. Click **"Create monitor"**
3. **Monitor type**: AWS services
4. **Monitor name**: `FinSolve-Anomaly`
5. Add your email for alerts
6. **Threshold**: $1 (alert on small anomalies)

### Step 4: Set Up Billing Alerts

1. Go to **Billing** → **Billing preferences**
2. Enable ✅ **"Receive AWS Free Tier alerts"**
3. Enable ✅ **"Receive CloudWatch billing alerts"**
4. Enter your email

---

## Architecture Overview

```
                    ┌─────────────────────────────────────┐
                    │          INTERNET                   │
                    └─────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    │                               │
                    ▼                               ▼
        ┌───────────────────┐           ┌─────────────────────┐
        │   Streamlit UI    │           │    API Gateway      │
        │ (Streamlit Cloud) │           │  (HTTPS endpoint)   │
        │       FREE        │           │       FREE*         │
        └───────────────────┘           └─────────────────────┘
                    │                               │
                    │        HTTP Requests          │
                    └───────────────┬───────────────┘
                                    ▼
                    ┌─────────────────────────────────────┐
                    │         AWS Lambda                  │
                    │    (FastAPI + Mangum)               │
                    │   FREE: 1M requests/month           │
                    └─────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    ▼               ▼               ▼
            ┌───────────┐   ┌───────────┐   ┌───────────────┐
            │ ChromaDB  │   │   Groq    │   │  CloudWatch   │
            │ (in-memory│   │  Cloud    │   │ (monitoring)  │
            │  or S3)   │   │   FREE    │   │    FREE*      │
            └───────────┘   └───────────┘   └───────────────┘

* Within free tier limits
```

---

## Option A: Serverless (Lambda + API Gateway)

**Best for**: Low traffic, cost optimization, simple deployment

### Why Lambda?
- **Free tier**: 1 million requests/month + 400,000 GB-seconds
- **Auto-scaling**: Handles traffic spikes automatically
- **No servers to manage**: AWS handles everything

### Step 1: Prepare Lambda Deployment Package

Due to Lambda's size limits (250MB unzipped), we'll use a Lambda Layer for dependencies.

**Create a simplified Lambda handler:**

```bash
cd ds-rpc-01
```

Create `lambda_handler.py`:

```python
"""
AWS Lambda handler using Mangum.
Wraps FastAPI app for Lambda compatibility.
"""
from mangum import Mangum
from app.main import app

# Mangum converts Lambda events to ASGI (FastAPI format)
handler = Mangum(app, lifespan="off")
```

### Step 2: Create Lambda Layer for Dependencies

Lambda Layers store shared code/dependencies.

```bash
# Create layer directory
mkdir -p lambda_layer/python

# Install dependencies into layer
pip install \
    fastapi \
    uvicorn \
    langchain \
    langchain-groq \
    chromadb \
    sentence-transformers \
    pydantic \
    mangum \
    -t lambda_layer/python/

# Zip the layer (this will be large, ~200MB)
cd lambda_layer
zip -r ../lambda_layer.zip python/
cd ..
```

**⚠️ Size Issue**: sentence-transformers is too large for Lambda. 

**Solution: Use a lightweight alternative or ECS (Option B)**

For Lambda, let's simplify - skip local reranking:

### Step 3: Create Simplified Lambda Version

Create `lambda_simple.py`:

```python
"""
Simplified Lambda handler (without heavy ML models).
Uses Groq for all inference.
"""
import json
import os
from typing import Dict

# Set environment variables
os.environ["GROQ_API_KEY"] = os.getenv("GROQ_API_KEY", "")

def handler(event, context):
    """AWS Lambda handler."""
    
    # Parse the incoming request
    http_method = event.get("httpMethod", "GET")
    path = event.get("path", "/")
    body = event.get("body", "{}")
    
    if isinstance(body, str):
        body = json.loads(body) if body else {}
    
    # Route requests
    if path == "/health":
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "healthy"}),
            "headers": {"Content-Type": "application/json"}
        }
    
    elif path == "/chat" and http_method == "POST":
        # Import here to avoid cold start overhead
        from langchain_groq import ChatGroq
        
        message = body.get("message", "")
        
        llm = ChatGroq(
            api_key=os.environ["GROQ_API_KEY"],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
        )
        
        response = llm.invoke(message)
        
        return {
            "statusCode": 200,
            "body": json.dumps({"response": response.content}),
            "headers": {"Content-Type": "application/json"}
        }
    
    return {
        "statusCode": 404,
        "body": json.dumps({"error": "Not found"})
    }
```

### Step 4: Create Lambda Function

1. Go to **AWS Console** → Search **"Lambda"**
2. Click **"Create function"**

3. **Basic information**:
   - Function name: `finsolve-ai-assistant`
   - Runtime: `Python 3.11`
   - Architecture: `x86_64`

4. Click **"Create function"**

5. **Add Environment Variables**:
   - Click **"Configuration"** tab
   - Click **"Environment variables"**
   - Click **"Edit"**
   - Add: `GROQ_API_KEY` = `your_groq_api_key`

6. **Increase timeout and memory**:
   - In **"Configuration"** → **"General configuration"**
   - Click **"Edit"**
   - Memory: `512 MB` (minimum for ML)
   - Timeout: `30 seconds`
   - Click **"Save"**

7. **Upload code**:
   - In **"Code"** tab
   - Paste your handler code
   - Click **"Deploy"**

### Step 5: Create API Gateway

1. Go to **AWS Console** → Search **"API Gateway"**
2. Click **"Create API"**
3. Choose **"HTTP API"** (simpler and cheaper)
4. Click **"Build"**

5. **Configure**:
   - API name: `finsolve-api`
   - Click **"Add integration"**
   - Integration type: `Lambda`
   - Lambda function: `finsolve-ai-assistant`

6. **Configure routes**:
   - Method: `ANY`
   - Resource path: `/{proxy+}` (catches all paths)

7. **Configure stages**:
   - Stage name: `prod`
   - Auto-deploy: ✅ Enabled

8. Click **"Create"**

9. **Copy your API URL** (something like):
   ```
   https://abc123xyz.execute-api.us-east-1.amazonaws.com/prod
   ```

### Step 6: Test the API

```bash
# Health check
curl https://YOUR-API-URL/health

# Chat (requires auth header in real app)
curl -X POST https://YOUR-API-URL/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is FinSolve?"}'
```

---

## Option B: Container (ECS Fargate)

**Best for**: Full application with ML models, more flexibility

### Why ECS Fargate?
- No size limits (unlike Lambda)
- Run the full application with all ML models
- Still serverless (no EC2 instances to manage)
- **Cost**: ~$0 with minimal usage, but watch carefully

### Step 1: Create Dockerfile

Create `Dockerfile` in project root:

```dockerfile
# Use Python slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better caching)
COPY pyproject.toml .

# Install Python dependencies
RUN pip install --no-cache-dir .

# Copy application code
COPY app/ app/
COPY data/ data/
COPY scripts/ scripts/

# Initialize vector store at build time
RUN python scripts/init_vectorstore.py

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Step 2: Build and Test Locally

```bash
# Build the image
docker build -t finsolve-ai:latest .

# Test locally
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key_here \
  finsolve-ai:latest

# Test it works
curl http://localhost:8000/health
```

### Step 3: Create ECR Repository

ECR (Elastic Container Registry) stores your Docker images.

1. Go to **AWS Console** → Search **"ECR"**
2. Click **"Create repository"**

3. **Settings**:
   - Visibility: `Private`
   - Repository name: `finsolve-ai`
   - Tag immutability: `Disabled`
   - Scan on push: ✅ `Enabled` (security)

4. Click **"Create repository"**

5. **Copy the repository URI** (like):
   ```
   123456789.dkr.ecr.us-east-1.amazonaws.com/finsolve-ai
   ```

### Step 4: Push Image to ECR

```bash
# Authenticate Docker to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-east-1.amazonaws.com

# Tag your image
docker tag finsolve-ai:latest \
  123456789.dkr.ecr.us-east-1.amazonaws.com/finsolve-ai:latest

# Push to ECR
docker push 123456789.dkr.ecr.us-east-1.amazonaws.com/finsolve-ai:latest
```

### Step 5: Create ECS Cluster

1. Go to **AWS Console** → Search **"ECS"**
2. Click **"Clusters"** → **"Create cluster"**

3. **Cluster configuration**:
   - Cluster name: `finsolve-cluster`
   - Infrastructure: ✅ `AWS Fargate (serverless)`
   - ❌ Uncheck "Amazon EC2 instances" (costs money!)

4. Click **"Create"**

### Step 6: Create Task Definition

1. Go to **ECS** → **"Task definitions"**
2. Click **"Create new task definition"**

3. **Task definition configuration**:
   - Task definition family: `finsolve-task`
   - Launch type: `AWS Fargate`
   - Operating system: `Linux/X86_64`
   - CPU: `0.5 vCPU` (512)
   - Memory: `1 GB`

4. **Container details**:
   - Name: `finsolve-container`
   - Image URI: `123456789.dkr.ecr.us-east-1.amazonaws.com/finsolve-ai:latest`
   - Port mappings: `8000` TCP

5. **Environment variables**:
   - Click **"Add environment variable"**
   - Key: `GROQ_API_KEY`
   - Value type: `Value`
   - Value: Your Groq API key

   ⚠️ **Better approach**: Use AWS Secrets Manager:
   - Key: `GROQ_API_KEY`
   - Value type: `ValueFrom`
   - Value: `arn:aws:secretsmanager:us-east-1:123456789:secret:groq-key`

6. Click **"Create"**

### Step 7: Create Service

1. Go to **ECS** → **Clusters** → Click `finsolve-cluster`
2. Click **"Services"** tab → **"Create"**

3. **Compute configuration**:
   - Launch type: `FARGATE`

4. **Deployment configuration**:
   - Application type: `Service`
   - Family: `finsolve-task`
   - Service name: `finsolve-service`
   - Desired tasks: `1` (start with 1 to minimize cost)

5. **Networking**:
   - VPC: Select default VPC
   - Subnets: Select all available
   - Security group: Create new
     - Inbound rule: TCP port 8000 from 0.0.0.0/0
   - Public IP: ✅ `Turned on`

6. Click **"Create"**

7. **Wait for deployment** (~2-5 minutes)

8. **Get the public IP**:
   - Go to the service → **"Tasks"** tab
   - Click the running task
   - Find **"Public IP"**
   - Test: `curl http://PUBLIC_IP:8000/health`

### Step 8: Add Application Load Balancer (Optional but Recommended)

For HTTPS and better reliability:

1. Go to **EC2** → **"Load Balancers"**
2. Click **"Create Load Balancer"**
3. Choose **"Application Load Balancer"**
4. Name: `finsolve-alb`
5. Scheme: `Internet-facing`
6. Select your VPC and subnets
7. Create target group pointing to your ECS service
8. Add listener rules for your API

---

## Frontend Deployment (Streamlit)

### Option 1: Streamlit Cloud (Free, Easiest)

1. Push your code to GitHub
2. Go to https://streamlit.io/cloud
3. Click **"New app"**
4. Connect your GitHub repo
5. **Settings**:
   - Main file: `app/streamlit_app.py`
   - Python version: `3.10`
6. **Environment variables** (in Advanced settings):
   - `API_URL`: Your Lambda/ECS API URL
7. Click **"Deploy"**

### Option 2: S3 + CloudFront (Static)

If you convert Streamlit to a static site (not recommended):

1. Build static files
2. Upload to S3
3. Create CloudFront distribution
4. (Complex - stick with Streamlit Cloud)

---

## Monitoring & Alerts

### CloudWatch Dashboards

1. Go to **CloudWatch** → **"Dashboards"**
2. Click **"Create dashboard"**
3. Name: `FinSolve-Monitoring`

4. **Add widgets**:

   **Lambda Metrics** (if using Lambda):
   - Invocations
   - Duration
   - Errors
   - Throttles

   **ECS Metrics** (if using ECS):
   - CPU Utilization
   - Memory Utilization
   - Running Task Count

5. Click **"Save dashboard"**

### Create Alarm for High Costs

1. Go to **CloudWatch** → **"Alarms"**
2. Click **"Create alarm"**
3. **Select metric**:
   - Billing → Total Estimated Charge
4. **Conditions**:
   - Threshold: `$5`
   - Period: `6 hours`
5. **Notification**:
   - Create SNS topic
   - Add your email
6. **Name**: `High-Cost-Alert`
7. Click **"Create alarm"**

---

## Cost Breakdown

| Service | Free Tier Limit | Expected Usage | Cost |
|---------|-----------------|----------------|------|
| **Lambda** | 1M requests/month | ~1,000 | $0 |
| **API Gateway** | 1M HTTP calls/month | ~1,000 | $0 |
| **ECR** | 500MB storage | ~300MB | $0 |
| **ECS Fargate** | No free tier | Minimal | ~$2-5* |
| **CloudWatch** | 10 metrics, 10 alarms | Within limits | $0 |
| **S3** | 5GB storage | ~100MB | $0 |
| **Data Transfer** | 100GB out | ~1GB | $0 |

*ECS costs can be minimized by stopping the service when not in use.

### Cost Optimization Tips

1. **Use Lambda** for low-traffic scenarios
2. **Stop ECS tasks** when not needed
3. **Set desired count to 0** during development
4. **Use Spot instances** for ECS (not Fargate)
5. **Monitor daily** in Cost Explorer

---

## Troubleshooting

### Lambda: "Task timed out"

**Solution**: Increase timeout in Configuration → General configuration

### Lambda: Package too large

**Solution**: 
- Use Lambda Layers
- Exclude unnecessary files
- Consider ECS instead

### ECS: Task keeps failing

**Check logs**:
1. Go to ECS → Cluster → Service → Tasks
2. Click the stopped task
3. Click "Logs" tab
4. Look for errors

### API Gateway: 502 Bad Gateway

**Causes**:
- Lambda timeout
- Lambda error
- Integration issue

**Fix**: Check Lambda logs in CloudWatch

### "Access Denied" errors

**Fix**: Check IAM permissions for your user/role

---

## Cleanup (Avoid Charges!)

When you're done, delete resources to avoid charges:

### Delete ECS Resources

```bash
# Delete service
aws ecs delete-service \
  --cluster finsolve-cluster \
  --service finsolve-service \
  --force

# Delete cluster
aws ecs delete-cluster --cluster finsolve-cluster
```

### Delete Lambda

1. Go to Lambda → Select function → Actions → Delete

### Delete API Gateway

1. Go to API Gateway → Select API → Actions → Delete

### Delete ECR Images

```bash
aws ecr batch-delete-image \
  --repository-name finsolve-ai \
  --image-ids imageTag=latest
```

### Delete CloudWatch

1. Go to CloudWatch → Dashboards → Delete
2. Go to CloudWatch → Alarms → Delete

### Verify No Resources Running

1. Go to **Billing** → **Bills**
2. Check for any charges
3. Use **Cost Explorer** to see what's running

---

## Quick Reference Commands

```bash
# Check AWS identity
aws sts get-caller-identity

# List Lambda functions
aws lambda list-functions

# List ECS clusters
aws ecs list-clusters

# List ECR repositories
aws ecr describe-repositories

# View Lambda logs
aws logs tail /aws/lambda/finsolve-ai-assistant --follow

# View ECS logs
aws logs tail /ecs/finsolve-task --follow

# Check costs (current month)
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

---

## Summary

**Recommended approach for this project**:

1. ✅ **Use Streamlit Cloud** for frontend (free, easy)
2. ✅ **Use Lambda** for simple API (free tier)
3. ⚠️ **Use ECS Fargate** only if Lambda limitations hit you
4. ✅ **Set up budgets FIRST** before deploying anything
5. ✅ **Monitor costs daily** during development

**Total Expected Cost: $0 - $5** (within free tier)

If you follow this guide carefully, you should stay well under your $10 budget!

---

*Questions? Check AWS documentation or create an issue in the project repository.*
