from app.main import app
from http.server import BaseHTTPRequestHandler
from starlette.requests import Request
from starlette.responses import Response
from starlette.datastructures import Headers
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        logger.info(f"Received GET request: {self.path}")
        self._handle_request()

    def do_POST(self):
        logger.info(f"Received POST request: {self.path}")
        self._handle_request()

    def do_PUT(self):
        logger.info(f"Received PUT request: {self.path}")
        self._handle_request()

    def do_DELETE(self):
        logger.info(f"Received DELETE request: {self.path}")
        self._handle_request()

    def _handle_request(self):
        try:
            # Create a Starlette request
            scope = {
                "type": "http",
                "http_version": "1.1",
                "method": self.command,
                "path": self.path,
                "headers": [(k.lower(), v) for k, v in self.headers.items()],
                "query_string": self.path.split("?")[1].encode() if "?" in self.path else b"",
                "client": ("127.0.0.1", 8000),
                "server": ("127.0.0.1", 8000),
                "scheme": "http",
                "root_path": "",
                "raw_path": self.path.encode(),
            }

            async def receive():
                body = self._get_body()
                logger.info(f"Received body: {body}")
                return {"type": "http.request", "body": body.encode()}

            async def send(message):
                logger.info(f"Sending message: {message['type']}")
                if message["type"] == "http.response.start":
                    self.send_response(message["status"])
                    for header, value in message["headers"]:
                        self.send_header(header.decode(), value.decode())
                    self.end_headers()
                elif message["type"] == "http.response.body":
                    self.wfile.write(message["body"])

            # Call FastAPI directly with receive and send
            app(scope, receive, send)
        except Exception as e:
            logger.error(f"Error handling request: {str(e)}", exc_info=True)
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

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