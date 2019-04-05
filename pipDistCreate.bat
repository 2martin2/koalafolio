rmdir /s /q dist
pipenv run setup.py sdist bdist_wheel
python -m twine check dist/*