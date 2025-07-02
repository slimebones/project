run *args:
    @ python -m src {{args}}

install:
    @ rm -rf ~/dist/project
    @ cp -r ../project ~/dist/project
    @ echo "Installed."
