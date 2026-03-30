FROM public.ecr.aws/lambda/python:3.12

# Upgrade pip
RUN pip install --upgrade pip

# Copy and install requirements (much smaller now - no ML models!)
COPY requirements-lambda.txt .
RUN pip install --no-cache-dir -r requirements-lambda.txt

# Copy application code
COPY app/ ./app/
COPY data/ ./data/

# Copy vector store
COPY chroma_db/ ./chroma_db/

# Set handler
CMD ["app.lambda_handler.handler"]
