from fastapi import FastAPI
from mangum import Mangum
from app.main import app

# Create handler for Vercel
handler = Mangum(app)

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 