"""
Tests for artist description service.
"""
import pytest
from app.services.artist_descriptions import (
    slugify_artist,
    get_description,
    get_description_snippet,
    reload_descriptions
)


def test_slugify_artist():
    """Test artist name slugification."""
    assert slugify_artist("Utagawa Kuniyoshi") == "utagawa_kuniyoshi"
    assert slugify_artist("Vincent van Gogh") == "vincent_van_gogh"
    assert slugify_artist("Claude Monet") == "claude_monet"
    assert slugify_artist("Aaron Siskind") == "aaron_siskind"
    assert slugify_artist("UPPERCASE NAME") == "uppercase_name"
    assert slugify_artist("Name-With-Hyphens") == "name_with_hyphens"
    assert slugify_artist("Name  Multiple  Spaces") == "name_multiple_spaces"
    assert slugify_artist("Name's with apostrophe") == "name_s_with_apostrophe"


def test_get_description_existing_artist():
    """Test getting description for existing artist."""
    # Test with artists from our test file
    desc = get_description("Rembrandt")
    assert desc is not None
    assert "Dutch Golden Age" in desc or "Dutch draughtsman" in desc
    
    desc = get_description("Aaron Siskind")
    assert desc is not None
    assert len(desc) > 0


def test_get_description_nonexistent_artist():
    """Test getting description for nonexistent artist."""
    desc = get_description("Nonexistent Artist Name")
    assert desc is None


def test_get_description_priority_order():
    """Test that description priority order is correct."""
    # Rembrandt has llm_standard_description, wikipedia_description, and google_arts_description
    desc = get_description("Rembrandt")
    assert desc is not None
    # Should get llm_standard_description first
    assert "Dutch Golden Age" in desc
    
    # Abdullah has only llm_standard_description
    desc = get_description("Abdullah Suriosubroto")
    assert desc is not None
    assert "Indonesian" in desc


def test_get_description_snippet():
    """Test getting description snippet."""
    snippet = get_description_snippet("Rembrandt")
    assert snippet is not None
    
    # Snippet should be shorter or equal to full description
    full_desc = get_description("Rembrandt")
    assert len(snippet) <= len(full_desc)
    
    # Should end with period or ellipsis
    assert snippet.endswith('.') or snippet.endswith('...')
    
    # Test with an artist that has a multi-sentence description
    snippet_long = get_description_snippet("Claude Monet")
    full_long = get_description("Claude Monet")
    # Both should have content
    assert snippet_long is not None
    assert full_long is not None


def test_get_description_snippet_nonexistent():
    """Test getting snippet for nonexistent artist."""
    snippet = get_description_snippet("Nonexistent Artist")
    assert snippet is None


def test_get_description_case_insensitive():
    """Test that artist name matching is case insensitive."""
    desc1 = get_description("rembrandt")
    desc2 = get_description("REMBRANDT")
    desc3 = get_description("Rembrandt")
    
    assert desc1 is not None
    assert desc1 == desc2
    assert desc2 == desc3


def test_reload_descriptions():
    """Test reloading descriptions from file."""
    # Get a description to ensure it's loaded
    desc1 = get_description("Rembrandt")
    assert desc1 is not None
    
    # Reload
    reload_descriptions()
    
    # Get same description again
    desc2 = get_description("Rembrandt")
    assert desc2 is not None
    assert desc1 == desc2
