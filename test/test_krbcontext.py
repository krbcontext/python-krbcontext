# -*- coding: utf-8 -*-

import os
import unittest

import gssapi

from mock import patch

import krbcontext.context as kctx
from krbcontext.context import krbContext
from krbcontext.context import get_login


class CleanArgumetsUsingKeytabTest(unittest.TestCase):
    """Test clean_context_options for using keytab"""

    def test_missing_principal(self):
        self.assertRaises(ValueError, krbContext, using_keytab=True)

    def test_all_defaults(self):
        context = krbContext(using_keytab=True,
                             principal='HTTP/hostname@EXAMPLE.COM')

        self.assertTrue(context.cleaned_options['using_keytab'])
        expected_princ = gssapi.names.Name(
            'HTTP/hostname@EXAMPLE.COM',
            gssapi.names.NameType.kerberos_principal)
        self.assertEqual(expected_princ, context.cleaned_options['principal'])
        self.assertEqual(kctx.DEFAULT_CCACHE,
                         context.cleaned_options['ccache'])
        self.assertEqual(kctx.DEFAULT_KEYTAB,
                         context.cleaned_options['keytab'])

    @patch('os.path.exists')
    def test_specify_existing_keytab(self, exists):
        exists.return_value = True

        context = krbContext(using_keytab=True,
                             principal='HTTP/hostname@EXAMPLE.COM',
                             keytab_file='/etc/app/app.keytab')
        self.assertEqual('/etc/app/app.keytab',
                         context.cleaned_options['keytab'])

    @patch('os.path.exists')
    def test_specify_nonexisting_keytab(self, exists):
        exists.return_value = False

        self.assertRaises(ValueError,
                          krbContext,
                          using_keytab=True,
                          principal='HTTP/hostname@EXAMPLE.COM',
                          keytab_file='/etc/app/app.keytab')

    def test_specify_ccache(self):
        context = krbContext(using_keytab=True,
                             principal='HTTP/hostname@EXAMPLE.COM',
                             ccache_file='/var/app/krb5_ccache')
        self.assertEqual('/var/app/krb5_ccache',
                         context.cleaned_options['ccache'])


class CleanArgumentsAsRegularUserTest(unittest.TestCase):
    """Test clean_context_options for not using keytab"""

    @patch('krbcontext.context.get_login')
    def test_all_defaults(self, get_login):
        get_login.return_value = 'cqi'

        context = krbContext()

        expected_princ = gssapi.names.Name(get_login.return_value,
                                           gssapi.names.NameType.user)
        self.assertEqual(expected_princ, context.cleaned_options['principal'])
        self.assertEqual(kctx.DEFAULT_CCACHE,
                         context.cleaned_options['ccache'])
        self.assertFalse(context.cleaned_options['using_keytab'])

    def test_specify_ccache(self):
        context = krbContext(principal='cqi',
                             ccache_file='/var/app/krb5_ccache')
        self.assertEqual('/var/app/krb5_ccache',
                         context.cleaned_options['ccache'])

    def test_specify_principal(self):
        context = krbContext(principal='cqi')
        expected_princ = gssapi.names.Name('cqi', gssapi.names.NameType.user)
        self.assertEqual(expected_princ, context.cleaned_options['principal'])


class FakeCredentials(object):
    """Used for test test_ccache_is_expired"""

    def __init__(self, *args, **kwargs):
        """Actually no need to initialize this fake object"""
        self.args = args
        self.kwargs = kwargs

    @property
    def lifetime(self):
        """test_ccache_is_expired needs to catch ExpiredCredentialsError"""
        raise gssapi.exceptions.ExpiredCredentialsError(1, 1)


