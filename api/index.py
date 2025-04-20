from app.main import app
from fastapi import Request
from fastapi.responses import JSONResponse

async def handler(request: Request):
    try:
        response = await app(request.scope, request.receive, request.send)
        return response
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": str(e)}
        )

# For local development
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 