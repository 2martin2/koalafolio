rem todo: exe needs graphics and Import/defaultApiData.db relative to exe path.
rem Include of these files in .spec does not work with single file mode.
rem When they are copied to dist folder manually, it works.
pipenv run pyinstaller koalafolio.spec