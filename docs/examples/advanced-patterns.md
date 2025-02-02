# Advanced Usage Patterns

This guide demonstrates advanced usage patterns and real-world examples for Rivusio.

## 1. Real-time Data Processing

### Stock Market Data Processing

```python
import asyncio
from datetime import timedelta
from typing import List, Optional

import aiohttp
from rivusio import AsyncBasePipe, AsyncPipeline
from rivusio.streams import AsyncStream
from rivusio.config import StreamConfig


class StockDataFetcher(AsyncBasePipe[str, dict]):
    def __init__(self, api_key: str):
        super().__init__()
        self.api_key = api_key


    async def process(self, symbol: str) -> dict:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.example.com/v1/stocks/{symbol}?apikey={self.api_key}"
            async with session.get(url) as response:
                return await response.json()


class MovingAverageCalculator(AsyncBasePipe[dict, dict]):
    def __init__(self, window_size: int = 20):
        super().__init__()
        self.window_size = window_size
        self.prices: List[float] = []

    async def process(self, data: dict) -> dict:
        price = float(data["price"])
        self.prices.append(price)
        if len(self.prices) > self.window_size:
            self.prices.pop(0)

        data["moving_average"] = sum(self.prices) / len(self.prices)
        return data


class AlertGenerator(AsyncBasePipe[dict, Optional[str]]):
    def __init__(self, threshold: float = 0.1):
        super().__init__()
        self.threshold = threshold

    async def process(self, data: dict) -> Optional[str]:
        price = float(data["price"])
        ma = data["moving_average"]
        deviation = abs(price - ma) / ma

        if deviation > self.threshold:
            return f"Alert: {data['symbol']} price deviation {deviation:.2%}"
        return None


async def main():
    # Configure pipeline
    pipeline = AsyncPipeline([
        StockDataFetcher(api_key="your_key"),
        MovingAverageCalculator(window_size=20),
        AlertGenerator(threshold=0.1)
    ])

    # Configure stream
    config = StreamConfig(
        window_size=timedelta(minutes=5),
        batch_size=10
    )

    # Process stream
    async def symbols():
        for symbol in ["AAPL", "GOOGL", "MSFT"]:
            yield symbol

    stream = AsyncStream(symbols(), config=config)

    async with pipeline:
        async for alerts in stream.process(pipeline):
            if alerts:
                print(alerts)

if __name__ == "__main__":
    asyncio.run(main())
```

## 2. Error Handling and Retry Logic

### Robust HTTP Client

```python
import logging

from rivusio import AsyncBasePipe, AsyncPipeline
from rivusio.sync.parallel import ExecutionStrategy
from rivusio.monitoring import PipelineMonitor
import aiohttp
import asyncio
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class RobustHTTPClient(AsyncBasePipe[str, Optional[Dict[str, Any]]]):
    def __init__(
            self,
            max_retries: int = 3,
            base_delay: float = 1.0,
            max_delay: int = 3
    ):
        super().__init__()
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay

    async def process(self, url: str) -> Optional[Dict[str, Any]]:
        retries = 0
        while retries <= self.max_retries:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 429:
                            retry_after = int(response.headers.get("Retry-After", self.base_delay))
                            await asyncio.sleep(min(retry_after, self.max_delay))
                            continue

                        response.raise_for_status()
                        return await response.json()

            except aiohttp.ClientError as e:
                retries += 1
                if retries > self.max_retries:
                    logger.error(f"Failed to fetch {url}: {str(e)}")
                    return None

                delay = min(self.base_delay * (2 ** retries), self.max_delay)
                await asyncio.sleep(delay)

        return None


async def main():
    pipeline = AsyncPipeline([RobustHTTPClient(max_retries=3)])

    monitor = PipelineMonitor()
    pipeline.monitor = monitor
    pipeline.configure_parallel(ExecutionStrategy.THREAD_POOL, max_workers=5)

    urls = [
        "https://randomuser.me/api/",
        "http://worldtimeapi.org/api/timezone/Etc/UTC",
        "https://official-joke-api.appspot.com/jokes/random",
        "https://api64.ipify.org?format=json",
        "https://uselessfacts.jsph.pl/random.json?language=en"
    ]

    async with pipeline:
        pipeline.monitor.start()
        results = await pipeline.execute_parallel(urls)
        pipeline.monitor.stop()
        for result in results:
            logger.info(result)

    logger.info(pipeline.monitor.get_metrics())
```

