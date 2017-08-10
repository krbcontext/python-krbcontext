# -*- coding: utf-8 -*-

# Copyright (C) 2013  Chenxiong Qi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import gssapi
import os
import pwd
import sys
import getpass

from threading import Lock

__all__ = ('krbContext',)


DEFAULT_CCACHE = 'DEFAULT_CCACHE'
DEFAULT_KEYTAB = 'DEFAULT_KEYTAB'
ENV_KRB5CCNAME = 'KRB5CCNAME'


def get_login():
    """Get current effective user name"""
    return pwd.getpwuid(os.getuid()).pw_name


class krbContext(object):
    """A context manager for Kerberos-related actions

    krbContext is able to initialize credential cache automatically when the
    cache is not valid.

    krbContext aims to use Kerberos environment variable ``KRB5CCNAME`` to
    point to a given local credential cache, which will be used by Kerberos
    library, whatever the krb5 API or GSSAPI, to store ticket.

    If default credential cache is used, it is unnecessary to point out to the
    default by that variable, Kerberos library is able to handle that.

    After credential cache is initialized, original value of ``KRB5CCNAME``, if
    have, must be restored. Otherwise, ``KRB5CCNAME`` must not be present in
    program's environment variables.

    krbContext can work with ``with`` statement to simplify your code.
    """

    def __init__(self, using_keytab=False, principal=None, keytab_file=None,
                 ccache_file=None, password=None):
        """Initialize context

        :param bool using_keytab: indicate whether to initialize credential
            cache from a keytab. It is optional. Default is ``False``, ccache
            will be initialized with password, that is using a regular user's
            Kerberos name and password. When ``True`` is specified, keytab will
            be used.
        :param str principal: Kerberos principal to get TGT from KDC. To
            initialize using a regular user Kerberos account, a principal would
            be name@EXAMPLE.COM. To initialize using a keytab, a principal
            would be a service principal with format
            service_name/hostname@EXAMPLE.COM.
        :param str keytab_file: file name of a keytab file, either absolute or
            relative is okay. It is optional. Default keytab will be used if
            omitted.
        :param str ccache_file: file name of a credential cache to initialize.
            It is optional. Default ccache will be used if omitted.
        :param str password: user principal's password. It is optional. If
            omitted, program will be blocked and prompts to enter a password
            from command line, which requires program runs in a terminal.
        """
        self.cleaned_options = self.clean_options(using_keytab=using_keytab,
                                                  principal=principal,
                                                  keytab_file=keytab_file,
                                                  ccache_file=ccache_file,
                                                  password=password)
        self.original_krb5ccname = None

        self._init_lock = Lock()

    def clean_options(self,
                      using_keytab=False, principal=None,
                      keytab_file=None, ccache_file=None,
                      password=None):
        """Clean argument to related object

        :param bool using_keytab: refer to ``krbContext.__init__``.
        :param str principal: refer to ``krbContext.__init__``.
        :param str keytab_file: refer to ``krbContext.__init__``.
        :param str ccache_file: refer to ``krbContext.__init__``.
        :param str password: refer to ``krbContext.__init__``.

        :return: a mapping containing cleaned names and values, which are used
            internally.
        :rtype: dict
        :raises ValueError: principal is missing or given keytab file does not
            exist, when initialize from a keytab.
        """
        cleaned = {}

        if using_keytab:
            if principal is None:
                raise ValueError('Principal is required when using key table.')
            princ_name = gssapi.names.Name(
                principal, gssapi.names.NameType.kerberos_principal)

            if keytab_file is None:
                cleaned['keytab'] = DEFAULT_KEYTAB
            elif not os.path.exists(keytab_file):
                raise ValueError(
                    'Keytab file {0} does not exist.'.format(keytab_file))
            else:
                cleaned['keytab'] = keytab_file
        else:
            if principal is None:
                principal = get_login()
            princ_name = gssapi.names.Name(principal,
                                           gssapi.names.NameType.user)

        cleaned['using_keytab'] = using_keytab
        cleaned['principal'] = princ_name
        cleaned['ccache'] = ccache_file or DEFAULT_CCACHE
        cleaned['password'] = password

        return cleaned

    def need_init(self):
        """Check if necessary to initialize credential cache

        Following cases are handled

        * No Kerberos credentials available in cache.
        * Credential cache file does not exist.
        * Credential cache file has bad format.
        * TGT expires.

        :return: True if necessary to initialize, otherwise False.
        :rtype: bool
        :raises gssapi.exceptions.GSSError: if krbcontext can't handle this
            error raised from ``gssapi.creds.Credentials``.
        """
        ccache = self.cleaned_options['ccache']

        if ccache != DEFAULT_CCACHE:
            store = {'ccache': ccache}
        else:
            store = None

        try:
            creds = gssapi.creds.Credentials(usage='initiate', store=store)
        except gssapi.exceptions.GSSError as e:
            if e.min_code in (2529639053,  # No Kerberos credentials available
                              2529639111,  # Bad format in credentials cache
                              2529639107,  # No credentials cache found
                              ):
                return True
            raise

        try:
            creds.lifetime
        except gssapi.exceptions.ExpiredCredentialsError:
            return True

        return False

    def init_with_keytab(self):
        """Initialize credential cache with keytab

        :return: filename of newly initialized credential cache.
        :rtype: str
        """
        store = {}
        if self.cleaned_options['keytab'] != DEFAULT_KEYTAB:
            store['keytab'] = self.cleaned_options['keytab']
        if self.cleaned_options['ccache'] != DEFAULT_CCACHE:
            os.remove(self.cleaned_options['ccache'])
            store['ccache'] = self.cleaned_options['ccache']

        creds = gssapi.creds.Credentials(
            usage='initiate',
            name=self.cleaned_options['principal'],
            store=store)
        creds.lifetime

        return self.cleaned_options['ccache']

    def init_with_password(self):
        """Initialize credential cache with password

        **Causion:** once you enter password from command line, or pass it to
        API directly, the given password is not encrypted always. Although
        getting credential with password works, from security point of view, it
        is strongly recommended **NOT** use it in any formal production
        environment . If you need to initialize credential in an application to
        application Kerberos authentication context, keytab has to be used.

        :return: name of newly initialized credential cache
        :rtype: str
        :raises IOError: if password is not provided and need to prompt user to
            enter one.
        """
        password = self.cleaned_options['password']

        if not password:
            if not sys.stdin.isatty():
                raise IOError(
                    'krbContext is not running from a terminal. So, you need '
                    'to run kinit with your principal manually before '
                    'anything goes.')

            # If there is no password specified via API call, prompt to enter
            # one in order to continue to get credential. BUT, in some cases,
            # blocking program and waiting for input of password is really bad,
            # which may be only suitable for some simple use cases, for
            # example, writing some scripts to test something that need
            # Kerberos authentication. Anyway, whether it is really to enter a
            # password from command line, it depends on concrete use cases
            # totally.
            password = getpass.getpass()

        cred = gssapi.raw.acquire_cred_with_password(
            self.cleaned_options['principal'], password)

        ccache = self.cleaned_options['ccache']
        if ccache == DEFAULT_CCACHE:
            gssapi.raw.store_cred(cred.creds, usage='initiate', overwrite=True)
        else:
            gssapi.raw.store_cred_into({'ccache': ccache},
                                       cred.creds,
                                       usage='initiate',
                                       overwrite=True)
        return ccache

    def _prepare_context(self):
        """Prepare context

        Initialize credential cache with keytab or password according to
        ``using_keytab`` parameter. Then, ``KRB5CCNAME`` is set properly so
        that Kerberos library called in current context is able to get
        credential from correct cache.

        Internal use only.
        """
        ccache = self.cleaned_options['ccache']
        if self.cleaned_options['using_keytab']:
            self.init_with_keytab()
        else:
            self.init_with_password()

        if ccache == DEFAULT_CCACHE:
            if ENV_KRB5CCNAME in os.environ:
                self.original_krb5ccname = os.environ[ENV_KRB5CCNAME]
                del os.environ[ENV_KRB5CCNAME]
        else:
            self.original_krb5ccname = os.environ.get(ENV_KRB5CCNAME)
            os.environ[ENV_KRB5CCNAME] = ccache

    def __enter__(self):
        """Initialize ccache when necessary before executing user code

        Lock is acquired as well before user code executes.
        """
        self._init_lock.acquire()

        init_required = self.need_init()

        if init_required:
            self._prepare_context()

        self._initialized = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Clean context

        If ccache is reinitialized, original value of ``KRB5CCNAME`` will be
        restored correctly, if there was. And, lock gets released as well.
        """
        if self._initialized:
            # Restore original ccache, only when non-default ccache is used.
            # krbcontext only saves and set KRB5CCNAME when non-default ccache
            # is used, because Kerberos library is able to handle default one.
            if self.original_krb5ccname:
                # Originally, there might be KRB5CCNAME set, however, maybe
                # not. So, krbcontext only needs to restore original ccache
                # if it was set.
                os.environ[ENV_KRB5CCNAME] = self.original_krb5ccname

        self.original_krb5ccname = None

        self._init_lock.release()


# Backward compatibility
krbcontext = krbContext
