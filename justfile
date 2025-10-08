set shell := ["nu", "-c"]

main *args:
    @ python main.py {{args}}

test:
    @ pytest

deploy:
    @ rm -rf ~/.app/project
    @ mkdir ~/.app/project
    @ cp -r * ~/.app/project/