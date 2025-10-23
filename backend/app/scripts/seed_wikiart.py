"""
CLI wrapper for seeding WikiArt data into the database.

Usage:
    docker compose exec backend python -m app.scripts.seed_wikiart --wikiart-dir /app/ml/input/wikiart --top 0.01
    docker compose exec backend python -m app.scripts.seed_wikiart --wikiart-dir /app/ml/input/wikiart --top 0.1 --popularity-pt /app/ml/output/popularity.pt
"""
import asyncio
import argparse
import logging
from pathlib import Path
from app.scripts.seed_data import seed_artworks, load_popularity_scores

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """CLI entry point for seeding WikiArt data."""
    parser = argparse.ArgumentParser(
        description="Seed WikiArt artwork data into the database"
    )
    parser.add_argument(
        "--wikiart-dir",
        type=str,
        required=True,
        help="Path to WikiArt directory (e.g., /app/ml/input/wikiart)",
    )
    parser.add_argument(
        "--top",
        type=float,
        default=0.1,
        help="Keep only top X percentage of artworks per style (default: 0.1 = 10%%)",
    )
    parser.add_argument(
        "--popularity-pt",
        type=str,
        default=None,
        help="Optional path to popularity scores .pt file",
    )
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("WikiArt Data Seeding CLI")
    logger.info("=" * 60)
    logger.info(f"WikiArt directory: {args.wikiart_dir}")
    logger.info(f"Top percentage: {args.top * 100}%")
    
    # Load popularity scores if provided
    popularity_scores = {}
    if args.popularity_pt:
        logger.info(f"Loading popularity scores from: {args.popularity_pt}")
        popularity_scores = load_popularity_scores(args.popularity_pt)
    else:
        logger.info("No popularity scores provided - all artworks will have score 0.0")
    
    # Run seeding
    asyncio.run(
        seed_artworks(
            wikiart_dir=args.wikiart_dir,
            popularity_scores=popularity_scores,
            top_percentage=args.top,
        )
    )
    
    logger.info("=" * 60)
    logger.info("Seeding completed successfully!")
    logger.info("=" * 60)
    logger.info("You can now view the gallery at: http://localhost:8000/")


if __name__ == "__main__":
    main()
