from app.main import app
from http.server import BaseHTTPRequestHandler
from mangum import Mangum

class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        self.handler = Mangum(app)
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self.handler(self.path, self.headers)

    def do_POST(self):
        self.handler(self.path, self.headers)

    def do_PUT(self):
        self.handler(self.path, self.headers)

    def do_DELETE(self):
        self.handler(self.path, self.headers)

handler = Handler

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 