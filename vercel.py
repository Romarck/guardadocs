from api.index import app
from mangum import Mangum

# Configure handler for Vercel
handler = Mangum(app, lifespan="off") 