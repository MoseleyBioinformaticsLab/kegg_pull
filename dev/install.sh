echo "Removing previous .env/ directory if it exists..."
rm -rf .env/
echo "Creating new .env/ directory..."
python3 -m venv .env/
source .env/bin/activate
python3 -m pip install --upgrade pip
python3 -m pip install pytest pytest-mock pytest-cov sphinx sphinx-rtd-theme notebook
python3 -m pip install -e .
