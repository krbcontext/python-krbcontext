# -*- coding: utf-8 -*-

from setuptools import setup, find_packages

def get_long_description():
    return open('README', 'r').read()

setup(
    name = 'krbcontext',
    version = '0.1',
    description = 'A Kerberos context manager',
    long_description = get_long_description(),
    keywords = ['krb', 'kerberos', 'context', 'principal', 'credential', 'ticket'],
    license = 'GPL',
    author = 'Chenxiong Qi',
    author_email = 'cqi@redhat.com',
    url = 'https://github.com/tkdchen/python-krbcontext',

    packages = find_packages('src'),
    package_dir = { '': 'src', },

    classifiers = [
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
