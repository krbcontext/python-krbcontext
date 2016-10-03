# -*- coding: utf-8 -*-

import krbV
import os
import time
import unittest

from datetime import datetime
from datetime import timedelta
from mock import patch
from mock import Mock

import config
import krbcontext.context as kctx

from krbcontext.context import is_initialize_ccache_necessary
from krbcontext.context import KRB5InitError
from krbcontext.utils import get_tgt_time
from krbcontext.utils import CredentialTime


def krb_default_cc_name():
    context = krbV.default_context()
    return context.default_ccache().name


def krb_default_keytab_name():
    context = krbV.default_context()
    return context.default_keytab().name


def get_fake_cred_time(expired):
    assert isinstance(expired, bool)
    delta = 5
    if expired:
        delta *= -1
    endtime = datetime.now() + timedelta(minutes=delta)
    return CredentialTime(authtime=None, starttime=None, endtime=endtime, renew_till=None)


class GetTGTTimeError(Exception):
    """Used for running tests only"""


class CCacheInitializationRequiredTest(unittest.TestCase):

    def setUp(self):
        self.context = krbV.default_context()
        self.ccache = krbV.CCache(config.user_ccache_file, context=self.context)
        self.principal = krbV.Principal(config.service_principal, context=self.context)

    @patch('krbcontext.context.get_tgt_time')
    def test_init_if_ccache_is_expired(self, get_tgt_time):
        get_tgt_time.return_value = get_fake_cred_time(expired=True)

        result = is_initialize_ccache_necessary(self.context, self.ccache, self.principal)
        self.assertTrue(result)

    @patch('krbcontext.context.get_tgt_time')
    def test_dont_init_ccache_is_not_expired(self, get_tgt_time):
        get_tgt_time.return_value = get_fake_cred_time(expired=False)

        result = is_initialize_ccache_necessary(self.context, self.ccache, self.principal)
        self.assertFalse(result)

    def test_ccache_is_not_valid(self):
        err_codes = (krbV.KRB5_FCC_NOFILE,
                     krbV.KRB5_CC_FORMAT,
                     krbV.KRB5_CC_NOTFOUND)

        for err_code in err_codes:
            with patch('krbcontext.context.get_tgt_time',
                       side_effect=krbV.Krb5Error(err_code, '')):
                result = is_initialize_ccache_necessary(self.context, self.ccache, self.principal)
                self.assertTrue(result)

    def test_error_when_get_cred_time(self):
        with patch('krbcontext.context.get_tgt_time', side_effect=GetTGTTimeError()):
            self.assertRaises(GetTGTTimeError, is_initialize_ccache_necessary,
                              self.context, self.ccache, self.principal)

    def test_non_monitored_error_occurs(self):
        # krbV.KRB5_CC_NOT_KTYPE is choosed for raising an non-monitored error,
        # which means an error is raised but that is not treated as a flag
        # indicating the credential cache should be initialized.
        # Thus, for running this test, any other errors could be used as long
        # as it is not known errors by krbcontext.
        with patch('krbcontext.context.get_tgt_time',
                   side_effect=krbV.Krb5Error(krbV.KRB5_CC_NOT_KTYPE, '')):
            self.assertRaises(krbV.Krb5Error, is_initialize_ccache_necessary,
                              self.context, self.ccache, self.principal)


class GetDefaultCCacheTest(unittest.TestCase):

    def setUp(self):
        self.context = krbV.default_context()

    def test_get_default_ccache_from_env(self):
        with patch.dict(os.environ, {'KRB5CCNAME': config.user_ccache_file}, clear=False):
            ccache = kctx.get_default_ccache(self.context)
            self.assertEqual(config.user_ccache_file, ccache.name)

    def test_get_default_ccache_from_filesystem(self):
        with patch.dict(os.environ, {'fake_var': '1'}, clear=True):
            ccache = kctx.get_default_ccache(self.context)
            default_ccache = '/tmp/krb5cc_{0}'.format(os.getuid())
            self.assertEqual(default_ccache, ccache.name)


