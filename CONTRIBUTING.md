# Contributing to glinet

Thanks for your interest in contributing! This document explains how the
project is organised, how to set up a development environment, and the
process for opening pull requests.

> **New here?** Skim [Local Development](#local-development) first, then
> open your PR.

---

## Code of Conduct

This project follows the [Contributor Covenant](https://www.contributor-covenant.org/).
By participating, you agree to abide by its terms. Be respectful, assume
good intent, and focus on what is best for the community.

---

## Local Development

### 1. Fork and clone

```bash
git clone https://github.com/<your-username>/python-glinet-router.git
cd python-glinet-router
git remote add upstream https://github.com/vithurshanselvarajah/python-glinet-router.git
```

### 2. Set up a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / macOS
# .venv\Scripts\activate    # Windows PowerShell
python -m pip install --upgrade pip
python -m pip install -e ".[test]" ruff
```

### 3. Create a feature branch

```bash
git fetch upstream
git checkout -b feature/your-change upstream/main
```

### 4. Make your changes

See [Architecture](docs/architecture.md) for the internal module map,
and [Extending the library](docs/architecture.md#extending-the-library)
for the recommended way to add a new endpoint or module.

### 5. Run the checks

```bash
# Tests
pytest -q

# Lint (with auto-fix where safe)
ruff check src tests --fix

# Format
ruff format src tests

# Sanity-check that everything compiles
python -m compileall -q src tests
```

CI runs the same checks on every PR.

---

## Testing & Linting

The test suite uses `pytest` with `pytest-asyncio` in auto mode. The
shared test doubles (`FakeSession`, `FakeResponse`, `FakePostContext`)
live in [`tests/_fakes.py`](tests/_fakes.py).

Test guidelines:

- One test file per module (e.g. `tests/test_modem.py` for
  `src/glinet/modules/modem.py`).
- Use the shared fakes — do not introduce new mocks without a reason.
- Cover the happy path, the failure modes (non-zero error codes, token
  expiry, unsupported firmware algorithms), and any new behaviour you
  introduce.

---

## Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) style:

```text
feat(wg_client): add get_wireguard_state for firmware 4.8

The 4.8 endpoint shape differs from 4.9; pick based on the cached
firmware version.
```

Common prefixes: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`,
`chore:`.

---

## Release Process

Releases are managed by the maintainer(s) only and use
[PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) —
there is no PyPI API token stored in GitHub.

The full flow is documented in
[`docs/ci-release.md`](docs/ci-release.md). The short version:

1. Bump the `version` in `pyproject.toml`.
2. Add a new dated entry under `CHANGELOG.md`.
3. Open a PR titled e.g. `Release 0.0.2`, merge after CI passes.
4. Land the merge on `main` with a commit message that starts with
   `release:` (the literal prefix is the trigger). The version is
   read from `pyproject.toml`; you do not tag by hand.
5. The `Release` workflow tests the build, publishes to TestPyPI,
   then publishes to PyPI via OIDC, and creates the `vX.Y.Z` tag and
   GitHub Release.

Use the `Publish` workflow (`workflow_dispatch`) to re-cut a failed
release or publish a backport branch.

---

## Adding a New Module or Endpoint

The recommended workflow for any API change is:

1. **API surface:** add the new method to the appropriate module under
   `src/glinet/modules/`. Attach new modules to
   `GLinetApiClient.__init__` in `src/glinet/client.py` and re-export the
   class from `src/glinet/modules/__init__.py`.
2. **Tests:** mirror the change in `tests/test_<module>.py`.
3. **Docs:** add or update the relevant page under `docs/`. The
   integration's [developer reference](https://github.com/vithurshanselvarajah/ha-glinet-router/blob/development/docs/developer-reference.md)
   does not need to change unless the public surface shifts.
4. **CHANGELOG:** add a one-line entry under "Unreleased".

---

## Documentation

The `docs/` folder mirrors to a wiki via the same `wiki-sync.yml`
workflow used by the integration. Keep page names in kebab-case
(`lowercase-with-dashes.md`) so the wiki auto-generates correct titles.

---

## Security

If you find a security issue, please do not open a public issue. Email
the maintainer instead (see `pyproject.toml` `[project.urls]` for
contact links).
