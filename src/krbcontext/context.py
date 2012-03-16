# -*- coding: utf-8 -*-

__all__ = [ 'krbcontext', 'KRB5KinitError', ]

import os, sys
import pwd
import subprocess

import krbV

from contextlib import contextmanager

class KRB5KinitError(Exception):
    pass

def get_login():
    ''' Get current effective user name '''

    return pwd.getpwuid(os.getuid()).pw_name

def init_ccache_as_regular_user(principal=None, ccache_file=None):
    '''Initialize credential cache as a regular user

    Return the filename of newly initialized credential cache
    '''

    if not os.isatty(sys.stdin):
        raise IOError('This is not running on console. So, you need to run kinit '
                      'with your principal manually before anything goes.')

    cmd = 'kinit %(ccache_file) %(principal)s'
    args = {}

    if principal:
        args['principal'] = principal
    else:
        args['principal'] = get_login()
    if ccache_file:
        args['ccache_file'] = ccache_file

    kinit_proc = subprocess.Popen(
        cmd.split(),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = kinit_proc.communicate()

    if kinit_proc.returncode > 0:
        raise KRB5KinitError(stdout_data)

    if ccache_file:
        return ccache_file
    else:
        context = krbV.default_context()
        ccache = context.default_ccache()
        return ccache.name

def init_ccache_with_keytab(principal=None, keytab_file=None, ccache_file=None):
    '''Initialize credential cache using keytab file

    Return the filename of newly initialized credential cache
    '''

    context = krbV.default_context()
    princ = krbV.Principal(name=principal, context=context)
    if keytab_file:
        keytab = krbV.Keytab(name=keytab_file, context=context)
    else:
        keytab = context.default_keytab()
    if ccache_file:
        ccache = krbV.CCache(name=ccache_file, context=context)
    else:
        ccache = context.default_ccache()

    ccache.init(princ)
    ccache.init_creds_keytab(principal=princ, keytab=keytab)
    return ccache_file

@contextmanager
def krbcontext(func, using_keytab=False, **kwargs):
    '''A context manager for Kerberos-related actions

    action: the method containing what to run in Kerberos context.
    using_keytab: specify to use Keytab file in Kerberos context if True,
                  or be as a regular user.
    kwargs: contains the necessary arguments used in kerberos context.
            It can contain principal, keytab_file, ccache_file.
            When you want to use Keytab file, keytab_file must be included.
    '''

    old_ccache = os.getenv('KRB5CCNAME')
    if using_keytab:
        ccache_file = init_ccache_with_keytab(**kwargs)
    else:
        ccache_file = init_ccache_as_regular_user(**kwargs)
    os.environ['KRB5CCNAME'] = ccache_file

    try:
        func()
    finally:
        if old_ccache:
            os.environ['KRB5CCNAME'] = old_ccache
        else:
            del os.environ['KRB5CCNAME']