class CleanArgumetsUsingKeytabTest(unittest.TestCase):

    def setUp(self):
        self.context = krbV.default_context()
        self.kwargs = {
            'using_keytab': True,
        }

    def testPrincipalNotProvide(self):
        self.assertRaises(NameError, kctx.clean_context_options, self.context, **self.kwargs)

    def testAllDefault(self):
        self.kwargs.update({
            'principal': config.service_principal,
        })
        cleaned_kwargs = kctx.clean_context_options(self.context, **self.kwargs)

        self.assert_('principal' in cleaned_kwargs)
        self.assertEqual(cleaned_kwargs['principal'].name, config.service_principal)

        self.assert_('ccache' in cleaned_kwargs)
        expected_ccache_file = krb_default_cc_name()
        self.assertEqual(cleaned_kwargs['ccache'].name, expected_ccache_file)

        self.assert_('keytab' in cleaned_kwargs)
        kt = cleaned_kwargs['keytab']
        expected_kt_name = krb_default_keytab_name()
        self.assertEqual(kt.name, expected_kt_name)

    def testSpecifyAllManually(self):
        self.kwargs.update({
            'principal': config.service_principal,
            'ccache_file': config.user_ccache_file,
            'keytab_file': config.user_keytab_file,
        })

        cleaned_kwargs = kctx.clean_context_options(self.context, **self.kwargs)

        self.assert_('ccache' in cleaned_kwargs)
        self.assertEqual(cleaned_kwargs['ccache'].name, config.user_ccache_file)

        self.assert_('keytab' in cleaned_kwargs)
        kt = cleaned_kwargs['keytab']
        expected_kt_name = config.user_keytab_file
        self.assert_(kt.name.endswith(expected_kt_name))


class CleanArgumetsAsRegularUserTest(unittest.TestCase):

    def setUp(self):
        self.context = krbV.default_context()

    def testAllDefault(self):
        cleaned_kwargs = kctx.clean_context_options(self.context, **{})
        self.assert_('using_keytab' in cleaned_kwargs)
        self.assertFalse(cleaned_kwargs['using_keytab'])

        self.assert_('principal' in cleaned_kwargs)
        principal = cleaned_kwargs['principal']
        self.assertEqual(principal.name.split('@')[0], kctx.get_login())

        self.assert_('ccache' in cleaned_kwargs)
        ccache = cleaned_kwargs['ccache']
        self.assertEqual(ccache.name, krb_default_cc_name())

    def testSpecifyAllManually(self):
        kwargs = {
            'using_keytab': False,
            'principal': config.user_principal,
            'ccache_file': config.user_ccache_file,
        }
        cleaned_kwargs = kctx.clean_context_options(self.context, **kwargs)

        self.assert_('principal' in cleaned_kwargs)
        test_user_princ = cleaned_kwargs['principal']
        self.assertEqual(test_user_princ.name, config.user_principal)

        self.assert_('ccache' in cleaned_kwargs)
        ccache = cleaned_kwargs['ccache']
        self.assertEqual(ccache.name, config.user_ccache_file)


class InitAsRegularUserTest(unittest.TestCase):

    @patch('sys.stdin')
    @patch('krbcontext.context.get_tgt_time')
    @patch('krbcontext.context.subprocess.Popen')
    def test_init(self, Popen, get_tgt_time, stdin):
        get_tgt_time.return_value = get_fake_cred_time(expired=True)
        Popen.return_value.communicate.return_value = ('', '')
        Popen.return_value.returncode = 0
        stdin.isatty.return_value = True

        with kctx.krbContext():
            pass

    @patch('sys.stdin')
    @patch('krbcontext.context.subprocess.Popen')
    def test_init_command_fails(self, Popen, stdin):
        Popen.return_value.returncode = 1
        Popen.return_value.communicate.return_value = ('', 'something goes wrong.')
        stdin.isatty.return_value = True

        try:
            with kctx.krbContext():
                pass
        except Exception as e:
            self.assertTrue(isinstance(e, KRB5InitError))

    @patch('sys.stdin')
    @patch('krbcontext.context.get_tgt_time')
    def test_not_in_terminal(self, get_tgt_time, stdin):
        stdin.isatty.return_value = False
        get_tgt_time.return_value = get_fake_cred_time(expired=True)

        try:
            with kctx.krbContext():
                pass
        except Exception as e:
            self.assertTrue(isinstance(e, IOError))


