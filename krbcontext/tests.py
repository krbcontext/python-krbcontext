# -*- coding: utf-8 -*-

import context as kctx

from context import ENV_KRB5CCNAME
from context import init_ccache_with_keytab
from context import is_initialize_ccache_necessary
from context import KRB5InitError
from context import krbcontext
from utils import get_tgt_time

import krbV
import os
import tests_config as config
import time
import textwrap
import unittest


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


class OriginalKRB5CCNAMESafeMixin(object):
    '''Ensure the original system's KRB5CCNAME is safe'''

    def protect_KRB5CCNAME(self):
        self._original_krb5ccname_env = os.getenv(ENV_KRB5CCNAME)

    def recovery_KRB5CCNAME(self):
        has_krb5ccname_in_process = self._original_krb5ccname_env is not None
        if has_krb5ccname_in_process:
            os.environ[ENV_KRB5CCNAME] = self._original_krb5ccname_env
        else:
            krb5ccname_set_in_testcases = ENV_KRB5CCNAME in os.environ
            if krb5ccname_set_in_testcases:
                del os.environ[ENV_KRB5CCNAME]


class CCacheInitializationRequiredTest(unittest.TestCase,
                                       OriginalKRB5CCNAMESafeMixin):
    def setUp(self):
        self.protect_KRB5CCNAME()
        os.environ[ENV_KRB5CCNAME] = config.user_ccache_file

    def tearDown(self):
        self.recovery_KRB5CCNAME()

    def testCCacheFileNotFound(self):
        os.system('kdestroy -c %s 2>/dev/null' % config.user_ccache_file)
        context = krbV.default_context()
        ccache = krbV.CCache(config.user_ccache_file, context=context)
        principal = krbV.Principal(config.service_principal, context=context)
        result = is_initialize_ccache_necessary(context, ccache, principal)
        self.assert_(result)

        if config.run_under_user_principal:
            context = krbV.default_context()
            ccache = krbV.CCache(config.user_ccache_file, context=context)
            principal = krbV.Principal(config.user_principal, context=context)
            result = is_initialize_ccache_necessary(context, ccache, principal)
            self.assert_(result)

    def testCCacheFileBadFormat(self):
        os.system('echo > %s' % config.user_ccache_file)
        context = krbV.default_context()
        ccache = krbV.CCache(config.user_ccache_file, context=context)
        principal = krbV.Principal(config.service_principal, context=context)
        result = is_initialize_ccache_necessary(context, ccache, principal)
        self.assert_(result)

        if config.run_under_user_principal:
            context = krbV.default_context()
            ccache = krbV.CCache(config.user_ccache_file, context=context)
            principal = krbV.Principal(config.user_principal, context=context)
            result = is_initialize_ccache_necessary(context, ccache, principal)
            self.assert_(result)

    def testInitCCacheIsNecessary(self):
        ''' Sleep several seconds after initializing credentials cache so that
            it expires.
        '''
        if config.run_under_user_principal:
            init_user_ccache(lifetime='3s')
            time.sleep(5)
            context = krbV.default_context()
            ccache = krbV.CCache(config.user_ccache_file, context=context)
            principal = krbV.Principal(config.user_principal, context=context)
            result = is_initialize_ccache_necessary(context, ccache, principal)
            self.assert_(result)

        init_ccache_using_keytab(lifetime='3s')
        time.sleep(5)
        context = krbV.default_context()
        ccache = krbV.CCache(config.user_ccache_file, context=context)
        principal = krbV.Principal(config.service_principal, context=context)
        result = is_initialize_ccache_necessary(context, ccache, principal)
        self.assert_(result)

    def testInitCCacheIsUnnecessary(self):
        if config.run_under_user_principal:
            init_user_ccache()
            context = krbV.default_context()
            ccache = krbV.CCache(config.user_ccache_file, context=context)
            principal = krbV.Principal(config.user_principal, context=context)
            result = is_initialize_ccache_necessary(context, ccache, principal)
            self.assertFalse(result)

        init_ccache_using_keytab()
        context = krbV.default_context()
        ccache = krbV.CCache(config.user_ccache_file, context=context)
        principal = krbV.Principal(config.service_principal, context=context)
        result = is_initialize_ccache_necessary(context, ccache, principal)
        self.assertFalse(result)


