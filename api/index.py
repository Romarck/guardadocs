from app.main import app
from http.server import BaseHTTPRequestHandler
import json

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_PUT(self):
        self._handle_request()

    def do_DELETE(self):
        self._handle_request()

    def _handle_request(self):
        # Create a mock event for the FastAPI app
        event = {
            "path": self.path,
            "httpMethod": self.command,
            "headers": dict(self.headers),
            "queryStringParameters": {},
            "body": self._get_body()
        }

        # Call the FastAPI app
        response = app(event, None)
        
        # Send the response
        self.send_response(response["statusCode"])
        for header, value in response.get("headers", {}).items():
            self.send_header(header, value)
        self.end_headers()
        self.wfile.write(response.get("body", "").encode())

    def _get_body(self):
        content_length = int(self.headers.get("Content-Length", 0))
        if content_length > 0:
            return self.rfile.read(content_length).decode()
        return ""

handler = Handler

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 