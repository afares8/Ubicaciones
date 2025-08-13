from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from app.wms.routers import (
    locations, bins, stock, movements, counts, labels, packing_bridge
)
from app.database import engine, Base, test_connection
import logging
import time
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('wms_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WMS Bin-Locations Inventory System", 
    description="Warehouse Management System for bin locations and stock tracking with SAP B1 integration",
    version="1.0.0"
)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(f"[HTTP] REQUEST RECEIVED")
    logger.info(f"   Client IP: {client_ip}")
    logger.info(f"   Method: {request.method}")
    logger.info(f"   URL: {request.url}")
    logger.info(f"   Path: {request.url.path}")
    logger.info(f"   Query params: {dict(request.query_params)}")
    logger.info(f"   Headers: {dict(request.headers)}")
    logger.info(f"   Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    response = await call_next(request)
    
    elapsed_time = time.time() - start_time
    logger.info(f"   Response: {response.status_code}")
    logger.info(f"   Completed in {elapsed_time:.3f}s")
    logger.info(f"   Response headers: {dict(response.headers)}")
    
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5175"
    ],
    allow_origin_regex=r"http://.*:(3000|5175|8000)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(locations.router, prefix="/api/v1/wms", tags=["locations"])
app.include_router(bins.router, prefix="/api/v1/wms", tags=["bins"])
app.include_router(stock.router, prefix="/api/v1/wms", tags=["stock"])
app.include_router(movements.router, prefix="/api/v1/wms", tags=["movements"])
app.include_router(counts.router, prefix="/api/v1/wms", tags=["counts"])
app.include_router(labels.router, prefix="/api/v1/wms", tags=["labels"])
app.include_router(packing_bridge.router, prefix="/api/v1/wms", tags=["packing-bridge"])

@app.on_event("startup")
async def startup():
    """Initialize database tables and check connections"""
    logger.info("Starting WMS Bin-Locations Inventory System...")
    
    if test_connection():
        logger.info("✅ SQL Server database connection successful")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created/verified successfully")
    else:
        logger.warning("⚠️ SQL Server database connection failed. Running in development mode.")
    
    sap_di_url = os.getenv("SAP_DI_BASE_URL", "http://localhost:8001")
    logger.info(f"SAP DI Service URL: {sap_di_url}")

@app.get("/")
async def root():
    return {
        "message": "WMS Bin-Locations Inventory System API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        db_status = test_connection()
        return {
            "status": "healthy",
            "database": "connected" if db_status else "disconnected",
            "service": "wms-api"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "wms-api"
        }
