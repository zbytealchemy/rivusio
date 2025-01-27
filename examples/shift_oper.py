"""Example of using the shift operator to compose pipelines."""

from rivusio import AsyncBasePipe


class FilterPipe(AsyncBasePipe[dict, dict]):
	"""Filter dictionary values."""

	async def process(self, data: dict) -> dict:
		"""Filter dictionary items where value is below 100."""
		min_value: int = 100
		return {k: v for k, v in data.items() if v > min_value}


class TransformPipe(AsyncBasePipe[dict, list]):
	"""Transform dictionary to list."""

	async def process(self, data: dict) -> list:
		"""Transform dictionary to list of values."""
		return list(data.values())


class OperatorPipe(AsyncBasePipe[list, tuple]):
	"""Multiply list items by 5."""

	async def process(self, data: list) -> tuple:
		"""Multiply list items by 5."""
		result = [5 * item for item in data]
		return tuple(result)


async def main() -> None:
	"""Run the example."""
	pipeline = FilterPipe() >> TransformPipe() >> OperatorPipe()  # type: ignore

	data = {"a": 150, "b": 50, "c": 200}
	result = await pipeline(data)  # [750, 1000]
	print(result)

if __name__ == "__main__":
	import asyncio
	asyncio.run(main())
