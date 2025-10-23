"""
Seed database with artworks that exist on CDN (no local files needed).

This script creates artwork records using image URLs from cdn_artworks_list.txt
that exist on the DigitalOcean Spaces CDN. Perfect for deployment where the 70GB
WikiArt dataset is not available locally.

Usage:
    docker compose exec backend python -m app.scripts.seed_from_cdn
"""
import asyncio
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple
from sqlmodel import select
from app.db.session import async_session, engine
from app.models.category import Category
from app.models.artwork import Artwork
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def parse_cdn_filename(style: str, filename: str) -> Tuple[str, str]:
    """
    Parse artwork filename to extract artist and title.
    Example: "claude-monet_water-lilies-1916.jpg" -> ("Claude Monet", "Water Lilies 1916")
    """
    basename = filename.replace(".jpg", "").replace(".jpeg", "").replace(".png", "")
    parts = basename.split("_", 1)
    if len(parts) == 2:
        artist = parts[0].replace("-", " ").title()
        title = parts[1].replace("-", " ").title()
    else:
        artist = "Unknown Artist"
        title = basename.replace("-", " ").title()
    return artist, title


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    return text.lower().replace(" ", "-").replace("_", "-")


def load_cdn_artworks_from_file() -> List[Tuple[str, str, float]]:
    """
    Load artwork list from cdn_artworks_list.txt file.
    Returns list of (style, filename, popularity_score) tuples.
    """
    artworks = []
    script_dir = Path(__file__).parent
    list_file = script_dir / "cdn_artworks_list.txt"
    
    if not list_file.exists():
        logger.error(f"cdn_artworks_list.txt not found at {list_file}")
        return []
    
    with open(list_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or '/' not in line:
                continue
            
            parts = line.split('/')
            if len(parts) >= 2:
                style = parts[0]
                filename = parts[1]
                # Default popularity score (can be customized)
                popularity = 0.75
                artworks.append((style, filename, popularity))
    
    logger.info(f"Loaded {len(artworks)} artworks from file")
    return artworks


# Load artworks from file
CDN_ARTWORKS = load_cdn_artworks_from_file()


async def seed_cdn_artworks():
    """Seed database with CDN artwork records."""
    logger.info("=" * 60)
    logger.info("Seeding artworks from CDN (no local files needed)")
    logger.info("=" * 60)
    
    # Get unique styles
    styles = list(set(style for style, _, _ in CDN_ARTWORKS))
    
    # Create categories
    async with async_session() as session:
        logger.info(f"Creating {len(styles)} categories...")
        for style in styles:
            slug = slugify(style)
            result = await session.execute(
                select(Category).where(Category.slug == slug)
            )
            existing = result.scalar_one_or_none()
            if not existing:
                category = Category(name=style, slug=slug)
                session.add(category)
                logger.info(f"  - {style}")
        await session.commit()
    
    # Create artworks
    async with async_session() as session:
        added = 0
        skipped = 0
        
        logger.info(f"\nProcessing {len(CDN_ARTWORKS)} artworks...")
        
        for style, filename, popularity in CDN_ARTWORKS:
            # Check if exists
            image_path = f"ml/input/wikiart/{style}/{filename}"
            result = await session.execute(
                select(Artwork).where(Artwork.image_path == image_path)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                # Update with CDN URL
                base_url = settings.ARTWORKS_BASE_URL.rstrip("/")
                existing.image_url = f"{base_url}/{style}/{filename}"
                existing.popularity_score = popularity
                skipped += 1
            else:
                # Parse filename for artist/title
                artist, title = parse_cdn_filename(style, filename)
                
                # Construct CDN URL
                base_url = settings.ARTWORKS_BASE_URL.rstrip("/")
                cdn_url = f"{base_url}/{style}/{filename}"
                
                # Create new artwork
                artwork = Artwork(
                    title=title,
                    artist=artist,
                    style=style,
                    image_path=image_path,
                    image_url=cdn_url,  # Use CDN URL directly
                    popularity_score=popularity,
                    views=0,
                    is_active=True,
                )
                session.add(artwork)
                added += 1
                
                if added % 10 == 0:
                    logger.info(f"  Added {added} artworks...")
        
        await session.commit()
        
        logger.info("=" * 60)
        logger.info(f"SUMMARY:")
        logger.info(f"  Styles: {len(styles)}")
        logger.info(f"  Artworks added: {added}")
        logger.info(f"  Artworks updated: {skipped}")
        logger.info(f"  Total: {added + skipped}")
        logger.info("=" * 60)
        logger.info("\n✅ Gallery ready at: http://localhost:8000/")


async def main():
    """Main entry point."""
    await seed_cdn_artworks()


if __name__ == "__main__":
    asyncio.run(main())
