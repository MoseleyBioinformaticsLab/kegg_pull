source .env/bin/activate

python -m pytest tests --cov --cov-branch --cov-report=term-missing
