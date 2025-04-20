from app.main import app
from mangum import Mangum
from http.server import BaseHTTPRequestHandler
import json

mangum_handler = Mangum(app, lifespan="off")

class Handler(BaseHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def do_GET(self):
        self._handle_request()

    def do_POST(self):
        self._handle_request()

    def do_PUT(self):
        self._handle_request()

    def do_DELETE(self):
        self._handle_request()

    def _handle_request(self):
        try:
            # Create event for Mangum
            event = {
                'httpMethod': self.command,
                'path': self.path,
                'headers': dict(self.headers),
                'queryStringParameters': {},
                'body': self._get_body()
            }

            # Call Mangum handler
            response = mangum_handler(event, None)

            # Send response
            self.send_response(response.get('statusCode', 200))
            for key, value in response.get('headers', {}).items():
                self.send_header(key, value)
            self.end_headers()
            
            body = response.get('body', '')
            if isinstance(body, str):
                body = body.encode('utf-8')
            self.wfile.write(body)

        except Exception as e:
            self.send_response(500)
            self.end_headers()
            error_response = {'error': str(e)}
            self.wfile.write(json.dumps(error_response).encode())

    def _get_body(self):
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length > 0:
            return self.rfile.read(content_length).decode()
        return ''

handler = Handler

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 