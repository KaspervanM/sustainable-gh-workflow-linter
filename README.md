# Sustainable GitHub Workflow Linter

A linter that makes GitHub workflows more sustainable.

## How to install

You can install **suslint** in several ways depending on your environment.

### Option 1 — Download a prebuilt binary (recommended)

1. Go to the **Releases** page of this repository.
2. Download the binary for your system:

| System                | File                         |
| --------------------- | ---------------------------- |
| Linux (x86_64)        | `suslint-x86_64-linux`       |
| Linux (ARM)           | `suslint-aarch64-linux`      |
| macOS (Intel)         | `suslint-x86_64-darwin`      |
| macOS (Apple Silicon) | `suslint-aarch64-darwin`     |
| Windows               | `suslint-x86_64-windows.exe` |

3. Make the file executable (Linux/macOS):

```bash
chmod +x suslint-*
```

4. Move it somewhere in your PATH (optional but recommended):

```bash
sudo mv suslint-* /usr/local/bin/suslint
```

You can now run:

```bash
suslint
```

### Option 2 — Install with pip (Python)

If you have **Python 3.11 or newer** installed:

```bash
pip install sustainable-gh-workflow-linter
```

This installs the command:

```bash
suslint
```

### Option 3 — Run with Nix

If you use **Nix**, you can run the tool directly without installing it:

```bash
nix run github:KaspervanM/sustainable-gh-workflow-linter
```

Or install it permanently:

```bash
nix profile install github:KaspervanM/sustainable-gh-workflow-linter
```

### Verify installation

After installing, verify that the tool works:

```bash
suslint --help
```

Or, if using **Nix**:

```bash
nix run github:KaspervanM/sustainable-gh-workflow-linter -- --help
```

You should see the command line help message.


## Development

If you want to contribute to **suslint** or develop new linting rules, follow these steps.

### 1. Clone the repository

```bash
git clone https://github.com/KaspervanM/sustainable-gh-workflow-linter.git
cd sustainable-gh-workflow-linter
```

### 2. Enter the development environment

This project provides a reproducible development environment using **Nix**.

Run:

```bash
nix develop
```

This will open a shell with all required dependencies installed (Python, mypy, etc.).

Alternatively, you can use pip instead of Nix:
```bash
pip install -e .
pip install mypy
```

### 3. Run the linter locally

Inside the development shell you can run the tool directly:

```bash
python3 -m suslint.cli test.yaml
```

Or check the CLI help:

```bash
python3 -m suslint.cli --help
```

The CLI also supports directories, glob patterns, JSON output, and rule filtering:

```bash
python3 -m suslint.cli .github/workflows
python3 -m suslint.cli ".github/workflows/*.yml"
python3 -m suslint.cli --format json test.yaml
python3 -m suslint.cli --select SUS001 test.yaml
python3 -m suslint.cli --ignore SUS002 test.yaml
```

Text output includes a short summary line with the total number of issues and affected files.

### 4. Type checking

The project uses **mypy** for static type checking.

Run:

```bash
mypy suslint
```

### 5. Build the executable

To build the packaged application using Nix:

```bash
nix build
```

The resulting executable will appear in:

```
./result/bin/suslint
```

You can run it with:

```bash
./result/bin/suslint test.yaml
```

### 6. Adding a new lint rule

Rules live in:

```
suslint/rules/
```

To add a new rule:

1. Create a new file in `suslint/rules/`
2. Implement a class that follows the `Rule` protocol
3. The rule will automatically be discovered and executed

Example:

```python
from typing import Iterable

from ruamel.yaml.comments import CommentedMap

from suslint.rule import Issue, RuleMetadata


class ExampleRule:
    id = "SUS999"
    description = "Example rule"
    metadata = RuleMetadata(
        severity="warning",
        category="example-category",
        remediation="Describe how to fix the issue.",
    )

    def check(self, workflow: CommentedMap) -> Iterable[Issue]:
        ...
```

The linter automatically loads rules from the `suslint.rules` package.

<details>
<summary><strong>How parsing and locations work</strong></summary>

Workflow files are loaded using **ruamel.yaml**, which produces a mapping object that behaves like a normal Python dictionary but also stores line and column information for each key. This allows rules to report exactly where a problem occurs in the YAML file.

When writing a rule:

1. **Access the part(s) of the workflow the rule is about** using normal dictionary operations.
2. **Check for conditions** to enforce.
    * E.g. existance of keys/values
3. **Determine the location** in the YAML **(if applicable)**:
    * Use the helper in `suslint/position.py` to get the 1-based line and column of a key.
    * Construct a `Location` object with a descriptive `trail` (like `"on.push"` or `"jobs.build"`) and the line/column.
4. **Yield an `Issue`** with the rule ID, message, and `Location`.

</details>

### 7. Testing your rule

Create or modify a workflow file (for example `test.yaml`) and run:

```bash
python3 -m suslint.cli test.yaml
```

Here’s a revised, concise version that makes that requirement explicit:

## Contributing

GitHub Actions automate versioning, building, and releasing the linter based on [Conventional Commits](https://www.conventionalcommits.org/):

* On pushes to `main`, workflows determine a semantic version for the branch, build platform-specific binaries, and upload them as release artifacts.
* Versions for other branches (e.g., `dev`, `rc`) can also be set to increment automatically. These branches must be added to the triggers in **auto-version.yml**.
* To create a standard (non-prerelease) release, use **make-latest-release.yml** manually.

### Versioning

* `main` is the release branch: `vX.Y.Z`.
* Other branches are labeled (pre-)releases: `vX.Y.Z-branch.N`.
* **Contributors must follow [Conventional Commits](https://www.conventionalcommits.org/) for all commit messages**, as version bumps are automatically determined from them:

  * `BREAKING CHANGE` or `!` --> major
  * `feat` --> minor
  * `fix`/`perf` --> patch
* Pre-release branches increment only the pre-release number if no new changes relative to `main` exist.
