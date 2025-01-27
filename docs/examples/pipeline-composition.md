# Pipeline Composition Example

This example demonstrates different ways to compose pipelines in Rivusio.

## Basic Composition

```python
from rivusio import Pipeline, ConfigurablePipe, PipeConfig
from typing import Dict, List

# Define pipes
class FilterConfig(PipeConfig):
    min_value: float

class FilterPipe(ConfigurablePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        if data["value"] >= self.config.min_value:
            return data
        return None

class TransformPipe(ConfigurablePipe[Dict, Dict]):
    async def process(self, data: Dict) -> Dict:
        data["value"] *= 2
        return data

# Create pipeline
filter_pipe = FilterPipe(FilterConfig(min_value=10))
transform_pipe = TransformPipe()

pipeline = Pipeline()
pipeline.add_pipe(filter_pipe)
pipeline.add_pipe(transform_pipe)
```

## Using Operators

```python
# Using the >> operator
pipeline = filter_pipe >> transform_pipe

# Process data
data = {"value": 15}
result = await pipeline.process(data)  # {"value": 30}
```

## Branching Pipelines

```python
class BranchConfig(PipeConfig):
    threshold: float

class BranchPipe(ConfigurablePipe[Dict, Dict]):
    def __init__(self, config: BranchConfig):
        super().__init__(config)
        self.high_branch = Pipeline()
        self.low_branch = Pipeline()
    
    async def process(self, data: Dict) -> Dict:
        if data["value"] >= self.config.threshold:
            return await self.high_branch.process(data)
        return await self.low_branch.process(data)

# Create branching pipeline
branch = BranchPipe(BranchConfig(threshold=20))
branch.high_branch.add_pipe(TransformPipe())
branch.low_branch.add_pipe(FilterPipe(FilterConfig(min_value=5)))
```

## Parallel Processing

```python
from asyncio import gather

class ParallelPipeline(Pipeline):
    def __init__(self, pipes: List[Pipeline]):
        super().__init__()
        self.pipes = pipes
    
    async def process(self, data: Dict) -> List[Dict]:
        tasks = [pipe.process(data) for pipe in self.pipes]
        return await gather(*tasks)

# Create parallel pipelines
pipe1 = Pipeline([FilterPipe(FilterConfig(min_value=10))])
pipe2 = Pipeline([TransformPipe()])

parallel = ParallelPipeline([pipe1, pipe2])
```

## Error Handling

```python
class SafePipeline(Pipeline):
    async def process(self, data: Dict) -> Dict:
        try:
            return await super().process(data)
        except Exception as e:
            print(f"Error in pipeline: {e}")
            return None

# Create safe pipeline
safe = SafePipeline()
safe.add_pipe(filter_pipe)
safe.add_pipe(transform_pipe)
```

## Full Example

```python
async def main():
    # Create pipes
    filter_pipe = FilterPipe(FilterConfig(min_value=10))
    transform_pipe = TransformPipe()
    
    # Create branching pipeline
    branch = BranchPipe(BranchConfig(threshold=20))
    branch.high_branch.add_pipe(transform_pipe)
    branch.low_branch.add_pipe(filter_pipe)
    
    # Create safe pipeline
    pipeline = SafePipeline()
    pipeline.add_pipe(filter_pipe)
    pipeline.add_pipe(branch)
    pipeline.add_pipe(transform_pipe)
    
    # Process data
    data = {"value": 25}
    result = await pipeline.process(data)
    print(result)  # {"value": 100}

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Best Practices

1. Keep pipelines focused and modular
2. Use appropriate error handling
3. Consider performance implications
4. Document pipeline behavior
5. Test pipeline components
6. Monitor pipeline execution
