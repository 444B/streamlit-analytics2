# Contributing to Streamlit-Analytics2

## Getting Started
1. Fork and clone:
```sh
git clone https://github.com/444B/streamlit-analytics2.git
cd streamlit-analytics2
```
2. Create branch:
```sh
git checkout -b test/your-feature-name
```

## Development Environment Setup
1. Install Python 3.11 or newer
2. Install and setup uv:
```sh
pip install uv
uv venv .venv --python 3.11
source .venv/bin/activate
```
3. Install dependencies:
```sh
uv pip install -e ".[dev]"
```
4. Verify setup:
```sh
streamlit run examples/minimal.py
```

## Quality Checks
```sh
cd tests/
chmod +x run_checks.sh
./run_checks.sh
./run_checks.sh --fix # this will implement the fixes
```

## Pull Request Process
1. Push changes:
```sh
git add .
git commit -m "Your commit message"
git push origin test/your-feature-name
```
2. Open PR on GitHub

For issues: [GitHub issue tracker](https://github.com/444B/streamlit-analytics2/issues/new/choose)

By contributing, you agree to the project's [license](https://github.com/444B/streamlit-analytics2/blob/main/LICENSE).
