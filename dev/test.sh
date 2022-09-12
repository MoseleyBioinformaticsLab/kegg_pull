source .env/bin/activate

python -m pytest dev --cov --cov-branch --cov-report=term-missing
