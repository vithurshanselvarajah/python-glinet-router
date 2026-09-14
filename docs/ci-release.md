# CI & Releases

This project uses [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/)
and GitHub Actions to publish `glinet` to PyPI automatically. There is
no manually-managed API token.

## How a release happens

1. Maintainer creates a feature branch (or works on `main`).
2. Bump the `version` in `pyproject.toml` to the next PEP 440 value,
   e.g. `0.0.2` or `1.0.0`.
3. Add a dated `## [X.Y.Z] - YYYY-MM-DD` entry to `CHANGELOG.md`
   describing the changes since the last release.
4. Open a PR titled conventionally (e.g. `Release 0.0.2`) and merge
   when CI passes.
5. Land the merge commit on `main` with a commit message starting with
   `release:` — for example:

   ```text
   release: 0.0.2
   ```

   The literal prefix **`release:`** (case-insensitive) is the trigger
   the workflow looks for on `main` pushes. The colon and version are
   optional; only the prefix matters. The actual version is read from
   `pyproject.toml`.

6. The `Release` workflow:
   - Tests on Python 3.12 and 3.13.
   - Builds sdist and wheel.
   - Publishes to **TestPyPI** (so you can sanity-check the install).
   - Then publishes to **PyPI** via OIDC, with no stored secrets.
   - Creates the `vX.Y.Z` git tag and the GitHub Release, attaching
     the built `*.whl` and `*.tar.gz`.

## Manual trigger

The release workflow also runs on `workflow_dispatch`. Use it to
re-cut a failed release, or to publish a hot-fix branch after a
backport.

## First-time setup on PyPI

The first time the project is uploaded, PyPI needs to know which
GitHub repo is allowed to publish under the `glinet` name. As the
project owner:

1. Go to <https://pypi.org/manage/account/publishing/>.
2. Click **Add a new pending publisher**.
3. Fill in:

   | Field                      | Value                                |
   | -------------------------- | ------------------------------------ |
   | PyPI Project Name          | `glinet`                             |
   | Owner                      | `vithurshanselvarajah`               |
   | Repository name            | `python-glinet-router`               |
   | Workflow filename          | `release.yml`                        |
   | Workflow filename (alt)    | `publish.yml`                        |

4. Repeat on <https://test.pypi.org/manage/account/publishing/> for
   the `testpypi` environment if you want pre-release smoke tests.

The pending publisher is **not** verified until the first successful
publish, but that's fine — once it succeeds, the project on PyPI is
permanently linked to this GitHub repository and you never have to
rotate a token again.

## Environment rules (recommended)

On the GitHub repo, define two **deployment environments**:

- **`pypi`** — required reviewers set to the maintainers' team, and
  any branch protection rules you like. The OIDC token is scoped to
  this environment.
- **`testpypi`** — typically unrestricted; it's a sandbox.

With those in place, a malicious commit can't silently publish a new
release because the `environment:` block in
`.github/workflows/release.yml` requires environment approval.

## Reversing a bad release

PyPI releases are append-only — you cannot overwrite a version. To
"un-release" a bad tag:

1. Delete the GitHub Release and tag on GitHub.
2. Yank the version on PyPI (Settings → Project → release history →
   yank). It remains installable as `glinet==0.0.2` but new installs
   fail by default.
3. Bump to `0.0.3`, add a fix entry to `CHANGELOG.md`, and ship a
   follow-up release.

## Versioning

This project follows [Semantic Versioning](https://semver.org/):

- **Bug fixes and internal refactors** → bump PATCH (`0.0.1` → `0.0.2`).
- **New, backwards-compatible modules or methods** → bump MINOR
  (`0.0.1` → `0.1.0`).
- **Any backwards-incompatible change** → bump MAJOR (`0.x.y` → `1.0.0`).

Until `1.0.0`, MINOR may be used for anything that adds public surface
and PATCH for anything that doesn't.