## 3. Complex Data Transformation

### Log Processing Pipeline

```python
from rivusio import AsyncBasePipe, AsyncPipeline
from rivusio.streams import AsyncStream, StreamConfig
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional


class LogParser(AsyncBasePipe[str, Optional[Dict[str, Any]]]):
    def __init__(self):
        super().__init__()
        self.pattern = re.compile(
            r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) \[(\w+)\] (\w+): (.*)'
        )

    async def process(self, line: str) -> Optional[Dict[str, Any]]:
        match = self.pattern.match(line)
        if not match:
            return None

        timestamp, level, component, message = match.groups()
        return {
            "timestamp": datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S"),
            "level": level,
            "component": component,
            "message": message
        }


class ErrorAggregator(AsyncBasePipe[List[Dict[str, Any]], Dict[str, int]]):
    async def process(self, logs: List[Dict[str, Any]]) -> Dict[str, int]:
        error_counts = {}
        for log in logs:
            if log["level"] == "ERROR":
                component = log["component"]
                error_counts[component] = error_counts.get(component, 0) + 1
        return error_counts


class AlertFormatter(AsyncBasePipe[Dict[str, int], Optional[str]]):
    def __init__(self, threshold: int = 5):
        super().__init__()
        self.threshold = threshold


    async def process(self, error_counts: Dict[str, int]) -> Optional[str]:
        alerts = []
        for component, count in error_counts.items():
            if count >= self.threshold:
                alerts.append(
                    f"High error rate in {component}: {count} errors"
                )
        return "\n".join(alerts) if alerts else None


async def main():
    pipeline = AsyncPipeline(
        [
            LogParser(),
            ErrorAggregator(),
            AlertFormatter(threshold=5)
        ]
    )

    config = StreamConfig(
        window_size=timedelta(minutes=5),
        batch_size=100
    )

    async def log_generator():
        while True:
            with open("app.log", "r") as f:
                for line in f:
                    yield line
            await asyncio.sleep(1)

    stream = AsyncStream(log_generator(), config=config)

    async with pipeline:
        async for alert in stream.process(pipeline):
            if alert:
                print(alert)
```

## 4. Performance Optimization Example

### Parallel Data Processing

```python
import asyncio
from typing import List

import numpy as np
from rivusio import AsyncBasePipe, AsyncPipeline
from rivusio.sync.parallel import ExecutionStrategy
from rivusio.monitoring import PipelineMonitor


class DataPreprocessor(AsyncBasePipe[np.ndarray, np.ndarray]):
    async def process(self, data: np.ndarray) -> np.ndarray:
        # Simulate CPU-intensive preprocessing
        return np.fft.fft2(data)


class FeatureExtractor(AsyncBasePipe[np.ndarray, List[float]]):
    async def process(self, data: np.ndarray) -> List[float]:
        # Extract features from preprocessed data
        return [
            float(np.mean(data)),
            float(np.std(data)),
            float(np.max(data)),
            float(np.min(data))
        ]


class ModelPredictor(AsyncBasePipe[List[float], float]):
    def __init__(self):
        super().__init__()
        self.model = self._load_model()

    @classmethod
    def _func(cls, x: List[float]) -> float:
        if len(x) == 0:
            return 0
        return sum(x) / len(x)

    @classmethod
    def _load_model(cls):
        # Simulate model loading
        return cls._func

    async def process(self, features: List[float]) -> float:
        return self.model(features)


# Usage
async def main():
    # Create pipeline with monitoring
    pipeline = AsyncPipeline([DataPreprocessor(), FeatureExtractor(), ModelPredictor()])
    pipeline.monitor = PipelineMonitor()

    # Enable parallel processing
    pipeline.configure_parallel(ExecutionStrategy.PROCESS_POOL, max_workers=4)

    # Generate test data
    data = [np.random.rand(100, 100) for _ in range(1000)]

    # Process in parallel
    async with pipeline:
        pipeline.monitor.start()
        results = await pipeline.execute_parallel(data)
        print(results)
        pipeline.monitor.stop()

    # Print performance metrics
    metrics = pipeline.monitor.get_metrics()
    print(f"Total time: {metrics['total_time']:.2f}")
```

## Explanation

1. Data preprocessing using `DataPreprocessor`
2. Feature extraction from preprocessed data
3. Model prediction using a simple average function
4. Parallel processing using PROCESS_POOL strategy
5. Monitoring pipeline performance
6. Resource management with async context managers
