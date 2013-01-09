# -*- coding: utf-8 -*-

from contextlib import contextmanager
from datetime import datetime
from utils import get_tgt_time
from utils import get_login

import krbV
import os, sys
import subprocess


__all__ = ( 'krbcontext',
            'KRB5InitError', )


ENV_KRB5CCNAME = 'KRB5CCNAME'

# TODO: put this into standalone module
class KRB5InitError(Exception):
    pass

def init_ccache_as_regular_user(principal, ccache):
    '''Initialize credential cache as a regular user

    Return the filename of newly initialized credential cache
    '''
    cmd = 'kinit -c %(ccache_file)s %(principal)s'
    args = { 'principal': principal.name,
             'ccache_file': ccache.name, }

    kinit_proc = subprocess.Popen(
        (cmd % args).split(),
        stderr=subprocess.PIPE)
    stdout_data, stderr_data = kinit_proc.communicate()

    if kinit_proc.returncode > 0:
        raise KRB5InitError(stderr_data[:stderr_data.find('\n')])

    return ccache.name

def init_ccache_with_keytab(principal, keytab, ccache):
    ''' Initialize credential cache using keytab file.

    Return the filename of newly initialized credential cache.
    '''
    ccache.init(principal)
    ccache.init_creds_keytab(principal=principal, keytab=keytab)
    return ccache.name

def get_default_ccache(context):
    if ENV_KRB5CCNAME in os.environ:
        return krbV.CCache(os.environ[ENV_KRB5CCNAME], context=context)
    else:
        return context.default_ccache()

def is_initialize_ccache_necessary(context, ccache, principal):
    ''' Judge whether initializing credential cache is necessary.

    In three cases, it is necessary to initialize credential cache.

    - Credential cache file does not exist.
    - Credential cache file has bad format.
    - TGT expires.

    When TGT expires, attemption that getting credentials will return error
    ``Match credentials not found``, whose error code is KRB5_CC_NOTFOUND.

    Arguments:

    - context, current context object.
    - ccache, the CCache object that is associated with context.
    - principal, the principal name that is being used for getting ticket.
    '''
    try:
        cred_time = get_tgt_time(context, ccache, principal)
    except krbV.Krb5Error, err:
        # Credentials cache does not exist. In this case, initialize
        # credential cache is required.
        monitor_errors = (krbV.KRB5_FCC_NOFILE,
                          krbV.KRB5_CC_FORMAT,
                          krbV.KRB5_CC_NOTFOUND,)
        err_code = err.args[0]
        is_init_required = err_code in monitor_errors
        if is_init_required:
            return True
        else:
            # If error is unexpected, raise it to caller
            raise
    except:
        # Just like the above raise statement
        raise
    return datetime.now() >= cred_time.endtime

def clean_kwargs(context, kwargs):
    ''' Clean argument to related object

    In the case of using Key table, principal is required. keytab_file is
    optional, and default key table file /etc/krb5.keytab is used if keytab_file
    is not provided.

    In the case of initing as a regular user, principal is optional, and current
    user's effective name is used if principal is not provided.

    By default, initialize credentials cache for regular user.
    '''
    cleaned_kwargs = {}

    using_keytab = kwargs.get('using_keytab', False)
    if using_keytab:
        # Principal is required when using key table to initialize
        # credential cache.
        principal_name = kwargs.get('principal', None)
        if principal_name is None:
            raise NameError('Principal is required when using key table.')
        else:
            principal = krbV.Principal(principal_name, context=context)
            cleaned_kwargs['principal'] = principal
        kt_name = kwargs.get('keytab_file', None)
        if kt_name is None:
            keytab = context.default_keytab()
        else:
            keytab = krbV.Keytab(kt_name, context=context)
        cleaned_kwargs['keytab'] = keytab
    else:
        # When initialize credentials cache with a regular user, clean
        # principal has different rule. It will return a valid Principal object
        # always.
        principal_name = kwargs.get('principal', None)
        if principal_name is None:
            principal_name = get_login()
        principal = krbV.Principal(principal_name, context=context)
        cleaned_kwargs['principal'] = principal
    cleaned_kwargs['using_keytab'] = using_keytab

    ccache_file = kwargs.get('ccache_file', None)
    if ccache_file is None:
        ccache = get_default_ccache(context)
    else:
        ccache = krbV.CCache(ccache_file, context=context)
    cleaned_kwargs['ccache'] = ccache

    return cleaned_kwargs

def init_ccache_if_necessary(context, kwargs):
    ''' Initialize credential cache if necessary.

    Arguments:
    - context: current krb5 context.
    - kwargs: cleaned kwargs passed to krbcontext.
    '''
    ccache = kwargs['ccache']
    principal = kwargs['principal']
    old_ccache = None
    init_required = is_initialize_ccache_necessary(context, ccache, principal)
    if init_required:
        old_ccache = os.getenv(ENV_KRB5CCNAME)
        if kwargs['using_keytab']:
            keytab = kwargs['keytab']
            ccache_file = init_ccache_with_keytab(principal, keytab, ccache)
        else:
            # If client script is not running in terminal, it is impossible for
            # user to enter his/her password.
            if not sys.stdin.isatty():
                raise IOError('This is not running on console. So, you need to '
                              'run kinit with your principal manually before '
                              'anything goes.')
            ccache_file = init_ccache_as_regular_user(principal, ccache)
        os.environ[ENV_KRB5CCNAME] = ccache_file
    return (init_required, old_ccache)

@contextmanager
def krbcontext(**kwargs):
    '''A context manager for Kerberos-related actions

    using_keytab: specify to use Keytab file in Kerberos context if True,
                  or be as a regular user.
    kwargs: contains the necessary arguments used in kerberos context.
            It can contain principal, keytab_file, ccache_file.
            When you want to use Keytab file, keytab_file must be included.
    '''
    context = krbV.default_context()
    kwargs = clean_kwargs(context, kwargs)
    inited, old_ccache = init_ccache_if_necessary(context, kwargs)

    try:
        yield
    finally:
        if inited:
            if old_ccache:
                os.environ[ENV_KRB5CCNAME] = old_ccache
            else:
                del os.environ[ENV_KRB5CCNAME]

