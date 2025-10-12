---
title: How to Release
description: Explains how to release pydantic-settings-manager to PyPI.
---

This guide explains the release procedure using version 1.0.0 as an example.

## Release Procedure

### 1. Update CHANGELOG
First, add your changes to the `[Unreleased]` section in `CHANGELOG.md`:

```markdown
## [Unreleased]

### Added
- New feature description

### Fixed
- Bug fix description

### Changed
- Breaking change description
```

### 2. Update Version and CHANGELOG
Run the following commands to update version and finalize CHANGELOG:

```sh
# Update version in pyproject.toml
mise run version 1.0.0

# Convert [Unreleased] section to [1.0.0] with current date
mise run update-changelog 1.0.0
```

### 3. Review Changes
```sh
# Review changed files
git diff pyproject.toml CHANGELOG.md
```

### 4. Run CI Checks
```sh
# Ensure all CI checks pass
mise run ci
```

### 5. Commit, Tag, and Push
```sh
# Commit changes
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v1.0.0"

# Create annotated tag
git tag -a v1.0.0 -m "Release v1.0.0"

# Push with tags
git push origin main --tags
```

## Automated Processes

When you push a tag (e.g., `v1.0.0`), the `.github/workflows/release.yml` workflow in GitHub Actions automatically executes the following:

1. **CI Checks**: Runs format, lint, typecheck, test, and build
2. **Extract Release Notes**: Extracts the changelog section for the version
3. **GitHub Release**: Creates a GitHub Release with the extracted release notes
4. **PyPI Publication**: Publishes the package to PyPI (requires `PYPI_API_TOKEN` secret)

## Manual Publication (if needed)

If you need to publish manually:

```sh
# Build the package
mise run build

# Publish to PyPI
mise run publish

# Or publish to Test PyPI first
mise run publish --test
```

## Pre-release Versions

For alpha, beta, or release candidate versions:

```sh
# Update version with pre-release suffix
mise run version 1.0.0-alpha.1

# Update CHANGELOG
mise run update-changelog 1.0.0-alpha.1

# Commit and tag
git add pyproject.toml CHANGELOG.md
git commit -m "chore: release v1.0.0-alpha.1"
git tag -a v1.0.0-alpha.1 -m "Release v1.0.0-alpha.1"
git push origin main --tags
```

The GitHub Release will be automatically marked as a pre-release.
