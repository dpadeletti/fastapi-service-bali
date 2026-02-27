"""
Database seeding script
"""
import json
import logging
import os
import sys
from pathlib import Path

from sqlalchemy import text

from app.db.database import get_db_session
from app.db.models.place import Place
from app.services.ai_service import get_embedding

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def load_places_data():
    """Load places from JSON file"""
    data_file = Path(__file__).parent.parent.parent / "data" / "places.json"
    logger.info(f"Loading places from {data_file}")
    
    if not data_file.exists():
        raise FileNotFoundError(f"Data file not found: {data_file}")
    
    with open(data_file, "r") as f:
        data = json.load(f)
        places = data.get("places", [])
        logger.info(f"Loaded {len(places)} places from JSON")
        return places


def seed_database(force: bool = False):
    """
    Seed the database with places from JSON file
    
    Args:
        force: If True, truncate existing data before seeding
    """
    logger.info("=" * 80)
    logger.info("DATABASE SEEDING STARTED")
    logger.info(f"Force mode: {force}")
    logger.info(f"LLM_PROVIDER: {os.getenv('LLM_PROVIDER', 'NOT_SET')}")
    logger.info(f"AWS_REGION: {os.getenv('AWS_REGION', 'NOT_SET')}")
    logger.info("=" * 80)
    
    db = next(get_db_session())
    
    try:
        # Check if places already exist
        existing_count = db.query(Place).count()
        logger.info(f"Existing places in database: {existing_count}")
        
        if existing_count > 0 and not force:
            logger.info("Database already seeded. Use --force to reseed.")
            return
        
        if force and existing_count > 0:
            logger.warning("FORCE MODE: Truncating places table...")
            db.execute(text("TRUNCATE TABLE places CASCADE"))
            db.commit()
            logger.info("Table truncated successfully")
        
        # Load data
        places_data = load_places_data()
        
        # Seed places
        logger.info(f"Starting to seed {len(places_data)} places...")
        places_with_embeddings = 0
        places_without_embeddings = 0
        
        for idx, place_data in enumerate(places_data, 1):
            try:
                # Create place object
                place = Place(
                    name=place_data["name"],
                    area=place_data["area"],
                    latitude=place_data["latitude"],
                    longitude=place_data["longitude"],
                    description=place_data["description"],
                    tags=place_data["tags"]
                )
                
                # Generate embedding
                logger.info(f"[{idx}/{len(places_data)}] Processing: {place.name}")
                
                embedding_text = f"{place.name} {place.area} {place.description} {' '.join(place.tags)}"
                logger.debug(f"  Embedding text length: {len(embedding_text)} chars")
                
                try:
                    embedding = get_embedding(embedding_text)
                    if embedding:
                        place.embedding = embedding
                        places_with_embeddings += 1
                        logger.info(f"  ✓ Embedding generated: {len(embedding)} dimensions")
                    else:
                        places_without_embeddings += 1
                        logger.warning(f"  ✗ Embedding is None")
                except Exception as e:
                    places_without_embeddings += 1
                    logger.error(f"  ✗ Embedding generation failed: {str(e)}")
                
                db.add(place)
                
                # Commit every 10 places
                if idx % 10 == 0:
                    db.commit()
                    logger.info(f"  Committed batch at {idx} places")
                
            except Exception as e:
                logger.error(f"Error seeding place {place_data.get('name', 'unknown')}: {str(e)}")
                db.rollback()
                raise
        
        # Final commit
        db.commit()
        
        # Summary
        logger.info("=" * 80)
        logger.info("SEEDING COMPLETE")
        logger.info(f"Total places seeded: {len(places_data)}")
        logger.info(f"Places with embeddings: {places_with_embeddings}")
        logger.info(f"Places without embeddings: {places_without_embeddings}")
        logger.info(f"Success rate: {places_with_embeddings}/{len(places_data)} ({100*places_with_embeddings/len(places_data):.1f}%)")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Seeding failed: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Seed the database with places")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force reseed by truncating existing data"
    )
    
    args = parser.parse_args()
    
    try:
        seed_database(force=args.force)
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)