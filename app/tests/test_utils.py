import pytest
from unittest.mock import MagicMock
from fastapi import HTTPException
from pymongo.collection import Collection
from routes.menu import validate_option_names

@pytest.fixture
def mock_options_collection():
    mock_collection = MagicMock(Collection)
    return mock_collection

@pytest.mark.asyncio
async def test_validate_option_names(mock_options_collection):
    # Test when all options exist
    mock_options_collection.find.return_value = [
        {"name": "Cheese", "_id": "1"},
        {"name": "Bacon", "_id": "2"}
    ]
    await validate_option_names(["Cheese", "Bacon"])

    # Test when some options are missing
    mock_options_collection.find.return_value = [
        {"name": "Cheese", "_id": "1"}
    ]
    with pytest.raises(HTTPException) as exc:
        await validate_option_names(["Cheese", "Bacon"])
    
    assert exc.value.status_code == 400
    assert "Option(s) not found" in exc.value.detail
