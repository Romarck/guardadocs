from app.main import app
from mangum import Mangum

# Vercel serverless function handler
handler = Mangum(app) 