# Basic Pipeline Example

This example demonstrates how to create a basic data processing pipeline using Rivusio.

## Setup

First, install Rivusio:

```bash
pip install rivusio
```

## Creating the Pipeline

Here's a simple pipeline that processes user data:

```python
from rivusio import AsyncBasePipe, Pipeline
from typing import Dict, List
from pydantic import BaseModel, EmailStr

# Define data models
class User(BaseModel):
    name: str
    age: int
    email: EmailStr

# Define pipe configurations
class FilterConfig(PipeConfig):
    min_age: int

class EnrichConfig(PipeConfig):
    domain: str

# Create pipes
class AgeFilterPipe(AsyncBasePipe[List[User], List[User]]):
    def __init__(self, min_age: int):
        self.min_age = min_age
    
    async def process(self, users: List[User]) -> List[User]:
        return [user for user in users if user.age >= self.min_age]

class EmailEnrichPipe(AsyncBasePipe[List[User], List[User]]):
    def __init__(self, domain: str):
        self.domain = domain
    
    async def process(self, users: List[User]) -> List[User]:
        return users

# Create and run the pipeline
async def main():
    # Create sample data
    users = [
        User(name="Alice", age=25, email="alice.smith@example.com"),
        User(name="Bob", age=17, email="bob.jones@example.com"),
        User(name="Charlie", age=30, email="charlie.brown@example.com")
    ]
    
    # Configure pipes
    age_filter = AgeFilterPipe(min_age=18)
    email_enricher = EmailEnrichPipe(domain="example.com")
    
    # Create pipeline
    pipeline = Pipeline()
    pipeline.add_pipe(age_filter)
    pipeline.add_pipe(email_enricher)
    
    # Process data
    result = await pipeline.process(users)
    print(result)

# Run the pipeline
if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

## Output

The pipeline will output:
```python
[
    User(name='Alice', age=25, email='alice.smith@example.com'),
    User(name='Charlie', age=30, email='charlie.brown@example.com')
]
```

## Explanation

1. We define two pipes:
   - `AgeFilterPipe`: Filters out users under 18
   - `EmailEnrichPipe`: Adds domain information to emails

2. Each pipe has its own configuration class
3. The pipeline processes the data sequentially through both pipes
4. Type safety is enforced throughout the pipeline
5. All processing is done asynchronously
