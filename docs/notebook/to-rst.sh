# Note this will only work if pandoc is installed separately via "sudo dnf install pandoc"
jupyter nbconvert --to rst tutorial.ipynb
python3 correct_nbconvert.py
mv tutorial.rst ../tutorial.rst
