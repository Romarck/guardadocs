from app.main import app
from mangum import Mangum

# Create handler for Vercel
handler = Mangum(app, enable_proxy=True)

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 