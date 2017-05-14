from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='bgapi',
    version='0.1',
    py_modules= ['bgapi'],
    install_requires=[
        'zeep==1.0'
    ]
)

