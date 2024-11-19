import uvicorn
from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse
import logging

from instorage.allowed_origins.get_origin_callback import get_origin
from instorage.authentication import auth_dependencies
from instorage.main import config
from instorage.main.logging import get_logger
from instorage.server import api_documentation
from instorage.server.dependencies.lifespan import lifespan
from instorage.server.exception_handlers import add_exception_handlers
from instorage.server.middleware.cors import CORSMiddleware
from instorage.server.models.api import VersionResponse
from instorage.server.routers import router as api_router

if config.get_settings().using_intric_proprietary:
    from instorage_prop.config import get_allowed_origins

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = get_logger(__name__)

if config.get_settings().using_intric_proprietary:
    allowed_origins = get_allowed_origins()
else:
    allowed_origins = ["http://localhost:3000", "http://172.18.0.3:3000"]

def get_application():
    app = FastAPI(
        title=api_documentation.TITLE,
        version=config.get_settings().app_version,
        summary=api_documentation.SUMMARY,
        openapi_tags=api_documentation.TAGS_METADATA,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],  # Ensure "OPTIONS" requests are permitted
        allow_headers=["*"],
    )

    # Add a middleware to log requests and responses
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Incoming request: Method - {request.method}, URL - {request.url}, Headers - {dict(request.headers)}")
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            response = JSONResponse(status_code=500, content={"error": str(e)})
        logger.info(f"Response status: {response.status_code}, Headers - {dict(response.headers)}")
        return response

    app.include_router(api_router, prefix=config.get_settings().api_prefix)
    add_exception_handlers(app)  # Attach custom error handlers

    return app

app = get_application()

@app.exception_handler(500)
async def custom_http_500_exception_handler(request: Request, exc):
    logger.error(f"Internal Server Error: {exc}")
    response = JSONResponse(status_code=500, content={"error": "Something went wrong"})

    origin = request.headers.get("origin")
    if origin:
        cors = CORSMiddleware(
            app=app,
            allow_origins=allowed_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            callback=get_origin,
        )
        response.headers.update(cors.simple_headers)
        has_cookie = "cookie" in request.headers

        if cors.allow_all_origins and has_cookie:
            response.headers["Access-Control-Allow-Origin"] = origin

        elif not cors.allow_all_origins and await cors.is_allowed_origin(origin=origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers.add_vary_header("Origin")

    return response

@app.get("/version", dependencies=[Depends(auth_dependencies.get_current_active_user)])
async def get_version():
    return VersionResponse(version=config.get_settings().app_version)

# Health check endpoint for quick testing
@app.get("/health")
def health_check():
    return {"status": "ok"}

def start():
    uvicorn.run(
        "instorage.server.main:app",
        host="0.0.0.0",
        port=8123,
        reload=True,
        reload_dirs="./src/",
    )