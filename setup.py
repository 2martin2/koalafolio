from setuptools import setup

with open('README.rst', encoding="utf-8") as f:
    readme = f.read()

setup(
        name='koalafolio',
        version='0.5.8',
        description='portfolio app for crypto trading and tax reporting',
        long_description=readme,
        url='https://github.com/2martin2/pycryptoportfolio',
        author='2martin2',
        author_email='2martin2@protonmail.com',
        keywords='crypto cryptocurrency wrapper cryptocompare',
        license='MIT',
        python_requires='>=3',
        packages=['cryptocompare'],
        classifiers=['Programming Language :: Python :: 3'],
        install_requires=['pandas', 'pyqt5', 'pyqtchart', 'tzlocal', 'pyinstaller', 'xlrd', 'requests', 'openpyxl']
        )
