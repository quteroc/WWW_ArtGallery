"""
Artists API endpoints for artwork metadata.
"""
import torch
import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/artists", tags=["artists"])


class ArtistDescriptionResponse(BaseModel):
    """Response model for artist description."""
    artist: str
    description: str


def load_artist_descriptions():
    """Load artist descriptions from the torch file."""
    descriptions_path = os.path.join(
        os.path.dirname(__file__), 
        "../../../../ml/output/artist_descriptions.pt"
    )
    
    if os.path.exists(descriptions_path):
        try:
            return torch.load(descriptions_path)
        except Exception as e:
            print(f"Error loading artist descriptions: {e}")
    
    return {}


# Cache descriptions on startup
_artist_descriptions = load_artist_descriptions()


@router.get("/{artist_name}/description", response_model=ArtistDescriptionResponse)
async def get_artist_description(artist_name: str):
    """
    Get description for a specific artist.
    
    - **artist_name**: Name of the artist
    
    Returns 200 with artist description or 404 if not found.
    """
    if not _artist_descriptions:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Artist descriptions not available"
        )
    
    # Try exact match first
    if artist_name in _artist_descriptions:
        return ArtistDescriptionResponse(
            artist=artist_name,
            description=_artist_descriptions[artist_name]
        )
    
    # Try case-insensitive match
    for key, desc in _artist_descriptions.items():
        if key.lower() == artist_name.lower():
            return ArtistDescriptionResponse(
                artist=key,
                description=desc
            )
    
    # If not found, return generic description
    return ArtistDescriptionResponse(
        artist=artist_name,
        description=f"{artist_name} is a renowned artist known for exceptional artistic contributions."
    )


@router.get("/{artist_name}", response_model=ArtistDescriptionResponse)
async def get_artist(artist_name: str):
    """Alias for get_artist_description."""
    return await get_artist_description(artist_name)
