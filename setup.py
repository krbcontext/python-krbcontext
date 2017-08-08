# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def get_long_description():
    return '''%s

%s''' % (open('README.rst', 'r').read(), open('CHANGES', 'r').read())


def get_install_requires():
    with open('requirements.txt', 'r') as fin:
        return [package.strip() for package in fin]


def get_test_requires():
    with open('test-requirements.txt', 'r') as fin:
        return [package.strip() for package in fin
                if not package.startswith('-r')]


setup(
    name='krbcontext',
    version='0.3.3',
    description='A Kerberos context manager',
    long_description=get_long_description(),
    keywords='kerberos context',
    license='GPL',
    author='Chenxiong Qi',
    author_email='cqi@redhat.com',
    url='https://github.com/krbcontext/krbcontext',

    packages=find_packages(),

    install_requires=get_install_requires(),
    tests_require=get_test_requires(),

    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: POSIX',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
    ],
)
