# Testing Guide

## Unit Testing Pipes

```python
import pytest
from rivusio import BasePipe

class TestDataPipe(BasePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        return {"processed": data["value"] * 2}

@pytest.mark.asyncio
async def test_data_pipe():
    pipe = TestDataPipe()
    result = await pipe.process({"value": 5})
    assert result["processed"] == 10

@pytest.mark.asyncio
async def test_pipe_error_handling():
    pipe = TestDataPipe()
    with pytest.raises(PipeError):
        await pipe.process({"invalid": "data"})
```

## Pipeline Testing

```python
@pytest.mark.asyncio
async def test_pipeline_composition():
    pipe1 = TestDataPipe()
    pipe2 = TransformPipe()
    
    pipeline = Pipeline([pipe1, pipe2])
    result = await pipeline.process({"value": 5})
    
    assert result["transformed"]
    assert pipeline.get_pipe_outputs(pipe1)[0]["processed"] == 10
```

## Mocking External Dependencies

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_api_pipe():
    mock_api = AsyncMock(return_value={"api_data": "test"})
    
    with patch("external_api.fetch_data", mock_api):
        pipe = ApiPipe()
        result = await pipe.process({"id": 1})
        assert result["api_data"] == "test"
```