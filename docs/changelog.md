# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Support for Pydantic v2
- New stream processing capabilities
- Improved error handling and monitoring

### Changed
- Updated configuration classes to use ConfigDict
- Refactored test classes into fixtures
- Simplified Makefile by removing hardcoded paths

### Fixed
- Documentation warnings and missing references
- Pytest collection warnings

## [0.1.0] - 2023-12-01

### Added
- Initial release of Rivusio
- Core pipeline functionality
- Basic pipe types (Filter, Transform, etc.)
- Integration with Kafka and SQS
- Basic documentation and examples

[Unreleased]: https://github.com/zbytealchemy/rivusio/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/zbytealchemy/rivusio/releases/tag/v0.1.0
