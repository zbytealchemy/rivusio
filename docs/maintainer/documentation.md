# Documentation Guidelines

## Overview

This guide covers the documentation structure and maintenance procedures for Rivusio.

## Documentation Structure

```
docs/
├── index.md                 # Main landing page
├── getting-started/         # Getting started guides
├── user-guide/             # User documentation
├── maintainer/             # Maintainer documentation
├── api/                    # API documentation
└── examples/               # Code examples
```

## Writing Documentation

### Style Guidelines

1. **Clear and Concise**
   - Use active voice
   - Keep sentences short
   - Avoid jargon

2. **Code Examples**
   - Include type hints
   - Add comments for complex logic
   - Use realistic examples

3. **Formatting**
   - Use proper Markdown syntax
   - Include section headers
   - Add internal links

### API Documentation

- Document all public APIs
- Include type information
- Provide usage examples
- Note deprecations

## Building Documentation

```bash
# Install documentation dependencies
poetry install --with docs

# Build documentation
make docs

# Serve locally
make docs-serve
```

## Updating Documentation

1. **For New Features**
   - Add API documentation
   - Update relevant guides
   - Include examples

2. **For Changes**
   - Update affected docs
   - Review related sections
   - Update version notes

3. **For Deprecations**
   - Mark as deprecated
   - Add migration guides
   - Update examples