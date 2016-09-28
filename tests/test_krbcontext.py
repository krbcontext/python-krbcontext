# -*- coding: utf-8 -*-

import krbV
import os
import unittest

from datetime import datetime
from datetime import timedelta
from mock import patch

import config
import krbcontext.context as kctx

from krbcontext.context import is_initialize_ccache_necessary
from krbcontext.context import KRB5InitError
from krbcontext.utils import get_tgt_time
from krbcontext.utils import CredentialTime


def init_user_ccache(lifetime=None):
    cmd = 'kinit %(lifetime)s -c %(ccache)s %(princ)s' % {
        'lifetime': '-l %s' % lifetime if lifetime is not None else '',
        'princ': config.user_principal,
        'ccache': config.user_ccache_file, }
    os.system(cmd)


def init_ccache_using_keytab(lifetime=None):
    args = {
        'lifetime': '-l %s' % lifetime if lifetime is not None else '',
        'keytab': config.user_keytab_file,
        'princ': config.service_principal,
        'ccache': config.user_ccache_file,
    }
    cmd = 'kinit %(lifetime)s -c %(ccache)s -k -t %(keytab)s %(princ)s' % args
    os.system(cmd)


def krb_default_cc_name():
    context = krbV.default_context()
    return context.default_ccache().name


def krb_default_keytab_name():
    context = krbV.default_context()
    return context.default_keytab().name


def get_tgt_time_from_ccache(principal_name):
    context = krbV.default_context()
    principal = krbV.Principal(principal_name, context=context)
    ccache = krbV.CCache(config.user_ccache_file, context=context)
    ct = get_tgt_time(context, ccache, principal)
    return ct.endtime


class CCacheInitializationRequiredTest(unittest.TestCase):

    @patch('krbcontext.context.get_tgt_time')
    def test_init_if_ccache_is_expired(self, get_tgt_time):
        get_tgt_time.return_value = CredentialTime(authtime=None,
                                                   starttime=None,
                                                   endtime=datetime.now() - timedelta(minutes=5),
                                                   renew_till=None)

        context = krbV.default_context()
        ccache = krbV.CCache(config.user_ccache_file, context=context)
        principal = krbV.Principal(config.service_principal, context=context)
        result = is_initialize_ccache_necessary(context, ccache, principal)
        self.assertTrue(result)

    @patch('krbcontext.context.get_tgt_time')
    def test_dont_init_ccache_is_not_expired(self, get_tgt_time):
        get_tgt_time.return_value = CredentialTime(authtime=None,
                                                   starttime=None,
                                                   endtime=datetime.now() + timedelta(minutes=5),
                                                   renew_till=None)

        context = krbV.default_context()
        ccache = krbV.CCache(config.user_ccache_file, context=context)
        principal = krbV.Principal(config.service_principal, context=context)
        result = is_initialize_ccache_necessary(context, ccache, principal)
        self.assertFalse(result)

    def test_ccache_is_not_valid(self):
        err_codes = (krbV.KRB5_FCC_NOFILE,
                     krbV.KRB5_CC_FORMAT,
                     krbV.KRB5_CC_NOTFOUND)

        for err_code in err_codes:
            with patch('krbcontext.context.get_tgt_time',
                       side_effect=krbV.Krb5Error(err_code, '')):
                context = krbV.default_context()
                ccache = krbV.CCache(config.user_ccache_file, context=context)
                principal = krbV.Principal(config.service_principal, context=context)
                result = is_initialize_ccache_necessary(context, ccache, principal)
                self.assertTrue(result)


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

    def setUp(self):
        self.context = krbV.default_context()
        self.principal = krbV.Principal(config.user_principal, context=self.context)
        self.ccache = krbV.CCache(config.user_ccache_file, context=self.context)

    @patch('krbcontext.context.subprocess.Popen')
    def test_init_successfully(self, Popen):
        Popen.return_value.returncode = 0
        Popen.return_value.communicate.return_value = ('', '')

        cc_name = kctx.init_ccache_as_regular_user(self.principal, self.ccache)
        self.assertEqual(self.ccache.name, cc_name)

    @patch('krbcontext.context.subprocess.Popen')
    def test_init_command_fails(self, Popen):
        Popen.return_value.returncode = 1
        Popen.return_value.communicate.return_value = ('', 'something goes wrong.')

        self.assertRaises(KRB5InitError,
                          kctx.init_ccache_as_regular_user, self.principal, self.ccache)