class GetDefaultCCacheTest(unittest.TestCase, OriginalKRB5CCNAMESafeMixin):
    def setUp(self):
        self.context = krbV.default_context()
        self.protect_KRB5CCNAME()

    def tearDown(self):
        self.recovery_KRB5CCNAME()

    def testFromEnvironmentVariable(self):
        os.environ[ENV_KRB5CCNAME] = config.user_ccache_file
        ccache = kctx.get_default_ccache(self.context)
        self.assertEqual(ccache.name, config.user_ccache_file)

    def testFromKerberosDefaultCCacheName(self):
        ccache = kctx.get_default_ccache(self.context)
        ccache_file = ccache.name.lstrip(':')
        default_cc_name = '/run/user/%d/krb5cc' % os.getuid()
        self.assertTrue(ccache_file.startswith(default_cc_name))


class CleanArgumetsUsingKeytabTest(unittest.TestCase):
    def setUp(self):
        self.context = krbV.default_context()
        self.kwargs = {
            'using_keytab': True,
        }

    def testPrincipalNotProvide(self):
        self.assertRaises(NameError, kctx.clean_kwargs,
                          self.context, self.kwargs)

    def testAllDefault(self):
        self.kwargs.update({
            'principal': config.service_principal,
        })
        cleaned_kwargs = kctx.clean_kwargs(self.context, self.kwargs)

        self.assert_('principal' in cleaned_kwargs)
        self.assertEqual(
            cleaned_kwargs['principal'].name,
            config.service_principal,
            'Principal is not cleaned to proper an Principal.')

        self.assert_('ccache' in cleaned_kwargs)
        expected_ccache_file = krb_default_cc_name()
        self.assertEqual(
            cleaned_kwargs['ccache'].name, expected_ccache_file,
            'Cleaned ccache %s does not equal to expected %s.' % (
                cleaned_kwargs['ccache'].name, expected_ccache_file))

        self.assert_('keytab' in cleaned_kwargs)
        kt = cleaned_kwargs['keytab']
        expected_kt_name = krb_default_keytab_name()
        self.assertEqual(kt.name, expected_kt_name,
                         'Default key table should be used if not provide.')

    def testSpecifyAllManually(self):
        self.kwargs.update({
            'principal': config.service_principal,
            'ccache_file': config.user_ccache_file,
            'keytab_file': config.user_keytab_file,
        })

        cleaned_kwargs = kctx.clean_kwargs(self.context, self.kwargs)

        self.assert_('ccache' in cleaned_kwargs)
        self.assertEqual(
            cleaned_kwargs['ccache'].name, config.user_ccache_file,
            'Cleaned ccache %s does not equal to expected %s.' % (
                cleaned_kwargs['ccache'].name, config.user_ccache_file))

        self.assert_('keytab' in cleaned_kwargs)
        kt = cleaned_kwargs['keytab']
        expected_kt_name = config.user_keytab_file
        self.assert_(
            kt.name.endswith(expected_kt_name),
            'Key table %s should contain expected filename %s.' % (
                kt.name, expected_kt_name))


