from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from app.core.config import settings
from app.core.database import supabase_client
from app.api.v1.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Lead Generation SaaS Backend...")
    
    # Test Supabase connection
    try:
        # Simple test query to verify connection
        response = supabase_client.table("test").select("*").limit(1).execute()
        print("✅ Supabase connection successful")
    except Exception as e:
        print(f"⚠️ Supabase connection test failed: {e}")
        print("📝 Note: This is expected if tables don't exist yet")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Lead Generation SaaS Backend...")


app = FastAPI(
    title="Lead Generation SaaS Backend",
    description="A comprehensive lead generation system with web scraping and analytics",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=f"/api/{settings.API_VERSION}")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Lead Generation SaaS Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )