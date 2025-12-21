# Installation Guide

## System Requirements

- **Python 3.9+**
- For better performance: Linux or macOS (uvloop support)

## Installation Methods

### Using pip

```bash
pip install zeroapi
```

### From Source

```bash
git clone https://github.com/Ananto30/zero.git
cd zero
pip install -e .
```

## Optional Dependencies

Zero includes several optional dependencies for specific use cases:

### uvloop - Better Async Performance

Improves async performance on Linux and macOS (no effect on Windows):

```bash
pip install "zeroapi[uvloop]"
```

**When to use:** If you're building async-heavy services on Unix systems.

### Pydantic Support

Enable full Pydantic model support for complex data validation:

```bash
pip install "zeroapi[pydantic]"
```

**When to use:** When you need data validation and schema generation.

### Tornado - Windows Async Support

Windows-specific async runtime support:

```bash
pip install "zeroapi[tornado]"
```

**When to use:** If you're running async services on Windows.

### Everything

Install all optional dependencies at once:

```bash
pip install "zeroapi[all]"
```

## Verify Installation

```bash
python -c "from zero import ZeroServer, ZeroClient; print('✓ Zero is installed!')"
```

## Virtual Environment Setup

**Recommended**: Always use a virtual environment:

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install zero
pip install zeroapi
```

## Next Steps

- [Basic Usage](basic-usage.md) - Create your first server
- [Serialization](serialization.md) - Handle complex data types
- [Code Generation](code-generation.md) - Auto-generate client code
