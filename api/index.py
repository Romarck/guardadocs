from fastapi import FastAPI
from mangum import Mangum
from app.main import app

# Create handler for Vercel serverless function
async def handler(request, context):
    asgi_handler = Mangum(app, lifespan="off")
    response = await asgi_handler(request, context)
    return response

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 