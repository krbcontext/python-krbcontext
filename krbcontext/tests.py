# -*- coding: utf-8 -*-

import os
import subprocess
import unittest
import krbV

import tests_config as config

from context import get_login
from context import init_ccache_as_regular_user
from context import init_ccache_with_keytab
from context import krbcontext

class KlistResult(object):
    ticket_cache = None
    default_principal = None

def parse_klist_result(ccache_file):
    ''' Parse klist result to extract kerberos information '''

    klist_proc = subprocess.Popen(('klist -c %s' % ccache_file).split(),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout_data, stderr_data = klist_proc.communicate()

    if klist_proc.returncode > 0:
        return None

    from cStringIO import StringIO
    inbuf = StringIO(stdout_data)
    result = KlistResult()
    for line in inbuf:
        line = line.strip('\r\n')
        if line.startswith('Ticket cache: '):
            result.ticket_cache = line.replace('Ticket cache: ', '')
        if line.startswith('Default principal: '):
            result.default_principal = line.replace('Default principal: ', '')
    inbuf.close()
    return result

# TODO: test configuration for testing is a good idea.
class TestBase(unittest.TestCase):

    def setUp(self):
        self.default_ccache_file = '/tmp/krb5cc_%d' % os.getuid()
        self.default_ccache_file_bak = self.default_ccache_file + '.bak'

        if os.path.exists(self.default_ccache_file):
            os.rename(self.default_ccache_file, self.default_ccache_file_bak)

    def tearDown(self):
        if os.path.exists(self.default_ccache_file_bak):
            os.rename(self.default_ccache_file_bak, self.default_ccache_file)

    def test_configuration(self):
        pass

class TestInitCCacheAsRegularUser(TestBase):
    ''' Test case for initializing credential cache as regular user '''

    def test_init_with_defaults(self):
        ''' initializing with all default values '''

        ccache_file = init_ccache_as_regular_user()

        self.assertEqual(ccache_file, self.default_ccache_file,
            'The newly generated credential cache file is not the default one.')

        result = parse_klist_result(ccache_file)
        self.assertEqual(result.ticket_cache, 'FILE:%s' % self.default_ccache_file)
        self.assertEqual(result.default_principal.split('@')[0], get_login())

    def test_init_with_specified_arguments(self):
        ''' Do not use default values '''

        ccache_file = init_ccache_as_regular_user(
           principal=config.user_principal,
           ccache_file=config.user_ccache_file)
        self.assertEqual(ccache_file, config.user_ccache_file,
            'The returned ccache_file does not equal the one passed to method.')

        result = parse_klist_result(ccache_file)
        self.assertEqual(result.ticket_cache, 'FILE:%s' % config.user_ccache_file)
        self.assertEqual(result.default_principal, config.user_principal)

class TestInitCCacheWithKeytab(TestBase):
    '''Test case for initializing credential cache with keytab

    Developer must own a valid keytab file and the service principal
    before testing. Of course, you are developing a Kerberos application
    and you should get them from the system administrator.
    '''

    def test_init_with_default_ccache(self):
        self.assert_(os.path.exists('/etc/krb5.keytab'),
            'Default keytab does not exist.')

        ccache_file = init_ccache_with_keytab(
            principal=config.service_principal)

        self.assertEqual(ccache_file, self.default_ccache_file)

        result = parse_klist_result(ccache_file)
        self.assertEqual(result.ticket_cache, 'FILE:%s' % self.default_ccache_file)
        self.assertEqual(result.default_principal, config.service_principal)

    def test_init_with_specified_arguments(self):

        ccache_file = init_ccache_with_keytab(
            principal=config.service_principal,
            keytab_file=config.user_keytab_file,
            ccache_file=config.user_ccache_file)

        result = parse_klist_result(ccache_file)
        self.assertEqual(result.ticket_cache, 'FILE:%s' % config.user_ccache_file)
        self.assertEqual(result.default_principal, config.service_principal)

class Testkrbcontext(unittest.TestCase):
    ''' Test case for krbcontext '''

    def setUp(self):
        self.origin_ccache_file = os.getenv('KRB5CCNAME')

    def test_not_use_keytab(self):
        with krbcontext():
            self.assertNotEqual(os.getenv('KRB5CCNAME'), None)
            ccache_file = os.getenv('KRB5CCNAME')
            self.assert_(os.path.exists(ccache_file))

            proc = subprocess.Popen(('klist -c %s' % ccache_file).split(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            returncode = proc.wait()
            self.assertEqual(0, returncode)

        self.assertEqual(self.origin_ccache_file, os.getenv('KRB5CCNAME'),
            'The original KRB5CCNAME\'s value does not restored.')

        with krbcontext(
            principal=config.user_principal,
            ccache_file=config.user_ccache_file):

            ccache_file = os.getenv('KRB5CCNAME')
            ccache = krbV.CCache(ccache_file)
            try:
                princ = ccache.principal()
            except krbV.Krb5Error, err:
                self.fail(err.args[1])
            self.assertEqual(princ.name, config.user_principal)

    def test_using_keytab(self):
        with krbcontext(using_keytab=True, principal=config.service_principal):
            self.assertNotEqual(os.getenv('KRB5CCNAME'), None)
            ccache_file = os.getenv('KRB5CCNAME')
            self.assert_(os.path.exists(ccache_file))

            proc = subprocess.Popen(('klist -c %s' % ccache_file).split(),
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            returncode = proc.wait()
            self.assertEqual(0, returncode)

        self.assertEqual(self.origin_ccache_file, os.getenv('KRB5CCNAME'),
            'The original KRB5CCNAME\'s value does not restored.')

        with krbcontext(using_keytab=True,
                        principal=config.service_principal,
                        keytab_file=config.user_keytab_file,
                        ccache_file=config.user_ccache_file):

            ccache_file = os.getenv('KRB5CCNAME')
            ccache = krbV.CCache(ccache_file)
            try:
                princ = ccache.principal()
            except krbV.Krb5Error, err:
                self.fail(err.args[1])
            self.assertEqual(princ.name, config.service_principal)

if __name__ == '__main__':
    unittest.main()
