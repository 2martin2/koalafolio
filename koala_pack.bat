pipenv run pyinstaller koalafolio/gui_root.py ^
--windowed ^
--icon=koalafolio/KoalaIcon.ico ^
--name=koalafolio ^
--distpath dist ^
--add-data "koalafolio/Import/defaultApiData.db;Import" ^
--add-data "koalafolio/koalaicon.ico;." ^
--add-data "koalafolio/koalaicon.png;." ^
--add-data "koalafolio/graphics/;graphics"