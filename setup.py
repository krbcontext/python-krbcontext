# -*- coding: utf-8 -*-

import os
from configparser import ConfigParser
from setuptools import setup, find_packages


def get_long_description():
    return '''%s

%s''' % (open('README.rst', 'r').read(), open('CHANGELOG.rst', 'r').read())

setup_cfg = ConfigParser()
setup_cfg.read(os.path.join(os.path.dirname(__file__), 'setup.cfg'))

name = setup_cfg.get('package', 'name')
version = setup_cfg.get('package', 'version')
author = setup_cfg.get('package', 'author')
author_email = setup_cfg.get('package', 'author_email')

setup(
    name=name,
    version=version,
    description='A Kerberos context manager',
    long_description=get_long_description(),
    keywords='kerberos context',
    license='GPLv3',
    author=author,
    author_email=author_email,
    url='https://github.com/krbcontext/python-krbcontext',
    packages=find_packages(),
    python_requires='>=3.6',
    install_requires=["gssapi"],
    extras_require={
        "tests": ["pytest", "pytest-cov"],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
    ],
    project_urls={
        'Issue Reports': 'https://github.com/krbcontext/python-krbcontext/issues',
        'Source': 'https://github.com/krbcontext/python-krbcontext/',
        'Documentation': 'https://krbcontext.github.io/',
    },
)
