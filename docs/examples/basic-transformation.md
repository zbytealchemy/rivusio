# Basic Transformation Example

This example demonstrates how to perform basic data transformations using Rivusio.

## Setup

```python
from rivusio import AsyncBasePipe
from rivusio.config import PipeConfig
from typing import Dict, List
from pydantic import BaseModel, Field

# Define data model
class Record(BaseModel):
    id: int
    value: float
    category: str
```

## Create Configuration

```python
class TransformConfig(PipeConfig):
    multiply_by: float = Field(default=1.0, gt=0)
    categories: List[str] = Field(default_factory=lambda: ["A", "B", "C"])
```

## Implement Transformation

```python
class TransformPipe(AsyncBasePipe[Record, Record]):
    def __init__(self, config: TransformConfig):
        super().__init__()
        self.config = config

    async def process(self, data: Record) -> Record:
        return Record(
            id=data.id,
            value=data.value * self.config.multiply_by,
            category=data.category
        )
```

## Use the Pipe

```python
async def main():
    config = TransformConfig(multiply_by=2.0)
    pipe = TransformPipe(config)
    
    data = Record(id=1, value=10.0, category="A")
    result = await pipe(data)
    print(result)  # Record(id=1, value=20.0, category='A')

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Explanation

1. We define a simple data model using Pydantic
2. We create a configuration class for our transformation
3. We implement a pipe that multiplies values by a configurable factor
4. We process data through the pipe asynchronously

## Next Steps

- Try adding more transformations
- Combine multiple pipes into a pipeline
- Add error handling and validation
- Explore streaming capabilities
