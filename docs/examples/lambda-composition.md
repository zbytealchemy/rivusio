# Lambda Composition Example

This example shows how to use lambda functions and functional composition in Rivusio.

## Basic Lambda Pipe

```python
from rivusio import ConfigurablePipe, PipeConfig
from typing import Callable, Dict, Any

class LambdaConfig(PipeConfig):
    func: Callable
    args: tuple = ()
    kwargs: Dict[str, Any] = {}

class LambdaPipe(ConfigurablePipe[Any, Any]):
    async def process(self, data: Any) -> Any:
        return self.config.func(data, *self.config.args, **self.config.kwargs)
```

## Using Lambda Pipes

```python
# Create lambda pipes
multiply = LambdaPipe(LambdaConfig(
    func=lambda x, y: x * y,
    args=(2,)
))

add = LambdaPipe(LambdaConfig(
    func=lambda x, y: x + y,
    args=(5,)
))

# Compose pipes
pipeline = multiply >> add

# Process data
result = await pipeline.process(10)  # (10 * 2) + 5 = 25
```

## Functional Composition

```python
from functools import partial

class FunctionalPipe(ConfigurablePipe[Any, Any]):
    def __init__(self, func: Callable):
        super().__init__(PipeConfig())
        self.func = func
    
    async def process(self, data: Any) -> Any:
        return self.func(data)

# Create functional pipes
double = FunctionalPipe(lambda x: x * 2)
increment = FunctionalPipe(lambda x: x + 1)
square = FunctionalPipe(lambda x: x ** 2)

# Compose pipes
pipeline = double >> increment >> square
```

## Higher-Order Functions

```python
def create_filter(predicate: Callable[[Any], bool]) -> FunctionalPipe:
    async def filter_func(data: Any) -> Any:
        return data if predicate(data) else None
    return FunctionalPipe(filter_func)

def create_map(func: Callable) -> FunctionalPipe:
    return FunctionalPipe(func)

# Create pipes using higher-order functions
is_positive = create_filter(lambda x: x > 0)
double = create_map(lambda x: x * 2)
```

## Advanced Example

```python
from typing import List
from dataclasses import dataclass

@dataclass
class Record:
    value: float
    category: str

class DataPipeline:
    def __init__(self):
        self.pipeline = (
            create_filter(lambda x: x.value > 0)
            >> create_map(lambda x: Record(x.value * 2, x.category))
            >> create_filter(lambda x: x.category in ["A", "B"])
        )
    
    async def process(self, records: List[Record]) -> List[Record]:
        results = []
        for record in records:
            result = await self.pipeline.process(record)
            if result:
                results.append(result)
        return results

# Use the pipeline
async def main():
    pipeline = DataPipeline()
    
    records = [
        Record(10, "A"),
        Record(-5, "B"),
        Record(15, "C"),
        Record(20, "A")
    ]
    
    results = await pipeline.process(records)
    for record in results:
        print(f"Value: {record.value}, Category: {record.category}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Composition with Error Handling

```python
def safe_pipe(pipe: FunctionalPipe) -> FunctionalPipe:
    async def safe_process(data: Any) -> Any:
        try:
            return await pipe.process(data)
        except Exception as e:
            print(f"Error in pipe: {e}")
            return None
    return FunctionalPipe(safe_process)

# Create safe pipeline
safe_pipeline = (
    safe_pipe(double)
    >> safe_pipe(increment)
    >> safe_pipe(square)
)
```

## Best Practices

1. Keep functions pure and simple
2. Use type hints for better safety
3. Handle errors appropriately
4. Document function behavior
5. Test composition chains
6. Consider performance implications
