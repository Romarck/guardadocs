from app.main import app
from mangum import Mangum

# Configure Mangum handler
handler = Mangum(
    app,
    lifespan="off"
) 