# -*- coding: utf-8 -*-

'''Configuration for running test script
'''

# Format of Kerberos v5 user principal: name@REALM
# Example: 'qcxhome@DOMAIN.COM'
user_principal = ''

# Format of Kerberos v5 sevice principal: servicename/hostname@REALM
# Example: HTTP/localhost@DOMAIN.COM
service_principal = ''

# Absolute path of Keytab file
# Typically, for a web site, it can be the following value
user_keytab_file = '/etc/httpd/conf/httpd.keytab'

# Absolute path of credential cache
user_ccache_file = '/tmp/krb5cc_test'
