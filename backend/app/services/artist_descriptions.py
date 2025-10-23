"""
Artist description loader service.
Loads and caches artist descriptions from ML output file.
"""
import re
import torch
from typing import Optional, Dict
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

# Module-level cache
_descriptions_cache: Optional[Dict[str, Dict]] = None

# Try multiple possible paths for the descriptions file
_POSSIBLE_PATHS = [
    Path("/app/ml/output/artist_descriptions.pt"),
    Path(os.path.join(os.path.dirname(__file__), "../../../ml/output/artist_descriptions.pt")),
]


def slugify_artist(artist_name: str) -> str:
    """
    Convert artist name to slug format matching the .pt file keys.
    
    Examples:
        'Utagawa Kuniyoshi' -> 'utagawa_kuniyoshi'
        'Vincent van Gogh' -> 'vincent_van_gogh'
        'Claude Monet' -> 'claude_monet'
    
    Args:
        artist_name: Artist name to slugify
        
    Returns:
        Slugified artist name
    """
    # Convert to lowercase
    slug = artist_name.lower()
    # Replace non-alphanumeric characters with underscore
    slug = re.sub(r'[^a-z0-9]+', '_', slug)
    # Remove leading/trailing underscores
    slug = slug.strip('_')
    # Collapse multiple underscores
    slug = re.sub(r'_+', '_', slug)
    return slug


def _load_descriptions() -> Dict[str, Dict]:
    """
    Load artist descriptions from .pt file into memory.
    
    Returns:
        Dictionary mapping slugified artist names to description data
    """
    global _descriptions_cache
    
    if _descriptions_cache is not None:
        return _descriptions_cache
    
    try:
        # Try to find the file in possible paths
        descriptions_path = None
        for path in _POSSIBLE_PATHS:
            if path.exists():
                descriptions_path = path
                break
        
        if descriptions_path is None:
            logger.warning(f"Artist descriptions file not found in any of: {_POSSIBLE_PATHS}")
            _descriptions_cache = {}
            return _descriptions_cache
        
        # Load the torch file
        descriptions = torch.load(descriptions_path, map_location='cpu')
        
        if not isinstance(descriptions, dict):
            logger.error(f"Artist descriptions file has unexpected format: {type(descriptions)}")
            _descriptions_cache = {}
            return _descriptions_cache
        
        _descriptions_cache = descriptions
        logger.info(f"Loaded {len(_descriptions_cache)} artist descriptions from {descriptions_path}")
        return _descriptions_cache
        
    except Exception as e:
        logger.error(f"Error loading artist descriptions: {e}")
        _descriptions_cache = {}
        return _descriptions_cache


def get_description(artist_name: str) -> Optional[str]:
    """
    Get the best available description for an artist.
    
    Priority order:
    1. llm_standard_description
    2. wikipedia_description
    3. google_arts_description
    4. rijksmuseum_works
    
    Args:
        artist_name: Name of the artist
        
    Returns:
        Artist description or None if not found
    """
    descriptions = _load_descriptions()
    
    # Convert artist name to slug
    slug = slugify_artist(artist_name)
    
    # Check if artist exists in cache
    if slug not in descriptions:
        return None
    
    artist_data = descriptions[slug]
    
    # Try to get description in priority order
    for field in ['llm_standard_description', 'wikipedia_description', 
                  'google_arts_description', 'rijksmuseum_works']:
        if field in artist_data and artist_data[field]:
            desc = artist_data[field]
            # Ensure it's a string and not empty after stripping
            if isinstance(desc, str) and desc.strip():
                return desc.strip()
    
    return None


def get_description_snippet(artist_name: str, max_lines: int = 3) -> Optional[str]:
    """
    Get a short snippet of the artist description.
    
    Args:
        artist_name: Name of the artist
        max_lines: Maximum number of lines to return (approximate)
        
    Returns:
        Short description snippet or None if not found
    """
    description = get_description(artist_name)
    
    if not description:
        return None
    
    # Split into sentences and take first few
    sentences = description.split('. ')
    
    # Take first 2-3 sentences as snippet
    snippet_sentences = sentences[:min(2, len(sentences))]
    snippet = '. '.join(snippet_sentences)
    
    # Add ellipsis if there's more content
    if len(sentences) > 2:
        if not snippet.endswith('.'):
            snippet += '.'
        snippet += '...'
    elif not snippet.endswith('.'):
        snippet += '.'
    
    return snippet


def reload_descriptions():
    """Force reload of artist descriptions from file."""
    global _descriptions_cache
    _descriptions_cache = None
    _load_descriptions()
