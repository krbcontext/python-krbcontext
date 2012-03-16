# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

def get_long_description():
    return open('README', 'r').read()

setup(
    name = 'krbcontext',
    version = '0.1',
    long_description = get_long_description(),
    keywords = 'kerberos context principal credential',
    license = 'BSD',
    author = 'Chenxiong Qi',
    author_email = 'qcxhome@gmail.com',

    packages = find_packages('src'),
    package_dir = { '': 'src', },
)
