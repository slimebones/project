set shell := ["nu", "-c"]

run *args:
    @ python main.py {{args}}

test:
    @ pytest