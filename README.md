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

Here is a **clean, developer-friendly section** you can add after the install instructions. It keeps things **simple**, assumes **Nix as the main development environment**, and explains the workflow clearly.