class TestIsInitializeCCacheNecessary(unittest.TestCase):
    """Test is_initialize_ccache_necessary"""

    @patch('gssapi.creds.Credentials')
    def test_no_need_by_checking_from_default_ccache(self, Credentials):
        context = krbContext(principal='cqi')
        result = context.need_init()
        self.assertFalse(result)

    @patch('gssapi.creds.Credentials')
    def test_no_need_by_checking_from_given_ccache(self, Credentials):
        context = krbContext(principal='cqi', ccache_file='/tmp/my_cc')
        result = context.need_init()

        self.assertFalse(result)
        Credentials.assert_called_once_with(
            usage='initiate', store={'ccache': '/tmp/my_cc'})

    @patch('gssapi.creds.Credentials')
    def test_ccache_not_found(self, Credentials):
        Credentials.side_effect = gssapi.exceptions.GSSError(1, 2529639107)

        context = krbContext(principal='cqi', ccache_file='/tmp/my_cc')
        result = context.need_init()
        self.assertTrue(result)

    @patch('gssapi.creds.Credentials')
    def test_ccache_has_bad_format(self, Credentials):
        Credentials.side_effect = gssapi.exceptions.GSSError(1, 2529639111)

        context = krbContext(principal='cqi', ccache_file='/tmp/my_cc')
        result = context.need_init()
        self.assertTrue(result)

    @patch('gssapi.creds.Credentials')
    def test_ccache_no_cred_available(self, Credentials):
        Credentials.side_effect = gssapi.exceptions.GSSError(1, 2529639053)

        context = krbContext(principal='cqi', ccache_file='/tmp/my_cc')
        result = context.need_init()
        self.assertTrue(result)

    @patch('gssapi.creds.Credentials', new=FakeCredentials)
    def test_ccache_is_expired(self):
        context = krbContext(principal='cqi',
                             ccache_file='/tmp/app/krb5_my_cc')
        result = context.need_init()
        self.assertTrue(result)

    @patch('gssapi.creds.Credentials')
    def test_raise_if_unknown_gss_error_is_caught(self, Credentials):
        Credentials.side_effect = gssapi.exceptions.GSSError(1, 99999999)

        context = krbContext(principal='cqi', ccache_file=kctx.DEFAULT_CCACHE)
        self.assertRaises(gssapi.exceptions.GSSError, context.need_init)


class TestInitWithKeytab(unittest.TestCase):
    """Test init_ccache_with_keytab"""

    def setUp(self):
        self.service_principal = 'HTTP/hostname@EXAMPLE.COM'
        self.princ_name = gssapi.names.Name(
            self.service_principal,
            gssapi.names.NameType.kerberos_principal)

        self.Lock = patch('krbcontext.context.Lock')
        self.Lock.start()

    def tearDown(self):
        self.Lock.stop()

    @patch('gssapi.creds.Credentials')
    def test_init_with_all_defaults(self, Credentials):
        context = krbContext(using_keytab=True,
                             principal=self.service_principal)
        context.init_with_keytab()

        Credentials.assert_called_once_with(
            usage='initiate', name=self.princ_name, store={})

    @patch('gssapi.creds.Credentials')
    @patch('os.path.exists', return_value=True)
    def test_init_with_given_keytab(self, exists, Credentials):
        keytab = '/etc/app/app.keytab'
        context = krbContext(using_keytab=True,
                             principal=self.service_principal,
                             keytab_file=keytab)
        context.init_with_keytab()

        Credentials.assert_called_once_with(usage='initiate',
                                            name=self.princ_name,
                                            store={'keytab': keytab})

    @patch('gssapi.creds.Credentials')
    @patch('os.remove')
    def test_init_with_given_ccache(self, remove, Credentials):
        ccache = '/tmp/mycc'
        context = krbContext(using_keytab=True,
                             principal=self.service_principal,
                             ccache_file=ccache)
        context.init_with_keytab()

        Credentials.assert_called_once_with(
            usage='initiate', name=self.princ_name, store={'ccache': ccache})

    @patch('gssapi.creds.Credentials')
    @patch('os.path.exists', return_value=True)
    @patch('os.remove')
    def test_init_with_given_keytab_and_ccache(
            self, remove, exists, Credentials):
        keytab = '/etc/app/app.keytab'
        ccache = '/tmp/mycc'
        context = krbContext(using_keytab=True,
                             principal=self.service_principal,
                             keytab_file=keytab,
                             ccache_file=ccache)
        context.init_with_keytab()

        Credentials.assert_called_once_with(
            usage='initiate',
            name=self.princ_name,
            store={'ccache': ccache, 'keytab': keytab})


