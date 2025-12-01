# CI/CD Setup Guide

This document describes the GitHub Actions workflows that ensure code quality and test coverage for the NordInvest project.

## Overview

The CI/CD pipeline automatically validates all pull requests to the `main` branch by:

1. **Running pre-commit checks** - Code formatting, linting, and conventional commit validation
2. **Executing the full test suite** - Unit and integration tests with detailed reporting
3. **Measuring code coverage** - Tracking test coverage trends over time

## Workflows

### 1. PR Tests (`pr-tests.yml`)

**Triggers:** Pull requests to `main` branch

**Steps:**

1. **Checkout Code** - Clone the repository
2. **Setup Python** - Configure Python 3.12 environment
3. **Install uv** - Set up the UV package manager
4. **Cache Dependencies** - Cache `~/.cache/uv` for faster runs
5. **Sync Dependencies** - Install dependencies from `uv.lock`
6. **Run Pre-commit Checks** - Execute linting and formatting:
   - Trailing whitespace removal
   - EOF newline fixing
   - YAML/TOML validation
   - Debug statement detection
   - Ruff linting (import sorting, unused imports, formatting)
   - Black code formatting
   - Conventional commit validation
7. **Run Tests** - Execute pytest with verbose output and short tracebacks
8. **Publish Results** - Annotate PR with detailed test results

**Expected Output:**

- ✅ All pre-commit checks pass
- ✅ All tests pass (219 tests)
- Test results comment on PR showing:
  - Number of passed/failed/skipped tests
  - Duration of test run
  - Detailed failure information (if any)

### 2. Code Coverage (`coverage.yml`)

**Triggers:** Pull requests to `main` branch

**Steps:**

1. Setup Python 3.12 environment
2. Install uv and sync dependencies
3. Run pytest with coverage reporting:
   - Generates XML coverage report
   - Displays terminal output with missing coverage
   - Tracks coverage statistics
4. Upload to Codecov for historical tracking

**Output:**

- Coverage percentage per module
- Missing line coverage details
- Historical trend visualization (on Codecov)

## Branch Protection Rules

To enforce the CI/CD pipeline, configure branch protection rules on `main`:

1. Go to **Settings** → **Branches** → **Branch protection rules**
2. Create rule for `main` branch:
   - ✅ Require status checks to pass before merging
     - Select "PR Tests / test" workflow
     - Select "Code Coverage / coverage" workflow
   - ✅ Require code reviews before merging (recommended: 1 reviewer)
   - ✅ Require status checks to pass before merging
   - ✅ Include administrators in restrictions (optional)
   - ✅ Restrict who can push to matching branches (optional)

## Metrics & Thresholds

Current baseline metrics (as of Phase 7):

- **Test Count:** 219 tests
- **Skipped Tests:** 14 (expected - skipped for integration tests)
- **Pass Rate:** 100% (219/219)
- **Execution Time:** ~4-5 seconds
- **Coverage:** Currently not enforced (can add threshold)

### Recommended Coverage Thresholds

Consider adding coverage requirements:

```yaml
# In coverage.yml, after upload step:
- name: Check coverage threshold
  run: |
    # Fail if coverage drops below 70%
    coverage report --fail-under=70
```

## Local Development

To run the same checks locally before pushing:

```bash
# Run pre-commit checks
uv run poe pre-commit

# Run all tests
uv run pytest tests/ -q

# Run tests with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

## Troubleshooting

### Workflow Fails with "Module not found"

**Cause:** Dependencies not synced correctly
**Fix:** Ensure `uv.lock` is committed and up-to-date

```bash
uv sync
git add uv.lock
git commit -m "chore: update dependencies"
```

### Pre-commit Checks Fail (Formatting/Linting)

**Cause:** Code doesn't match black/ruff formatting
**Fix:** Run linting locally and commit the fixes

```bash
uv run poe lint
git add .
git commit -m "style: apply formatting rules"
```

### Tests Fail in CI but Pass Locally

**Cause:** Different Python versions or environment differences
**Fix:**

1. Verify you're using Python 3.12:
   ```bash
   python --version
   ```
2. Ensure `uv.lock` matches CI environment:
   ```bash
   uv sync
   uv run pytest tests/
   ```

### Coverage Upload Fails

**Cause:** Codecov token not configured
**Fix:** Add Codecov token to GitHub repository secrets:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Create secret `CODECOV_TOKEN` (get from codecov.io)
3. Workflow will automatically use the token

## Performance Optimization

The workflow uses several optimizations to keep execution time under 1 minute:

1. **Dependency Caching** - Reuses cached dependencies across runs
2. **Parallel Testing** - pytest runs all tests in parallel by default
3. **Fast Linting** - Ruff is extremely fast (< 1 second for this project)
4. **JIT Compilation** - Python 3.12 with optimizations

Current benchmark (Ubuntu runner):
- Checkout: ~2s
- Setup Python: ~5s
- Install uv: ~3s
- Sync dependencies: ~8s
- Pre-commit checks: ~3s
- Tests: ~4s
- Coverage: ~5s

**Total:** ~30 seconds per workflow

## Future Enhancements

Potential improvements:

1. **Coverage Threshold** - Fail if coverage drops below 70%
2. **Performance Benchmarks** - Track test execution time trends
3. **Dependency Security Checks** - Run `safety` or `pip-audit`
4. **LLM API Key Validation** - Ensure secrets are not leaked
5. **Docker Build** - Build and test Docker image in CI
6. **Scheduled Runs** - Daily tests against main branch
7. **PR Size Checks** - Warn on large PRs (help enforce small commits)
8. **Auto-merge** - Auto-merge PRs from dependabot if all checks pass

## Maintenance

### Updating Workflows

When updating dependencies or Python version:

1. Update `pyproject.toml` (requires-python)
2. Update `.github/workflows/pr-tests.yml` (python-version)
3. Update `.github/workflows/coverage.yml` (python-version)
4. Test locally with new Python version
5. Commit and push to create PR
6. Verify workflows pass with new configuration

### Archiving Old Results

GitHub keeps workflow runs for 90 days by default. To reduce storage:

1. Go to **Actions**
2. Select workflow
3. Click "Delete workflow runs" for old runs

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Pre-commit Framework](https://pre-commit.com/)
- [pytest Documentation](https://docs.pytest.org/)
- [Codecov Documentation](https://docs.codecov.io/)
- [UV Package Manager](https://github.com/astral-sh/uv)
