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

    krbContext aims to use Kerberos environment variable KRB5CCNAME to point
    to a given local credential cache, which will be used by Kerberos library,
    whatever the krb5 API or GSSAPI, to store ticket.

    If default credential cache is used, it is unnecessary to point out to the
    default by that variable, Kerberos library is able to handle that.

    After credential cache is initialized, original value of KRB5CCNAME, if
    have, must be restored. Otherwise, KRB5CCNAME must not be present in
    program's environment variables.

    krbContext can work with ``with`` statement to simplify your code.
    """

    def __init__(self, using_keytab=None, principal=None, keytab_file=None,
                 ccache_file=None, password=None):
        """Initialize context

        :param bool using_keytab: indicate whether to initialize credential
            cache from a keytab.
        :param str principal: Kerberos principal to get TGT from KDC. To
            initialize using a regular user Kerberos account, a principal would
            be name@EXAMPLE.COM. To initialize using a keytab, a principal
            would be a service principal with format
            service_name/hostname@EXAMPLE.COM.
        :param str keytab_file: file name of a keytab file, either absolute or
            relative is okay.
        :param str ccache_file: file name of a credential cache to initialize.
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

        In the case of using Key table, principal is required. keytab_file is
        optional, and default key table file ``/etc/krb5.keytab`` is used if
        keytab_file is not provided.

        In the case of initializing as a regular user, principal is optional,
        and current user's effective name is used if principal is not provided.

        By default, initialize credentials cache for regular user.

        :param dict options: keyword arguments that contains values passed from
            caller. Each one will be converted to corresponding krbV objects.
            Refer to ``krbContext.__init__`` to see each argument.
        :return: a mapping containing each converted krbV objects. It could
            contains keys principal, ccache, keytab, and using_keytab.
        :rtype: dict
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
        :raises GSSError: if krbcontext can't handle this error raised while
            initiating an instance of Credential.
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
        """Use keytab to initialize credential cache

        :param principal: the service principal name.
        :type principal: instance of ``gssapi.names.Name``.
        :param str keytab: the keytab file containing service' principal.
        :param str ccache: the credential cache to be initialized.
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
        """Initialize credential cache as a regular user

        **Causion:** once you enter password from command line, or pass it to
        API directly, the given password is not encrypted always. Although
        getting credential with password works, you should not use it in any
        formal production environment from security point of view. If you need
        to initialize credential in an application to application Kerberos
        authentication context, keytab has to be used.

        :param principal: the principal representing a Kerberos regular user.
        :param str ccache: the credential cache to be initialized.
        :param str password: the password used to get credential.
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
        ccache = self.cleaned_options['ccache']
        if self.cleaned_options['using_keytab']:
            self.init_with_keytab(self.cleaned_options['principal'],
                                  self.cleaned_options['keytab'],
                                  ccache)
        else:
            self.init_with_password(self.cleaned_options['principal'],
                                    ccache,
                                    self.cleaned_options['password'])

        if ccache == DEFAULT_CCACHE:
            if ENV_KRB5CCNAME in os.environ:
                self.original_krb5ccname = os.environ[ENV_KRB5CCNAME]
                del os.environ[ENV_KRB5CCNAME]
        else:
            self.original_krb5ccname = os.environ.get(ENV_KRB5CCNAME)
            os.environ[ENV_KRB5CCNAME] = ccache

    def __enter__(self):
        self._init_lock.acquire()

        init_required = self.need_init()

        if init_required:
            self._prepare_context()

        self._initialized = True
        return self

    def __exit__(self, exc_type, exc_value, traceback):
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
