# src/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.qp_gen_routes import router as qp_router
from api.evaluation_routes import evaluation_router
from api.error_handlers import add_error_handlers
from config.settings import settings
from utils.logger import logger

# Initialize FastAPI app
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="AI-powered Question Paper Generator using Local LLM"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define Prefix for all routes
prefix = "/api/v1"

# Add routes
app.include_router(qp_router, prefix=prefix)
app.include_router(evaluation_router,prefix=prefix)  

# Add error handlers
add_error_handlers(app)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Question Paper Generator API", {
        "version": settings.API_VERSION,
        "environment": settings.ENVIRONMENT,
        "endpoints": [
            "Question Generation",
            "Answer Evaluation"
        ]
    })

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Question Paper Generator API")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )