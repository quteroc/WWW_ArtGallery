"""
Data ingestion script to populate database from ML datasets.
"""
import os
import asyncio
import logging
import random
from pathlib import Path
from typing import Dict, List, Tuple
import torch
from sqlmodel import select, SQLModel
from app.db.session import async_session, engine
from app.models.category import Category
from app.models.artwork import Artwork

# Concise logging; silence SQL engine spam
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("app.scripts.seed_data")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)

def parse_filename(filename: str) -> Tuple[str, str]:
    """
    Parse artwork filename to extract artist and title.
    Example: "claude-monet_water-lilies-1916.jpg" -> ("Claude Monet", "Water Lilies 1916")
    """
    basename = os.path.splitext(filename)[0]
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

async def load_or_create_categories(styles: List[str], quiet: bool = True) -> Dict[str, Category]:
    """Load existing categories or create new ones."""
    async with async_session() as session:
        categories: Dict[str, Category] = {}
        for style in styles:
            slug = slugify(style)
            query = select(Category).where(Category.slug == slug)
            result = await session.execute(query)
            category = result.scalar_one_or_none()
            if not category:
                category = Category(name=style, slug=slug)
                session.add(category)
                if not quiet:
                    logger.info(f"Creating category: {style}")
            categories[style] = category
        await session.commit()
        return categories

def _score_from_dict(scores: dict) -> float:
    """Pick a popularity score, preferring Wikipedia 12-month normalized."""
    for key in ("wikipedia_views_normalized", "wikipedia_12m", "wikipedia"):
        if key in scores:
            try:
                return float(scores[key])
            except Exception:
                pass
    for v in scores.values():
        if isinstance(v, (int, float)):
            return float(v)
    return 0.0

def _norm_path(p: str) -> str:
    """Normalize path separators to forward slashes for consistent parsing."""
    return str(p).replace("\\", "/")

def load_popularity_scores(pt_file: str) -> Dict[str, float]:
    """
    Load popularity from a .pt file.

    Supported formats:
    - Dict[str, Dict]: absolute_path -> { 'google_trends_normalized': float, 'wikipedia_views_normalized': float, ... }
      Produces two keys per item:
        * "Style/Filename.jpg" (preferred)
        * "Filename.jpg" (fallback)
    - Dict[str, float]: filename -> score
    """
    if not os.path.exists(pt_file):
        logger.warning(f"Popularity scores file not found: {pt_file}")
        return {}
    try:
        data = torch.load(pt_file)
        pop: Dict[str, float] = {}
        if isinstance(data, dict) and data:
            sample_val = next(iter(data.values()))
            if isinstance(sample_val, dict):
                for abs_path, scores in data.items():
                    try:
                        norm = _norm_path(abs_path)
                        parts = norm.split("/")
                        if len(parts) < 2:
                            continue
                        filename = parts[-1]
                        style = parts[-2]
                        value = _score_from_dict(scores)
                        pop[f"{style}/{filename}"] = value
                        if filename not in pop:
                            pop[filename] = value
                    except Exception:
                        continue
                return pop
            # already filename->float
            return {k: float(v) for k, v in data.items()}
        return {}
    except Exception as e:
        logger.error(f"Error loading popularity scores: {e}")
        return {}

async def seed_artworks(
    wikiart_dir: str,
    popularity_scores: Dict[str, float] | None = None,
    top_percentage: float = 0.1,
    quiet: bool = True,
    update_existing: bool = True,
):
    """
    Seed database with artwork data.

    Behavior:
    - If popularity_scores provided: rank by score per style and keep top_percentage for adding new rows, but update popularity for ALL existing rows.
    - If no popularity_scores: randomly sample per style by top_percentage (deterministic) for adding new rows.
    - Existing rows: updated (popularity_score and image_url) when update_existing=True.
    """
    if not os.path.exists(wikiart_dir):
        logger.warning(f"WikiArt directory not found: {wikiart_dir}")
        return

    styles = [d for d in os.listdir(wikiart_dir) if os.path.isdir(os.path.join(wikiart_dir, d))]
    if not styles:
        logger.warning("No style folders found in WikiArt directory")
        return

    await load_or_create_categories(styles, quiet=True)

    async with async_session() as session:
        total_added = 0
        rng = random.Random(42)  # deterministic random
        for style in sorted(styles):
            style_dir = os.path.join(wikiart_dir, style)
            image_files = [f for f in os.listdir(style_dir) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
            scanned = len(image_files)
            if scanned == 0:
                if not quiet:
                    logger.info(f"{style}: scanned=0 kept=0 added=0 with_pop>0=0")
                continue

            # Build lookup for this style
            def lookup_score(img: str) -> float:
                if not popularity_scores:
                    return 0.0
                key_style = f"{style}/{img}"
                return float(popularity_scores.get(key_style, popularity_scores.get(img, 0.0)))

            # Determine which new images to add
            keep_set = set()
            if popularity_scores:
                scored = [(img, lookup_score(img)) for img in image_files]
                scored.sort(key=lambda x: x[1], reverse=True)
                keep_count = max(1, int(len(scored) * top_percentage))
                keep_set = {img for img, _ in scored[:keep_count]}
            else:
                # Random sample by top_percentage
                keep_count = max(1, int(len(image_files) * top_percentage))
                tmp = image_files[:]
                rng.shuffle(tmp)
                keep_set = set(tmp[:keep_count])

            kept = len(keep_set)
            added = 0
            with_pop_gt0 = 0

            # Update existing rows for ALL files; add only for keep_set
            for image_file in image_files:
                image_path = f"ml/input/wikiart/{style}/{image_file}"
                result = await session.execute(select(Artwork).where(Artwork.image_path == image_path))
                existing = result.scalar_one_or_none()

                score = lookup_score(image_file)
                if score > 0:
                    with_pop_gt0 += 1

                if existing:
                    if update_existing:
                        existing.popularity_score = score
                        existing.image_url = f"/static/artworks/{style}/{image_file}"
                else:
                    if image_file in keep_set:
                        artist, title = parse_filename(image_file)
                        artwork = Artwork(
                            title=title,
                            artist=artist,
                            style=style,
                            image_path=image_path,
                            image_url=f"/static/artworks/{style}/{image_file}",
                            popularity_score=score,
                            views=0,
                            is_active=True,
                        )
                        session.add(artwork)
                        added += 1
                        total_added += 1

            await session.commit()
            logger.info(f"{style}: scanned={scanned} kept={kept} added={added} with_pop>0={with_pop_gt0}")

        logger.info(f"TOTAL: styles={len(styles)} artworks_added={total_added}")

async def main():
    """Main entry point for data seeding."""
    logger.info("=" * 60)
    logger.info("Classic Art Gallery - Data Seeding Script")
    logger.info("=" * 60)

    project_root = Path(__file__).parent.parent.parent.parent
    wikiart_dir = project_root / "ml" / "input" / "wikiart"
    popularity_file = project_root / "ml" / "output" / "artwork_popularity_by_artist.pt"

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    popularity_scores = load_popularity_scores(str(popularity_file))
    await seed_artworks(
        str(wikiart_dir),
        popularity_scores=popularity_scores if popularity_scores else None,
        top_percentage=0.1,
        quiet=True,
        update_existing=True,
    )

    logger.info("=" * 60)
    logger.info("Data seeding completed!")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())