@patch('krbcontext.context.get_tgt_time')
@patch('krbcontext.context.krbV.CCache.init')
@patch('krbcontext.context.krbV.CCache.init_creds_keytab')
def test_need_init(init_creds_keytab, init, get_tgt_time):
    get_tgt_time.return_value = CredentialTime(authtime=None,
                                               starttime=None,
                                               endtime=datetime.now() - timedelta(minutes=5),
                                               renew_till=None)
    with kctx.krbContext(using_keytab=True,
                         principal='HTTP/localhost@PYPI.PYTHON.COM',
                         keytab_file='/etc/httpd/conf/httpd.keytab',
                         ccache_file='/tmp/krb5cc_pid_appname'):
        pass


@patch('krbcontext.context.get_tgt_time')
def test_not_necessary_to_init(get_tgt_time):
    get_tgt_time.return_value = CredentialTime(authtime=None,
                                               starttime=None,
                                               endtime=datetime.now() + timedelta(minutes=5),
                                               renew_till=None)
    with kctx.krbContext(using_keytab=True,
                         principal='HTTP/localhost@PYPI.PYTHON.COM',
                         keytab_file='/etc/httpd/conf/httpd.keytab',
                         ccache_file='/tmp/krb5cc_pid_appname'):
        pass


@patch('krbcontext.context.get_tgt_time')
@patch('krbcontext.context.krbV.CCache.init')
@patch('krbcontext.context.krbV.CCache.init_creds_keytab')
def test_KRB5CCNAME_is_restored_after_init(init_creds_keytab, init, get_tgt_time):
    get_tgt_time.return_value = CredentialTime(authtime=None,
                                               starttime=None,
                                               endtime=datetime.now() - timedelta(minutes=5),
                                               renew_till=None)

    original_krb5ccname = '/tmp/my_krb5_cc'
    with patch.dict(os.environ, {'KRB5CCNAME': original_krb5ccname}, clear=False):
        with kctx.krbContext(using_keytab=True,
                             principal='HTTP/localhost@PYPI.PYTHON.COM',
                             keytab_file='/etc/httpd/conf/httpd.keytab',
                             ccache_file='/tmp/krb5cc_pid_appname'):
            assert '/tmp/krb5cc_pid_appname' == os.environ['KRB5CCNAME']

        assert original_krb5ccname == os.environ['KRB5CCNAME']


@patch('krbcontext.context.get_tgt_time')
def test_original_KRB5CCNAME_is_not_changed_if_no_need_init(get_tgt_time):
    get_tgt_time.return_value = CredentialTime(authtime=None,
                                               starttime=None,
                                               endtime=datetime.now() + timedelta(minutes=5),
                                               renew_till=None)

    original_krb5ccname = '/tmp/my_krb5_cc'

    with patch.dict(os.environ, {'KRB5CCNAME': original_krb5ccname}, clear=False):
        with kctx.krbContext(using_keytab=True,
                             principal='HTTP/localhost@PYPI.PYTHON.COM',
                             keytab_file='/etc/httpd/conf/httpd.keytab',
                             ccache_file='/tmp/krb5cc_pid_appname'):
            assert original_krb5ccname == os.environ['KRB5CCNAME']

        # Ensure original KRB5CCNAME is not changed always.
        assert original_krb5ccname == os.environ['KRB5CCNAME']


@patch('krbcontext.context.get_tgt_time')
@patch('krbcontext.context.krbV.CCache.init')
@patch('krbcontext.context.krbV.CCache.init_creds_keytab')
def test_KRB5CCNAME_is_cleared_after_init(init_creds_keytab, init, get_tgt_time):
    get_tgt_time.return_value = CredentialTime(authtime=None,
                                               starttime=None,
                                               endtime=datetime.now() - timedelta(minutes=5),
                                               renew_till=None)

    with patch.dict(os.environ, {'fake_var': '1'}, clear=True):
        with kctx.krbContext(using_keytab=True,
                             principal='HTTP/localhost@PYPI.PYTHON.COM',
                             keytab_file='/etc/httpd/conf/httpd.keytab',
                             ccache_file='/tmp/krb5cc_pid_appname'):
            assert '/tmp/krb5cc_pid_appname' == os.environ['KRB5CCNAME']

        assert 'KRB5CCNAME' not in os.environ


@patch('krbcontext.context.get_tgt_time')
def test_KRB5CCNAME_is_not_set_if_no_need_init(get_tgt_time):
    get_tgt_time.return_value = CredentialTime(authtime=None,
                                               starttime=None,
                                               endtime=datetime.now() + timedelta(minutes=5),
                                               renew_till=None)
    with patch.dict(os.environ, {'fake_var': '1'}, clear=True):
        with kctx.krbContext(using_keytab=True,
                             principal='HTTP/localhost@PYPI.PYTHON.COM',
                             keytab_file='/etc/httpd/conf/httpd.keytab',
                             ccache_file='/tmp/krb5cc_pid_appname'):
            assert 'KRB5CCNAME' not in os.environ

        # Ensure original KRB5CCNAME is not set always.
        assert 'KRB5CCNAME' not in os.environ
