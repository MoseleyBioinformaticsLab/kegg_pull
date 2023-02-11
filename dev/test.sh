source .env/bin/activate || source .env/Scripts/activate # Windows has Scripts instead of bin

python3 -m pytest dev --cov --cov-branch --cov-report=term-missing
