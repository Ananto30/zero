# Contributing to Zero

Thank you for considering contributing to Zero! We welcome contributions of all kinds.

## Ways to Contribute

### 🐛 Report Bugs

Found a bug? Please [open an issue](https://github.com/Ananto30/zero/issues) with:

- Clear title describing the bug
- Python version and OS
- Steps to reproduce
- Expected vs actual behavior
- Full error traceback if applicable

### ✨ Suggest Improvements

Have an idea? We'd love to hear it! [Create an issue](https://github.com/Ananto30/zero/issues) with:

- Clear description of the enhancement
- Why you think it would be useful
- Examples of how it would be used
- Alternative approaches you've considered

### 📚 Improve Documentation

Help make Zero docs better:

- Fix typos or unclear explanations
- Add new examples or guides
- Improve API documentation
- Translate documentation

### 🔧 Contribute Code

Help implement features and fixes!

## Getting Started

### 1. Fork the Repository

```bash
git clone https://github.com/Ananto30/zero.git
cd zero
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[all]"

# Install dev dependencies
pip install -r requirements-lint.txt
```

### 3. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 4. Make Your Changes

Write your code following the style guide below.

### 5. Run Tests

```bash
# Run all tests
make test

# Run specific test file
python -m pytest tests/unit/test_server.py
```

### 6. Lint and Format Code

```bash
make lint
make format
```

### 7. Commit and Push

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature/your-feature-name
```

### 8. Submit Pull Request

[Create a pull request](https://github.com/Ananto30/zero/pull/new) with:

- Clear title and description
- References to related issues
- Description of changes
- How to test the changes

## Code Style Guide

### Python Style

We follow [PEP 8](https://pep8.org/) with these tools:

- **Formatter**: Black
- **Linter**: Flake8
- **Type checking**: Mypy

### Naming Conventions

```python
# Classes: PascalCase
class ZeroServer:
    pass

# Functions/methods: snake_case
def register_rpc():
    pass

# Constants: UPPER_CASE
MAX_MESSAGE_SIZE = 1024

# Private: prefix with underscore
def _internal_method():
    pass
```

### Type Hints

Always include type hints:

```python
# Good
def call(self, method_name: str, data: Any) -> Any:
    pass

# Avoid
def call(self, method_name, data):
    pass
```

### Docstrings

Use docstrings for all public functions:

```python
def register_rpc(self, func: Callable) -> Callable:
    """
    Register an RPC function.

    Parameters
    ----------
    func: Callable
        The function to register as an RPC method.

    Returns
    -------
    Callable
        The registered function

    Raises
    ------
    ValueError
        If function has no type hints
    """
    pass
```

## Documentation Guidelines

### Markdown Format

- Use clear headings (`#`, `##`, `###`)
- Bold for emphasis: **important**
- Code blocks for examples
- Links to related content
