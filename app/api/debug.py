"""
Debug endpoints for troubleshooting
"""
from fastapi import APIRouter, HTTPException
from sqlalchemy import text, func
from sqlalchemy.orm import Session
import os
import logging
import json
from typing import Dict, Any, List
import traceback
import io
import sys

from app.db.database import get_db_session
from app.db.models.place import Place
from app.services.ai_service import get_embedding
from app.db.seed import seed_database

router = APIRouter(prefix="/debug", tags=["debug"])
logger = logging.getLogger(__name__)


@router.get("/embedding")
async def test_embedding():
    """Test if Bedrock embedding generation is working"""
    try:
        test_text = "Beautiful beach in Bali"
        embedding = get_embedding(test_text)
        
        return {
            "success": True,
            "bedrock_working": embedding is not None,
            "embedding_dimensions": len(embedding) if embedding else 0,
            "sample_values": embedding[:5] if embedding else [],
            "llm_provider": os.getenv("LLM_PROVIDER", "not_set"),
            "aws_region": os.getenv("AWS_REGION", "not_set")
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "llm_provider": os.getenv("LLM_PROVIDER", "not_set"),
            "aws_region": os.getenv("AWS_REGION", "not_set")
        }


@router.get("/embedding-status")
async def embedding_status():
    """Check how many places have embeddings"""
    db = next(get_db_session())
    try:
        total = db.query(func.count(Place.id)).scalar()
        with_embedding = db.query(func.count(Place.id)).filter(Place.embedding.isnot(None)).scalar()
        without_embedding = total - with_embedding
        
        # Sample places with embeddings
        sample_with = db.query(Place.name).filter(Place.embedding.isnot(None)).limit(3).all()
        sample_without = db.query(Place.name).filter(Place.embedding.is_(None)).limit(3).all()
        
        return {
            "total_places": total,
            "with_embedding": with_embedding,
            "without_embedding": without_embedding,
            "embedding_coverage": f"{with_embedding}/{total}",
            "sample_with_embedding": [name[0] for name in sample_with],
            "sample_without_embedding": [name[0] for name in sample_without]
        }
    finally:
        db.close()


@router.get("/env")
async def check_environment():
    """Check environment variables relevant to the application"""
    return {
        "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "NOT_SET"),
        "ENVIRONMENT": os.getenv("ENVIRONMENT", "NOT_SET"),
        "AWS_REGION": os.getenv("AWS_REGION", "NOT_SET"),
        "AWS_DEFAULT_REGION": os.getenv("AWS_DEFAULT_REGION", "NOT_SET"),
        "DATABASE_URL": "***" if os.getenv("DATABASE_URL") else "NOT_SET",
        "PYTHONPATH": os.getenv("PYTHONPATH", "NOT_SET"),
        "PATH": os.getenv("PATH", "NOT_SET")[:100] + "..." if os.getenv("PATH") else "NOT_SET",
    }


@router.post("/force-seed")
async def force_seed():
    """
    Force reseed the database with embeddings and return detailed logs
    WARNING: This truncates the places table!
    """
    # Capture logs in memory
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    
    # Add handler to root logger
    root_logger = logging.getLogger()
    original_level = root_logger.level
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
    
    results = {
        "success": False,
        "error": None,
        "logs": [],
        "environment": {
            "LLM_PROVIDER": os.getenv("LLM_PROVIDER", "NOT_SET"),
            "AWS_REGION": os.getenv("AWS_REGION", "NOT_SET"),
        },
        "places_seeded": 0,
        "embeddings_generated": 0
    }
    
    try:
        logger.info("=" * 80)
        logger.info("FORCE SEED STARTED")
        logger.info(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'NOT_SET')}")
        logger.info(f"AWS_REGION: {os.getenv('AWS_REGION', 'NOT_SET')}")
        logger.info("=" * 80)
        
        # Run seed with force=True
        seed_database(force=True)
        
        # Check results
        db = next(get_db_session())
        try:
            total = db.query(func.count(Place.id)).scalar()
            with_embedding = db.query(func.count(Place.id)).filter(Place.embedding.isnot(None)).scalar()
            
            results["places_seeded"] = total
            results["embeddings_generated"] = with_embedding
            results["success"] = True
            
            logger.info(f"Seed complete: {total} places, {with_embedding} with embeddings")
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"Seed failed: {str(e)}")
        logger.error(traceback.format_exc())
        results["error"] = str(e)
        results["traceback"] = traceback.format_exc()
    
    finally:
        # Get logs
        log_contents = log_capture.getvalue()
        results["logs"] = log_contents.split('\n')
        
        # Cleanup
        root_logger.removeHandler(handler)
        root_logger.setLevel(original_level)
        log_capture.close()
    
    return results