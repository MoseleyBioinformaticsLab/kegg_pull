# Local Development
## Installing testing dependencies and kegg_pull as a package
With the root of the repository as the working directory, run the following:
```
bash tests/dev-install.sh # Installs testing dependencies and the kegg_pull package
bash tests/test.sh # Runs tests on the kegg_pull package
```
## Preventing the "module not found" error in PyCharm
* After installing `kegg_pull`, a file at `src/kegg_pull.egg-info/PKG-INFO` is generated.
* Go into that file and change `kegg-pull` (with a dash) to `kegg_pull` (with an underscore).
* Restart PyCharm