class TestInitWithPassword(unittest.TestCase):
    """Test init_ccache_as_regular_user"""

    def setUp(self):
        self.principal = 'cqi'
        self.princ_name = gssapi.names.Name(self.principal,
                                            gssapi.names.NameType.user)

    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred')
    def test_init_cred_in_default_ccache(self,
                                         store_cred,
                                         acquire_cred_with_password):
        context = krbContext(using_keytab=False,
                             principal=self.principal,
                             password='security')
        context.init_with_password()

        acquire_cred_with_password.assert_called_once_with(
            self.princ_name, 'security')

        store_cred.assert_called_once_with(
            acquire_cred_with_password.return_value.creds,
            usage='initiate',
            overwrite=True)

    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred_into')
    def test_init_cred_in_given_ccache(self,
                                       store_cred_into,
                                       acquire_cred_with_password):
        context = krbContext(using_keytab=False,
                             principal=self.principal,
                             ccache_file='/tmp/mycc',
                             password='security')
        context.init_with_password()

        acquire_cred_with_password.assert_called_once_with(
            self.princ_name, 'security')

        store_cred_into.assert_called_once_with(
            {'ccache': '/tmp/mycc'},
            acquire_cred_with_password.return_value.creds,
            usage='initiate',
            overwrite=True)

    @patch('sys.stdin.isatty', return_value=True)
    @patch('getpass.getpass')
    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred')
    def test_init_cred_with_need_enter_password(self, store_cred,
                                                acquire_cred_with_password,
                                                getpass, isatty):
        getpass.return_value = 'mypassword'

        context = krbContext(using_keytab=False, principal=self.principal)
        context.init_with_password()

        isatty.assert_called_once()
        # Ensure this must be called.
        getpass.assert_called_once()

        acquire_cred_with_password.assert_called_once_with(
            self.princ_name, 'mypassword')

        store_cred.assert_called_once_with(
            acquire_cred_with_password.return_value.creds,
            usage='initiate',
            overwrite=True)

    @patch('sys.stdin.isatty', return_value=False)
    def test_init_cred_with_entering_password_but_not_in_atty(self, isatty):
        context = krbContext(using_keytab=False, principal=self.principal)
        self.assertRaises(IOError, context.init_with_password)

        context = krbContext(using_keytab=False,
                             principal=self.principal,
                             password='')
        self.assertRaises(IOError, context.init_with_password)


class TestKrbContextManager(unittest.TestCase):
    """Test krbContext context manager"""

    def setUp(self):
        # Do not actually operate threading lock
        self.init_Lock = patch('krbcontext.context.Lock')
        self.init_Lock.start()

    def tearDown(self):
        self.init_Lock.stop()

    @patch('krbcontext.context.krbContext.need_init', return_value=True)
    @patch('krbcontext.context.krbContext.init_with_keytab')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_with_default_keytab(self, init_with_keytab, need_init):
        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM',
                        ccache_file='/tmp/my_cc'):
            init_with_keytab.assert_called_once_with()
            self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])

    @patch('krbcontext.context.krbContext.need_init', return_value=True)
    @patch('krbcontext.context.krbContext.init_with_password')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_with_password(self, init_with_password, need_init):
        with krbContext(using_keytab=False,
                        principal='cqi',
                        password='security'):
            init_with_password.assert_called_once_with()
            self.assertNotIn('KRB5CCNAME', os.environ)

    @patch('krbcontext.context.krbContext.need_init', return_value=True)
    @patch('krbcontext.context.krbContext.init_with_keytab')
    @patch.dict('os.environ', {'KRB5CCNAME': '/tmp/my_cc'}, clear=True)
    def test_original_ccache_should_be_restored(self,
                                                init_with_keytab,
                                                need_init):
        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM',
                        ccache_file='/tmp/app_pid_cc'):
            # Inside context, given ccache should be used.
            self.assertEqual('/tmp/app_pid_cc', os.environ['KRB5CCNAME'])
            init_with_keytab.assert_called_once_with()

        self.assertIn('KRB5CCNAME', os.environ)
        self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])

    @patch('krbcontext.context.krbContext.need_init', return_value=True)
    @patch('krbcontext.context.krbContext.init_with_keytab')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_in_default_ccache_without_original_krb5ccname_is_set(
            self, init_with_keytab, need_init):
        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM'):
            self.assertNotIn('KRB5CCNAME', os.environ)
            init_with_keytab.assert_called_once_with()

        # Originally, no KRB5CCNAME is set, it should be cleaned after exit.
        self.assertNotIn('KRB5CCNAME', os.environ)

    @patch('krbcontext.context.krbContext.need_init', return_value=True)
    @patch('krbcontext.context.krbContext.init_with_keytab')
    @patch.dict('os.environ', {'KRB5CCNAME': '/tmp/my_cc'}, clear=True)
    def test_init_in_default_ccache_with_original_krb5ccname_is_set(
            self, init_with_keytab, need_init):
        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM'):
            self.assertNotIn('KRB5CCNAME', os.environ)
            init_with_keytab.assert_called_once_with()

        self.assertIn('KRB5CCNAME', os.environ)
        self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])

    @patch('krbcontext.context.krbContext.need_init', return_value=False)
    @patch('krbcontext.context.krbContext.init_with_keytab')
    def test_do_nothing_if_unnecessary_to_init(self,
                                               init_with_keytab,
                                               need_init):
        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM'):
            pass
        init_with_keytab.assert_not_called()


class TestGetLogin(unittest.TestCase):
    """Test get_login"""

    @patch('os.getuid', return_value=1001)
    @patch('pwd.getpwuid')
    def test_get_login(self, getpwuid, getuid):
        getpwuid.return_value.pw_name = 'user'

        user = get_login()

        getpwuid.assert_called_once_with(getuid.return_value)
        self.assertEqual('user', user)
