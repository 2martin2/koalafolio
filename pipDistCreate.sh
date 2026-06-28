#!/bin/bash
rm -rf dist
pipenv run python setup.py sdist bdist_wheel
pipenv run python -m twine check dist/*