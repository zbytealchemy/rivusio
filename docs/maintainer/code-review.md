# Code Review Guidelines

## Overview

This document outlines the code review process and standards for Rivusio maintainers.

## Review Process

### 1. Initial Assessment

- Check if PR is linked to an issue
- Verify branch naming convention
- Confirm PR template is complete
- Check commit message format

### 2. Technical Review

#### Code Quality
- Type hints used correctly
- Documentation updated
- Tests included
- Performance considerations
- Error handling
- Code style compliance

#### Testing
- Unit tests added/updated
- Integration tests if needed
- Test coverage adequate
- Edge cases covered

### 3. Documentation Review

- API documentation complete
- Examples updated
- Changelog updated
- Docstrings present

## Review Checklist

- [ ] Follows [Contributing Guidelines](../contributing.md)
- [ ] Maximum 2 commits per PR
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Type checking passes
- [ ] Linting passes
- [ ] No security issues
- [ ] Performance impact considered

## Response Guidelines

### Providing Feedback

- Be constructive and specific
- Link to relevant documentation
- Explain the "why" behind suggestions
- Mark comments as resolved when fixed

### Common Responses

```markdown
# Request Changes
Could you please:
- Add type hints to function parameters
- Include unit tests for edge cases
- Update the changelog
```

## Final Approval

Before merging, ensure:
1. All discussions resolved
2. CI checks passing
3. Required approvals received
4. Documentation updated
5. Tests added and passing