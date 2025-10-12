# GitHub Configuration

This directory contains GitHub-specific configuration files for the pydantic-settings-manager project.

## Structure

```
.github/
├── ISSUE_TEMPLATE/
│   ├── bug_report.md          # Bug report template
│   └── feature_request.md     # Feature request template
├── workflows/
│   ├── ci.yml                 # Continuous Integration workflow
│   └── release.yml            # Release automation workflow
├── dependabot.yml             # Dependabot configuration
├── pull_request_template.md  # Pull request template
└── README.md                  # This file
```

## Issue Templates

### Bug Report
- **File**: `ISSUE_TEMPLATE/bug_report.md`
- **Purpose**: Standardized format for reporting bugs
- **Includes**: Reproduction steps, environment details, expected vs actual behavior

### Feature Request
- **File**: `ISSUE_TEMPLATE/feature_request.md`
- **Purpose**: Standardized format for suggesting new features
- **Includes**: Problem description, proposed solution, use cases

## Pull Request Template

- **File**: `pull_request_template.md`
- **Purpose**: Ensures PRs include all necessary information
- **Checklist includes**:
  - Type of change
  - Testing verification
  - Code quality checks
  - Documentation updates
  - CHANGELOG updates

## Workflows

### CI Workflow (`ci.yml`)

**Triggers**:
- Push to `main` branch
- Pull requests to `main` branch

**Jobs**:
1. **Test** - Runs on Python 3.9-3.13
   - Format check (`mise run format`)
   - Lint check (`mise run lint`)
   - Type check (`mise run typecheck`)
   - Tests with coverage (`mise run test --coverage`)
   - Upload coverage to Codecov (Python 3.13 only)

2. **Build** - Builds package and uploads artifacts
   - Runs after tests pass
   - Uploads `dist/` as artifact

**Features**:
- Uses `mise` for consistent development environment
- Matrix testing across multiple Python versions
- Codecov integration for coverage tracking
- Build artifact preservation

### Release Workflow (`release.yml`)

**Triggers**:
- Push of version tags (e.g., `v2.2.0`)

**Jobs**:
1. **Build and Publish**
   - Runs full CI checks
   - Builds package
   - Extracts release notes from CHANGELOG.md
   - Creates GitHub Release with artifacts
   - Publishes to PyPI

**Features**:
- Automatic CHANGELOG extraction using `mise run extract-changelog`
- Fallback to auto-generated release notes if CHANGELOG entry not found
- Prerelease detection (alpha, beta, rc)
- PyPI publishing with trusted publishing support

**Required Secrets**:
- `CODECOV_TOKEN` - For coverage uploads (optional)
- `PYPI_API_TOKEN` - For PyPI publishing

## Dependabot Configuration

- **File**: `dependabot.yml`
- **Purpose**: Automated dependency updates

**Update Schedule**:
- **Python dependencies**: Weekly (Monday)
  - Groups: dev-dependencies, test-dependencies, pydantic-dependencies
  - Max 5 PRs at once
- **GitHub Actions**: Weekly (Monday)
  - Max 3 PRs at once

**Labels**: Automatically adds `dependencies` and ecosystem-specific labels

## Setup Instructions

### For Contributors

1. **Create Issues**: Use the issue templates when reporting bugs or requesting features
2. **Create PRs**: Follow the PR template checklist
3. **Local Development**: Use `mise run ci` to verify changes before pushing

### For Maintainers

1. **Codecov Setup** (Optional):
   ```bash
   # Add CODECOV_TOKEN to repository secrets
   # Get token from https://codecov.io/
   ```

2. **PyPI Publishing Setup**:
   ```bash
   # Add PYPI_API_TOKEN to repository secrets
   # Get token from https://pypi.org/manage/account/token/
   ```

3. **Release Process**:
   ```bash
   # 1. Update version
   mise run version 2.3.0
   
   # 2. Update CHANGELOG
   mise run update-changelog 2.3.0
   
   # 3. Commit and tag
   git add .
   git commit -m "chore: bump version to 2.3.0"
   git tag v2.3.0
   
   # 4. Push with tags
   git push origin main --tags
   
   # 5. Release workflow will automatically:
   #    - Run CI checks
   #    - Build package
   #    - Create GitHub Release
   #    - Publish to PyPI
   ```

## Best Practices

### For Issues
- Use appropriate templates
- Provide minimal reproducible examples
- Include environment details
- Search for existing issues first

### For Pull Requests
- Fill out all sections of the PR template
- Link related issues
- Update CHANGELOG.md under `[Unreleased]`
- Ensure all CI checks pass
- Keep PRs focused and atomic

### For Releases
- Follow semantic versioning (MAJOR.MINOR.PATCH)
- Update CHANGELOG.md before tagging
- Use descriptive commit messages
- Test locally with `mise run ci` before releasing

## Troubleshooting

### CI Failures

**Format/Lint Issues**:
```bash
mise run format  # Auto-fix formatting
mise run lint    # Check for issues
```

**Test Failures**:
```bash
mise run test --verbose  # Run with verbose output
```

**Type Check Issues**:
```bash
mise run typecheck  # Run mypy
```

### Release Issues

**CHANGELOG Not Found**:
- Ensure version entry exists in CHANGELOG.md
- Use `mise run update-changelog <version>` to add entry

**PyPI Publishing Fails**:
- Check PYPI_API_TOKEN is valid
- Verify version doesn't already exist on PyPI
- Check package builds successfully locally

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Dependabot Documentation](https://docs.github.com/en/code-security/dependabot)
- [mise Documentation](https://mise.jdx.dev/)
- [Codecov Documentation](https://docs.codecov.com/)
