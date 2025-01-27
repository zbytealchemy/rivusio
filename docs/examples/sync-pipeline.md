# Synchronous Pipeline Examples

## Basic Sync Pipeline

```python
from rivusio import SyncBasePipe
from typing import Dict, List

class NumberFilterPipe(SyncBasePipe[Dict, Dict]):
    def process(self, data: Dict) -> Dict:
        return {k: v for k, v in data.items() if isinstance(v, (int, float))}

class SumPipe(SyncBasePipe[Dict, float]):
    def process(self, data: Dict) -> float:
        return sum(data.values())

def main():
    # Create pipeline
    pipeline = NumberFilterPipe() >> SumPipe()
    
    # Process data
    data = {"a": 10, "b": "text", "c": 20, "d": 30.5}
    result = pipeline(data)  # 60.5
    print(f"Sum of numbers: {result}")

if __name__ == "__main__":
    main()
```

## Batch Processing Example

```python
from rivusio import SyncBasePipe, PipeConfig
from typing import List
from pydantic import BaseModel, Field

class BatchConfig(PipeConfig):
    threshold: float = Field(gt=0)

class Transaction(BaseModel):
    id: str
    amount: float
    currency: str

class BatchFilterPipe(SyncBasePipe[List[Transaction], List[Transaction]]):
    def __init__(self, config: BatchConfig):
        self.config = config
    
    def process(self, transactions: List[Transaction]) -> List[Transaction]:
        return [t for t in transactions if t.amount > self.config.threshold]

class CurrencyNormalizePipe(SyncBasePipe[List[Transaction], List[Transaction]]):
    def process(self, transactions: List[Transaction]) -> List[Transaction]:
        return [
            Transaction(
                id=t.id,
                amount=t.amount,
                currency=t.currency.upper()
            ) for t in transactions
        ]

def main():
    # Sample data
    transactions = [
        Transaction(id="1", amount=100.0, currency="usd"),
        Transaction(id="2", amount=50.0, currency="eur"),
        Transaction(id="3", amount=200.0, currency="gbp"),
    ]
    
    # Create pipeline
    pipeline = BatchFilterPipe(BatchConfig(threshold=75.0)) >> CurrencyNormalizePipe()
    
    # Process batch
    result = pipeline(transactions)
    for t in result:
        print(f"Processed: {t}")

if __name__ == "__main__":
    main()
```
