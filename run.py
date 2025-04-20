import hypercorn.asyncio
import hypercorn.config
import asyncio
from app.main import app

async def main():
    config = hypercorn.config.Config()
    config.bind = ["0.0.0.0:8000"]
    config.use_reloader = True
    config.worker_class = "asyncio"
    config.workers = 4
    config.access_log_format = '%(h)s %(r)s %(s)s %(b)s %(D)s'
    config.accesslog = "-"
    config.errorlog = "-"
    config.loglevel = "INFO"
    config.keep_alive_timeout = 120
    config.graceful_timeout = 120
    config.max_body_size = 10485760  # 10MB

    await hypercorn.asyncio.serve(app, config)

if __name__ == "__main__":
    asyncio.run(main()) 