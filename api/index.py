from app.main import app
from starlette.types import ASGIApp, Message, Receive, Scope, Send

async def handler(scope: Scope, receive: Receive, send: Send) -> None:
    if scope["type"] == "lifespan":
        while True:
            message = await receive()
            if message["type"] == "lifespan.startup":
                await app(scope, receive, send)
            if message["type"] == "lifespan.shutdown":
                await app(scope, receive, send)
                return
    else:
        await app(scope, receive, send)

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 