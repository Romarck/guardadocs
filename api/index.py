from app.main import app
from mangum import Mangum
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import parse_qs, urlparse

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
            # Parse URL and query parameters
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Convert query params from lists to single values
            query_params = {k: v[0] if len(v) == 1 else v for k, v in query_params.items()}

            # Get request body
            body = self._get_body()

            # Create AWS Lambda event format
            event = {
                'version': '2.0',
                'routeKey': f'{self.command} {path}',
                'rawPath': path,
                'rawQueryString': parsed_url.query,
                'headers': dict(self.headers),
                'queryStringParameters': query_params if query_params else None,
                'requestContext': {
                    'http': {
                        'method': self.command,
                        'path': path,
                        'protocol': self.protocol_version,
                        'sourceIp': self.client_address[0],
                    },
                },
                'body': body,
                'isBase64Encoded': False
            }

            # Call Mangum handler
            response = mangum_handler(event, {})

            # Send response
            status_code = response.get('statusCode', 200)
            self.send_response(status_code)
            
            # Add headers
            headers = response.get('headers', {})
            for key, value in headers.items():
                self.send_header(key, value)
            self.end_headers()
            
            # Send body
            body = response.get('body', '')
            if isinstance(body, str):
                body = body.encode('utf-8')
            elif isinstance(body, dict):
                body = json.dumps(body).encode('utf-8')
            self.wfile.write(body)

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = {
                'error': str(e),
                'type': type(e).__name__
            }
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