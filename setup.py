# -*- coding: utf-8 -*-

from setuptools import setup, find_packages


def get_long_description():
    return '''%s

%s''' % (open('README.rst', 'r').read(), open('CHANGES.txt', 'r').read())

setup(
    name='krbcontext',
    version='0.3.3',
    description='A Kerberos context manager',
    long_description=get_long_description(),
    keywords='kerberos context',
    license='GPL',
    author='Chenxiong Qi',
    author_email='cqi@redhat.com',
    url='https://github.com/tkdchen/python-krbcontext',

    packages=find_packages(),

    setup_requires=['pytest-runner'],
    tests_require=['mock', 'pytest'],

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
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System :: Systems Administration',
    ],
)
