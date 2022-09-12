# Note this will only work if pandoc is installed separately via "sudo dnf install pandoc"
jupyter nbconvert --to rst tutorial.ipynb
mv tutorial.rst ../tutorial.rst

