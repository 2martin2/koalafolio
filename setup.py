import setuptools

with open('README.rst', encoding="utf-8") as f:
    readme = f.read()

setuptools.setup(
    name='koalafolio',
    version='0.12.4',
    description='portfolio app for crypto trading and tax reporting',
    long_description=readme,
    long_description_content_type='text/x-rst',
    url='https://github.com/2martin2/koalafolio',
    author='2martin2',
    author_email='2martin2@proton.me',
    keywords='crypto cryptocoins tax portfolio tracking',
    license='GPL-3.0',
    python_requires='>=3.7',
    packages=setuptools.find_packages(),
    classifiers=['Programming Language :: Python :: 3'],
    install_requires=['aiohttp>=3.9.0',
                      'base58check',
                      'bech32',
                      'certifi>=2023.7.22',
                      'coincurve',
                      'gevent>=23.9.0',
                      'gql',
                      'krakenex',
                      'openpyxl',
                      'pandas>=1.5.3',
                      'pillow>=6.2.0,<10.0.0',
                      'pycoingecko<=2.3.0',
                      'pycryptodomex',
                      'pygments>=2.15.0',
                      'pykrakenapi',
                      'pyqt5',
                      'pyqtchart',
                      'requests',
                      'typing-extensions',
                      'tzlocal>=5.0.1',
                      'urllib3>=1.24.2',
                      'web3',
                      'xlrd'],
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
