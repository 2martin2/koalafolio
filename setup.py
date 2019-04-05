import setuptools

with open('README.rst', encoding="utf-8") as f:
    readme = f.read()

setuptools.setup(
    name='koalafolio',
    version='0.6.0',
    description='portfolio app for crypto trading and tax reporting',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/2martin2/pycryptoportfolio',
    author='2martin2',
    author_email='2martin2@protonmail.com',
    keywords='crypto cryptocoins tax portfolio tracking',
    license='GPL-3.0',
    python_requires='>=3',
    packages=setuptools.find_packages(),
    classifiers=['Programming Language :: Python :: 3'],
    install_requires=['pandas', 'pyqt5', 'pyqtchart', 'tzlocal', 'pyinstaller', 'xlrd', 'requests', 'openpyxl'],
    include_package_data=True,
    entry_points={
            'console_scripts': [
                'koalafolio = koalafolio.gui_root:main',
            ],
            'gui_scripts': [
                'koalafolio = koalafolio.gui_root:main',
            ],
        }
    )
