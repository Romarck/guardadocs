from app.main import app
import asyncio
import json
import logging
from urllib.parse import parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def handler(event, context):
    """
    Handle requests from Vercel serverless function
    """
    logger.info(f"Received event: {json.dumps(event, default=str)}")
    
    # Parse request information
    path = event.get('path', '/')
    http_method = event.get('httpMethod', 'GET')
    headers = event.get('headers', {})
    query_string = event.get('queryStringParameters', {})
    body = event.get('body', '')
    
    # Convert query string to bytes
    query_bytes = '&'.join(f"{k}={v}" for k, v in query_string.items()).encode()
    
    # Prepare ASGI scope
    scope = {
        'type': 'http',
        'asgi': {'version': '3.0'},
        'http_version': '1.1',
        'method': http_method,
        'scheme': 'https',
        'path': path,
        'raw_path': path.encode(),
        'query_string': query_bytes,
        'headers': [[k.lower().encode(), v.encode()] for k, v in headers.items()],
        'client': ('127.0.0.1', 0),
        'server': (None, None),
    }

    # Prepare response holders
    response = {}
    send_queue = asyncio.Queue()

    async def receive():
        return {
            'type': 'http.request',
            'body': body.encode() if body else b'',
            'more_body': False,
        }

    async def send(message):
        await send_queue.put(message)

    # Run ASGI application
    await app(scope, receive, send)

    # Get response information
    message = await send_queue.get()
    if message['type'] == 'http.response.start':
        response['statusCode'] = message['status']
        response['headers'] = {
            k.decode(): v.decode()
            for k, v in message['headers']
        }

    # Get response body
    message = await send_queue.get()
    if message['type'] == 'http.response.body':
        response['body'] = message['body'].decode()

    logger.info(f"Sending response: {json.dumps(response, default=str)}")
    return response

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 