class CleanArgumetsAsRegularUserTest(unittest.TestCase):
    def setUp(self):
        self.context = krbV.default_context()
        self.kwargs = {
            'using_keytab': False,
        }

    def testAllDefault(self):
        cleaned_kwargs = kctx.clean_kwargs(self.context, {})
        self.assert_('using_keytab' in cleaned_kwargs)
        self.assertFalse(cleaned_kwargs['using_keytab'])

        self.assert_('principal' in cleaned_kwargs)
        principal = cleaned_kwargs['principal']
        self.assertEqual(principal.name.split('@')[0], kctx.get_login())

        self.assert_('ccache' in cleaned_kwargs)
        ccache = cleaned_kwargs['ccache']
        self.assertEqual(ccache.name, krb_default_cc_name())

    def testSpecifyAllManually(self):
        self.kwargs.update({
            'principal': config.user_principal,
            'ccache_file': config.user_ccache_file,
        })
        cleaned_kwargs = kctx.clean_kwargs(self.context, self.kwargs)

        self.assert_('principal' in cleaned_kwargs)
        test_user_princ = cleaned_kwargs['principal']
        self.assertEqual(
            test_user_princ.name, config.user_principal,
            'Principal name %s does not equal to expected %s.' % (
                test_user_princ, config.user_principal))

        self.assert_('ccache' in cleaned_kwargs)
        ccache = cleaned_kwargs['ccache']
        self.assertEqual(ccache.name, config.user_ccache_file)


class InitAsRegularUserTest(unittest.TestCase):
    def _setUp(self):
        self.context = krbV.default_context()
        self.principal = krbV.Principal(config.user_principal,
                                        context=self.context)
        self.ccache = krbV.CCache(config.user_ccache_file,
                                  context=self.context)

    def _testInitialization(self):
        cc_name = kctx.init_ccache_as_regular_user(self.principal, self.ccache)
        self.assert_(cc_name.endswith(self.ccache.name))

    def _testInitializationWithWrongArguments(self):
        principal = krbV.Principal('someone@domain.com', context=self.context)
        self.assertRaises(KRB5InitError,
                          kctx.init_ccache_as_regular_user,
                          principal, self.ccache)

    if config.run_under_user_principal:
        setUp = _setUp
        # Add other test case
        testInitialization = _testInitialization
        testInitializationWithWrongArguments = \
            _testInitializationWithWrongArguments


class InitUsingKeytabTest(unittest.TestCase):
    def setUp(self):
        self.context = krbV.default_context()
        self.principal = krbV.Principal(config.service_principal,
                                        context=self.context)
        self.keytab = krbV.Keytab(config.user_keytab_file,
                                  context=self.context)
        self.ccache = krbV.CCache(config.user_ccache_file,
                                  context=self.context)

    def testInitialization(self):
        cc_name = init_ccache_with_keytab(self.principal,
                                          self.keytab,
                                          self.ccache)
        self.assert_(cc_name.endswith(self.ccache.name))


class krbcontextUsingKeytabTest(unittest.TestCase):

    def setUp(self):
        init_ccache_using_keytab(lifetime='3s')

        self.sleep_seconds_for_expiration = 5
        self.kwargs = {
            'using_keytab': True,
            'principal': config.service_principal,
            'keytab_file': config.user_keytab_file,
            'ccache_file': config.user_ccache_file,
        }

    def tearDown(self):
        cmd = 'kdestroy -c %s' % config.user_ccache_file
        os.system(cmd)

    def testInitializeCCacheIsNotRequired(self):
        expected_endtime = get_tgt_time_from_ccache(config.service_principal)
        with krbcontext(**self.kwargs):
            pass
        test_endtime = get_tgt_time_from_ccache(config.service_principal)
        self.assertEqual(test_endtime, expected_endtime)

    def testInitializeCCacheWhenTGTExpires(self):
        endtime_before_init = get_tgt_time_from_ccache(config.service_principal)
        # Sleep for a while to make TGT expired
        time.sleep(self.sleep_seconds_for_expiration)
        with krbcontext(**self.kwargs):
            pass
        test_endtime = get_tgt_time_from_ccache(config.service_principal)
        self.assert_(test_endtime > endtime_before_init)

if __name__ == '__main__':
    help_msg = 'During running test, some test cases will sleep for several ' \
               'minutes in order to stimulate that credential expires.\n\n'

    if config.run_under_user_principal:
        help_msg += 'You have enabled configuration run_under_user_principal.' \
                    ' So, when each time initialize credential cache using a ' \
                    'regular user\'s principal, you will be prompted to enter' \
                    ' password.'

    print '\n'.join(textwrap.wrap(help_msg, 80))

    unittest.main()
