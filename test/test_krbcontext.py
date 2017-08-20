# -*- coding: utf-8 -*-

import os
import unittest

import gssapi

from mock import call, patch, PropertyMock

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

        self.assertTrue(context._cleaned_options['using_keytab'])
        expected_princ = gssapi.names.Name(
            'HTTP/hostname@EXAMPLE.COM',
            gssapi.names.NameType.kerberos_principal)
        self.assertEqual(expected_princ, context._cleaned_options['principal'])
        self.assertEqual(kctx.DEFAULT_CCACHE,
                         context._cleaned_options['ccache'])
        self.assertEqual(kctx.DEFAULT_KEYTAB,
                         context._cleaned_options['keytab'])

    @patch('os.path.exists')
    def test_specify_existing_keytab(self, exists):
        exists.return_value = True

        context = krbContext(using_keytab=True,
                             principal='HTTP/hostname@EXAMPLE.COM',
                             keytab_file='/etc/app/app.keytab')
        self.assertEqual('/etc/app/app.keytab',
                         context._cleaned_options['keytab'])

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
                         context._cleaned_options['ccache'])


class CleanArgumentsAsRegularUserTest(unittest.TestCase):
    """Test clean_context_options for not using keytab"""

    @patch('krbcontext.context.get_login')
    def test_all_defaults(self, get_login):
        get_login.return_value = 'cqi'

        context = krbContext()

        expected_princ = gssapi.names.Name(get_login.return_value,
                                           gssapi.names.NameType.user)
        self.assertEqual(expected_princ,
                         context._cleaned_options['principal'])
        self.assertEqual(kctx.DEFAULT_CCACHE,
                         context._cleaned_options['ccache'])
        self.assertFalse(context._cleaned_options['using_keytab'])

    def test_specify_ccache(self):
        context = krbContext(principal='cqi',
                             ccache_file='/var/app/krb5_ccache')
        self.assertEqual('/var/app/krb5_ccache',
                         context._cleaned_options['ccache'])

    def test_specify_principal(self):
        context = krbContext(principal='cqi')
        expected_princ = gssapi.names.Name('cqi', gssapi.names.NameType.user)
        self.assertEqual(expected_princ,
                         context._cleaned_options['principal'])


