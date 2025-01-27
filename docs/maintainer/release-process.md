# Release Process

## Overview

This document outlines the step-by-step process for releasing new versions of Rivusio.

## Prerequisites

- Write access to the main repository
- PyPI publishing rights
- Access to repository settings

## Release Steps

1. **Version Update**
   - Update version in `pyproject.toml`
   - Update `__version__` in `src/rivusio/__init__.py`
   - Update `CHANGELOG.md`

2. **Pre-release Checks**
   ```bash
   # Run all tests
   make test
   
   # Run type checking
   make type-check
   
   # Run linting
   make lint
   
   # Build documentation
   make docs
   ```

3. **Create Release PR**
   - Branch name: `release/v{version}`
   - Include all version updates
   - Update documentation if needed
   - Maximum 2 commits

4. **After PR Approval**
   - Merge to main
   - Contact @zmastylo to enable `RELEASE_FLAG`
   - Verify CI/CD pipeline completion

5. **Manual Release Steps**
   - Trigger publish workflow
   - Verify PyPI package
   - Check documentation updates

## Versioning Guidelines

We follow [Semantic Versioning](https://semver.org/):

- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible features
- PATCH version for backwards-compatible fixes

## Troubleshooting

### Common Issues

1. **Failed PyPI Upload**
   - Check PyPI token validity
   - Verify version number uniqueness
   - Review package structure

2. **CI/CD Pipeline Failures**
   - Check test failures
   - Verify environment variables
   - Review workflow logs