class InitUsingKeytab(unittest.TestCase):

    @patch('krbcontext.context.get_tgt_time')
    def test_no_need_init(self, get_tgt_time):
        get_tgt_time.return_value = get_fake_cred_time(expired=False)

        with patch.dict(os.environ, {}, clear=True):
            with kctx.krbContext(using_keytab=True,
                                 principal='HTTP/www.example.com@EXAMPLE.COM') as context:
                self.assertFalse(context.initialized)
                self.assertTrue('KRB5CCNAME' not in os.environ)
            self.assertTrue('KRB5CCNAME' not in os.environ)

    @patch('krbV.CCache.init')
    @patch('krbV.CCache.init_creds_keytab')
    def assert_krbContext(self, init_creds_keytab, init):
        with kctx.krbContext(using_keytab=True,
                             principal='HTTP/www.example@EXAMPLE.COM',
                             keytab_file='/etc/httpd/conf/httpd.keytab',
                             ccache_file='/tmp/krb5cc_app') as context:
            self.assertTrue(context.initialized)
            self.assertEqual('/tmp/krb5cc_app', os.environ['KRB5CCNAME'])

    @patch('krbcontext.context.get_tgt_time')
    def test_init(self, get_tgt_time):
        get_tgt_time.return_value = get_fake_cred_time(expired=True)

        with patch.dict(os.environ, {}, clear=True):
            self.assert_krbContext()
            self.assertTrue('KRB5CCNAME' not in os.environ)

        original_krb5ccname = '/tmp/krb5cc_system'
        with patch.dict(os.environ, {'KRB5CCNAME': original_krb5ccname}, clear=True):
            self.assert_krbContext()
            self.assertEqual(original_krb5ccname, os.environ['KRB5CCNAME'])


class BackwardCompabilityTest(unittest.TestCase):
    """Test backward compatible name krbcontext"""

    @patch('krbcontext.context.get_tgt_time')
    def test_krbcontext(self, get_tgt_time):
        get_tgt_time.return_value = get_fake_cred_time(expired=False)

        with kctx.krbcontext(using_keytab=True,
                             principal='HTTP/www.example.com@EXAMPLE.COM'):
            pass


class krbContextPropertiesAccessibleTest(unittest.TestCase):

    @patch('krbcontext.context.get_tgt_time')
    def test_access_initialized_property(self, get_tgt_time):
        get_tgt_time.return_value = get_fake_cred_time(expired=False)

        with patch.dict(os.environ, {'fake_var': '1'}, clear=True):
            with kctx.krbContext(using_keytab=True,
                                 principal='HTTP/localhost@PYPI.PYTHON.COM',
                                 keytab_file='/etc/httpd/conf/httpd.keytab',
                                 ccache_file='/tmp/krb5cc_pid_appname') as ctx:
                self.assertFalse(ctx.initialized)


class GetTGTTimeTest(unittest.TestCase):

    def test_get_tgt_time(self):
        context = krbV.default_context()
        principal = krbV.Principal('cqi@EXAMPLE.COM')

        expected_authtime = time.time()
        expected_starttime = time.time()
        expected_endtime = time.time()
        expected_renew_till = time.time()

        ccache = Mock()
        ccache.get_credentials.return_value = (
            None, None, (0, None),
            (expected_authtime, expected_starttime, expected_endtime, expected_renew_till),
            None, None, None, None, None, None)

        cred_time = get_tgt_time(context, ccache, principal)

        self.assertEqual(datetime.fromtimestamp(expected_authtime), cred_time.authtime)
        self.assertEqual(datetime.fromtimestamp(expected_starttime), cred_time.starttime)
        self.assertEqual(datetime.fromtimestamp(expected_endtime), cred_time.endtime)
        self.assertEqual(datetime.fromtimestamp(expected_renew_till), cred_time.renew_till)
