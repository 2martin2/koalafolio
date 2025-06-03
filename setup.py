import setuptools

with open('README.rst', encoding="utf-8") as f:
    readme = f.read()

setuptools.setup(
    name='koalafolio',
    version='0.12.7',
    description='portfolio app for crypto trading and tax reporting',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://gitea.com/2martin2/koalafolio',
    author='2martin2',
    author_email='koala+pypi@slmail.me',
    keywords='crypto cryptocoins tax portfolio tracking',
    license='GPL-3.0',
    python_requires='>=3.7',
    packages=setuptools.find_packages(),
    classifiers=['Programming Language :: Python :: 3'],
    install_requires=['ccxt',
                      'openpyxl',
                      'pandas>=1.5.3',
                      'pycoingecko<=2.3.0',
                      'pycryptodomex',
                      'pyqt5',
                      'pyqtchart',
                      'requests',
                      'tzlocal>=5.0.1',
                      'xlrd'
                      ],
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
