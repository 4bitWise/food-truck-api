import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from pymongo.collection import Collection

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from routes.menu import validate_option_names

@pytest.mark.asyncio
async def test_validate_option_names_success(mocker):
    """Test when all option names exist in the database."""
    # Mock the options collection
    mock_options_collection = mocker.patch("routes.menu.options_collection")

    # Simulate MongoDB cursor behavior (cursor-like object returning a list)
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = [{"name": "Cheese"}, {"name": "Bacon"}]
    mock_options_collection.find.return_value = mock_cursor

    # Test valid option names (should NOT raise an exception)
    await validate_option_names(["Cheese", "Bacon"])

@pytest.mark.asyncio
async def test_validate_option_names_failure(mocker):
    """Test when some option names do not exist in the database."""
    # Mock the options collection
    mock_options_collection = mocker.patch("routes.menu.options_collection")

    # Simulate MongoDB cursor behavior
    mock_cursor = MagicMock()
    mock_cursor.__iter__.return_value = [{"name": "Cheese"}]  # Only "Cheese" exists
    mock_options_collection.find.return_value = mock_cursor

    # Test with an invalid option (should raise HTTPException)
    with pytest.raises(HTTPException) as exc_info:
        await validate_option_names(["Cheese", "Bacon"])  # "Bacon" is missing

    assert exc_info.value.status_code == 400
    assert "Option(s) not found: Bacon" in str(exc_info.value)