class TestInitWithKeytab(unittest.TestCase):
    """Test krbContext.init_with_keytab"""

    def setUp(self):
        self.service_principal = 'HTTP/hostname@EXAMPLE.COM'
        self.princ_name = gssapi.names.Name(
            self.service_principal,
            gssapi.names.NameType.kerberos_principal)

        self.Lock = patch('krbcontext.context.Lock')
        self.Lock.start()

        # No need to create a real temp file for tests
        self.tmp_ccache = 'tmp-ccache'
        self.mkstemp = patch('tempfile.mkstemp',
                             return_value=(1, self.tmp_ccache))
        self.mkstemp.start()

        self.os_close = patch('os.close')
        self.os_close.start()

    def tearDown(self):
        self.os_close.stop()
        self.mkstemp.stop()
        self.Lock.stop()

    @patch('gssapi.creds.Credentials')
    def test_cred_not_expired(self, Credentials):
        context = krbContext(using_keytab=True,
                             principal=self.service_principal)
        context.init_with_keytab()

        self.assertEqual(1, Credentials.call_count)
        Credentials.return_value.store.assert_not_called()

    @patch('gssapi.creds.Credentials')
    def test_init_in_default_ccache_with_default_keytab(self, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        context = krbContext(using_keytab=True,
                             principal=self.service_principal)
        context.init_with_keytab()

        Credentials.has_calls(
            call(usage='initiate', name=self.princ_name),
            call(usage='initiate', name=self.princ_name,
                 store={'ccache': self.tmp_ccache}),
        )
        Credentials.return_value.store.assert_called_once_with(
            store=None,
            usage='initiate',
            overwrite=True)

    @patch('gssapi.creds.Credentials')
    @patch('os.path.exists', return_value=True)
    def test_init_in_default_ccache_with_given_keytab(self,
                                                      exists,
                                                      Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        keytab = '/etc/app/app.keytab'
        context = krbContext(using_keytab=True,
                             principal=self.service_principal,
                             keytab_file=keytab)
        context.init_with_keytab()

        Credentials.has_calls(
            call(usage='initiate', name=self.princ_name,
                 store={'client_keytab': keytab}),
            call(usage='initiate', name=self.princ_name,
                 store={'ccache': self.tmp_ccache}),
        )
        Credentials.return_value.store.assert_called_once_with(
            store=None,
            usage='initiate',
            overwrite=True)

    @patch('gssapi.creds.Credentials')
    def test_init_in_given_ccache_with_default_keytab(self, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        ccache = '/tmp/mycc'
        context = krbContext(using_keytab=True,
                             principal=self.service_principal,
                             ccache_file=ccache)
        context.init_with_keytab()

        Credentials.has_calls(
            call(usage='initiate', name=self.princ_name,
                 store={'ccache': ccache}),
            call(usage='initiate', name=self.princ_name,
                 store={'ccache': self.tmp_ccache}),
        )
        Credentials.return_value.store.assert_called_once_with(
            store={'ccache': ccache},
            usage='initiate',
            overwrite=True)

    @patch('gssapi.creds.Credentials')
    @patch('os.path.exists', return_value=True)
    def test_init_with_given_keytab_and_ccache(self, exists, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        keytab = '/etc/app/app.keytab'
        ccache = '/tmp/mycc'
        context = krbContext(using_keytab=True,
                             principal=self.service_principal,
                             keytab_file=keytab,
                             ccache_file=ccache)
        context.init_with_keytab()

        Credentials.has_calls(
            call(usage='initiate', name=self.princ_name,
                 store={'client_keytab': keytab, 'ccache': ccache}),
            call(usage='initiate', name=self.princ_name,
                 store={'client_keytab': keytab, 'ccache': self.tmp_ccache}),
        )
        Credentials.return_value.store.assert_called_once_with(
            store={'ccache': ccache},
            usage='initiate',
            overwrite=True)


class TestInitWithPassword(unittest.TestCase):
    """Test krbContext.init_with_password"""

    def setUp(self):
        self.principal = 'cqi'
        self.princ_name = gssapi.names.Name(self.principal,
                                            gssapi.names.NameType.user)

    @patch('gssapi.creds.Credentials')
    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred_into')
    def test_no_need_init_if_not_expired(
            self, store_cred_into, acquire_cred_with_password, Credentials):
        context = krbContext(using_keytab=False,
                             principal=self.principal,
                             password='security')
        context.init_with_password()

        self.assertEqual(1, Credentials.call_count)
        store_cred_into.assert_not_called()
        acquire_cred_with_password.assert_not_called()

    @patch('gssapi.creds.Credentials')
    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred')
    def test_init_in_default_ccache(
            self, store_cred, acquire_cred_with_password, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

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

    @patch('gssapi.creds.Credentials')
    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred_into')
    def test_init_in_given_ccache(
            self, store_cred_into, acquire_cred_with_password, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        ccache = '/tmp/mycc'
        context = krbContext(using_keytab=False,
                             principal=self.principal,
                             ccache_file=ccache,
                             password='security')
        context.init_with_password()

        Credentials.assert_called_once_with(
                usage='initiate',
                name=self.princ_name,
                store={'ccache': ccache})

        acquire_cred_with_password.assert_called_once_with(
            self.princ_name, 'security')

        store_cred_into.assert_called_once_with(
            {'ccache': '/tmp/mycc'},
            acquire_cred_with_password.return_value.creds,
            usage='initiate',
            overwrite=True)

    @patch('gssapi.creds.Credentials')
    @patch('sys.stdin.isatty', return_value=True)
    @patch('getpass.getpass')
    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred')
    def test_init_cred_with_need_enter_password(self, store_cred,
                                                acquire_cred_with_password,
                                                getpass, isatty,
                                                Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))
        getpass.return_value = 'mypassword'

        context = krbContext(using_keytab=False, principal=self.principal)
        context.init_with_password()

        isatty.assert_called_once()
        # Ensure this must be called.
        getpass.assert_called_once()

        Credentials.assert_called_once_with(usage='initiate',
                                            name=self.princ_name)

        acquire_cred_with_password.assert_called_once_with(
            self.princ_name, 'mypassword')

        store_cred.assert_called_once_with(
            acquire_cred_with_password.return_value.creds,
            usage='initiate',
            overwrite=True)

    @patch('gssapi.creds.Credentials')
    @patch('sys.stdin.isatty', return_value=False)
    def test_init_with_entering_password_but_not_in_atty(self,
                                                         isatty,
                                                         Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

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

    @patch('gssapi.creds.Credentials')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_with_default_keytab(self, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM',
                        ccache_file='/tmp/my_cc'):
            self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])

    @patch('gssapi.creds.Credentials')
    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_in_default_ccache_with_password(
            self, store_cred, acquire_cred_with_password, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        with krbContext(using_keytab=False,
                        principal='cqi',
                        password='security'):
            self.assertNotIn('KRB5CCNAME', os.environ)

        self.assertNotIn('KRB5CCNAME', os.environ)

    @patch('gssapi.creds.Credentials')
    @patch('gssapi.raw.acquire_cred_with_password')
    @patch('gssapi.raw.store_cred')
    @patch.dict('os.environ', {'KRB5CCNAME': '/tmp/my_cc'}, clear=True)
    def test_after_init_in_default_ccache_original_ccache_should_be_restored(
            self, store_cred, acquire_cred_with_password, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        with krbContext(using_keytab=False,
                        principal='cqi',
                        password='security'):
            self.assertNotIn('KRB5CCNAME', os.environ)

        self.assertIn('KRB5CCNAME', os.environ)
        self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])

    @patch('gssapi.creds.Credentials')
    @patch.dict('os.environ', {'KRB5CCNAME': '/tmp/my_cc'}, clear=True)
    def test_original_ccache_should_be_restored(self, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM',
                        ccache_file='/tmp/app_pid_cc'):
            # Inside context, given ccache should be used.
            self.assertEqual('/tmp/app_pid_cc', os.environ['KRB5CCNAME'])

        self.assertIn('KRB5CCNAME', os.environ)
        self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])

    @patch('gssapi.creds.Credentials')
    @patch.dict('os.environ', {}, clear=True)
    def test_init_in_default_ccache_without_original_krb5ccname_is_set(
            self, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM'):
            self.assertNotIn('KRB5CCNAME', os.environ)

        # Originally, no KRB5CCNAME is set, it should be cleaned after exit.
        self.assertNotIn('KRB5CCNAME', os.environ)

    @patch('gssapi.creds.Credentials')
    @patch.dict('os.environ', {'KRB5CCNAME': '/tmp/my_cc'}, clear=True)
    def test_init_in_default_ccache_and_original_krb5ccname_is_set(
            self, Credentials):
        type(Credentials.return_value).lifetime = PropertyMock(
            side_effect=gssapi.exceptions.ExpiredCredentialsError(1, 1))

        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM'):
            self.assertNotIn('KRB5CCNAME', os.environ)

        self.assertIn('KRB5CCNAME', os.environ)
        self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])

    @patch('gssapi.creds.Credentials')
    @patch.dict(os.environ, {'KRB5CCNAME': '/tmp/my_cc'}, clear=True)
    def test_do_nothing_if_unnecessary_to_init(self, Credentials):
        with krbContext(using_keytab=True,
                        principal='app/hostname@EXAMPLE.COM'):
            # Nothing is changed, but original KRB5CCNAME must be removed
            # since default ccache is used.
            self.assertNotIn('KRB5CCNAME', os.environ)

        # Original ccache must be restored.
        self.assertEqual('/tmp/my_cc', os.environ['KRB5CCNAME'])


class TestGetLogin(unittest.TestCase):
    """Test get_login"""

    @patch('os.getuid', return_value=1001)
    @patch('pwd.getpwuid')
    def test_get_login(self, getpwuid, getuid):
        getpwuid.return_value.pw_name = 'user'

        user = get_login()

        getpwuid.assert_called_once_with(getuid.return_value)
        self.assertEqual('user', user)
