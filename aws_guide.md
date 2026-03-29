# AWS Deployment Guide for Scout AI 🚀

Deploy Scout AI on AWS using the permanent free tier services to keep costs minimal.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUDFLARE PAGES (FREE)                      │
│                      React Frontend                             │
└─────────────────────────────────────────────────────────────────┘
                              │ HTTPS
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS API GATEWAY                              │
│              REST API with Usage Plans                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      AWS LAMBDA                                 │
│           FastAPI Backend (via Mangum adapter)                  │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │ LangChain   │  │  LangGraph  │  │    Guardrails           │ │
│  │ RAG Chain   │  │  Agentic    │  │  (PII, Injection)       │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
          │                   │                    │
          ▼                   ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐
│   AWS S3        │  │  Groq Cloud     │  │  HuggingFace        │
│ Vector Store    │  │  (FREE LLM)     │  │  (Embeddings)       │
│ + Documents     │  │  Llama 3.3 70B  │  │  all-MiniLM-L6-v2   │
└─────────────────┘  └─────────────────┘  └─────────────────────┘
```

---

## Cost Breakdown

| Service | Free Tier Limit | Our Usage | Cost |
|---------|-----------------|-----------|------|
| API Gateway | 1M requests/month | ~1K | **$0** |
| Lambda | 1M requests + 400K GB-s | ~10K | **$0** |
| S3 | 5GB storage | ~100MB | **$0** |
| CloudWatch | 5GB logs | ~1GB | **$0** |
| Cloudflare Pages | Unlimited | Unlimited | **$0** |
| Groq Cloud | 100K tokens/day | ~50K | **$0** |
| **Total** | | | **$0** |

> Note: These are permanent free tier limits (not 12-month trial).

---

## Prerequisites

You need:
- AWS account with IAM user configured
- AWS CLI installed: `brew install awscli` (macOS)
- Docker installed
- Groq API key from https://console.groq.com/keys

---

## Step 1: Configure AWS CLI

```bash
aws configure
```

Enter your credentials:
- AWS Access Key ID: (from IAM)
- AWS Secret Access Key: (from IAM)
- Default region: `us-east-1`
- Output format: `json`

---

## Step 2: Create S3 Bucket for Vector Store

```bash
# Create bucket (name must be globally unique)
aws s3 mb s3://scout-ai-vectorstore-$(whoami)

# Upload ChromaDB data
cd ds-rpc-01
zip -r chroma_db.zip chroma_db/
aws s3 cp chroma_db.zip s3://scout-ai-vectorstore-$(whoami)/
```

---

## Step 3: Create Lambda Function

### 3.1 Install Dependencies for Lambda

```bash
mkdir -p lambda_package
cd lambda_package

# Install dependencies
pip install \
  fastapi mangum langchain langchain-groq langchain-chroma \
  langchain-huggingface chromadb sentence-transformers \
  -t .

# Copy application code
cp -r ../app .
cp ../.env .

# Create deployment package
zip -r ../lambda_deployment.zip .
```

### 3.2 Create Lambda Function via Console

1. Go to **AWS Console** → **Lambda**
2. Click **Create function**
3. Settings:
   - Name: `scout-ai-backend`
   - Runtime: `Python 3.11`
   - Architecture: `x86_64`
4. Click **Create function**

### 3.3 Upload Code

1. In Lambda console, click **Upload from** → **.zip file**
2. Upload `lambda_deployment.zip`
3. Set Handler to: `app.main.handler`

### 3.4 Configure Environment Variables

Go to **Configuration** → **Environment variables** → **Edit**:

| Key | Value |
|-----|-------|
| GROQ_API_KEY | your_groq_api_key |
| ENVIRONMENT | production |
| CHROMA_DB_PATH | /tmp/chroma_db |

### 3.5 Increase Timeout and Memory

Go to **Configuration** → **General configuration** → **Edit**:
- Memory: `1024 MB`
- Timeout: `30 seconds`

---

## Step 4: Create API Gateway

### 4.1 Create REST API

1. Go to **AWS Console** → **API Gateway**
2. Click **Create API** → **REST API** → **Build**
3. Settings:
   - Name: `scout-ai-api`
   - Endpoint type: `Regional`

### 4.2 Create Resources and Methods

1. Click **Actions** → **Create Resource**
   - Resource name: `{proxy+}`
   - Enable CORS: ✅
2. Click **Actions** → **Create Method** → **ANY**
3. Integration type: **Lambda Function**
   - Lambda Function: `scout-ai-backend`
   - Use Lambda Proxy integration: ✅

### 4.3 Enable CORS

1. Select the `/{proxy+}` resource
2. Click **Actions** → **Enable CORS**
3. Check all methods
4. Click **Enable CORS**

### 4.4 Deploy API

1. Click **Actions** → **Deploy API**
2. Stage: **New Stage** → Name: `prod`
3. Copy the **Invoke URL** (e.g., `https://abc123.execute-api.us-east-1.amazonaws.com/prod`)

---

## Step 5: Deploy Frontend to Cloudflare Pages

### 5.1 Build Frontend

```bash
cd frontend

# Set API URL
echo "VITE_API_URL=https://YOUR_API_GATEWAY_URL/prod" > .env.production

# Build
npm run build
```

### 5.2 Deploy to Cloudflare

1. Go to https://pages.cloudflare.com/
2. Connect your GitHub repository
3. Build settings:
   - Build command: `cd frontend && npm run build`
   - Build output: `frontend/dist`
4. Environment variables:
   - `VITE_API_URL`: Your API Gateway URL

---

## Step 6: Update CORS in Lambda

Update `app/main.py` to allow your Cloudflare domain:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-project.pages.dev",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Monitoring

### CloudWatch Logs

```bash
# View recent logs
aws logs tail /aws/lambda/scout-ai-backend --follow
```

### Set Up Billing Alert

1. Go to **AWS Budgets** → **Create budget**
2. Budget type: **Cost budget**
3. Amount: `$5.00`
4. Alert threshold: `80%`
5. Email: your email

---

## Cleanup

To avoid charges, delete resources when done:

```bash
# Delete Lambda
aws lambda delete-function --function-name scout-ai-backend

# Delete API Gateway
aws apigateway delete-rest-api --rest-api-id YOUR_API_ID

# Delete S3 bucket
aws s3 rb s3://scout-ai-vectorstore-$(whoami) --force
```

---

## Troubleshooting

### Lambda Timeout
- Increase timeout to 30s in Lambda configuration
- Ensure ChromaDB is loaded from S3 to `/tmp/`

### CORS Errors
- Verify API Gateway has CORS enabled
- Check Lambda response includes CORS headers

### Cold Start Latency
- First request may take 10-15s (cold start)
- Use Provisioned Concurrency ($) to reduce this

---

## Alternative: EC2 Deployment

For more control, deploy on EC2 free tier (t2.micro):

```bash
# Launch EC2 instance
# SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip

# Install dependencies
sudo yum install -y python3.11 git
pip3 install -r requirements.txt

# Run server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Use Nginx as reverse proxy and Let's Encrypt for SSL.
