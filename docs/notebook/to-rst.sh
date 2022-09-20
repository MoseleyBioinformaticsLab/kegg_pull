# Note this will only work if pandoc is installed separately via "sudo dnf install pandoc"
jupyter nbconvert --to rst tutorial.ipynb
sed -i -e 's/! /% /g' tutorial.rst
mv tutorial.rst ../tutorial.rst
