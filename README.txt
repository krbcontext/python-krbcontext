Using krbcontext
================

krbcontext does the initialization of credential cache (ticket file) in a
kerberos-related context. It provides a context manager that allows
developers to put codes, which needs kerberos environment, into a kerberos context.

One important thing is that you should configure /etc/krb5.conf correctly before
doing anything with Kerberos.

krbcontext will initialize the credential cache when be invoked each time.

You can use krbcontext with a regular Kerberos user or a service Keytab file.
When you work as a regular user, krbcontext prompts you to enter password
of your Kerberos account. Whatever in which way, krbcontext accepts a set of
default values and specified values.

There are several concept you must know before using krbcontext, principal of user
and service, service Keytab file, and credential cache (ticket file). Therefore,
the arguments passed to krbcontext are mapped to these concepts.

Lazy initialization
-------------------

Before running client's code, krbcontext checks credential krbtgt/REALM@REALM in
credentials cache locally to see whether it is necessary it expires.

Thread-safe
-----------

If your want krbcontext to initialize credential in Kerberos standard
credenticial cache, or pass a file name to argument ``ccache_file`` explicitly,
krbcontext is thread-safe. However, it is still suggestion that you pass
credentials cache file name for each thread individually.

Dependencies
------------

krbcontext depends on python-krbV. This is a Python extension module for Kerberos 5.
It is hosted in fedorahosted.org, you can follow this URL to get more details.
https://fedorahosted.org/python-krbV/

If you choose to install krbcontext using the RPM distribution, the dependency will
be solved automatically. On the other hand, if easy_install or pip is used, it is
necessary to run yum or build from source to install python-krbV first.

Usage
-----

Arguments
~~~~~~~~~

using_keytab
    Specify whether using the service Keytab to initialize the credential cache.
    Default is False.

kwargs
    Specify necessary argument for initializing credential cache. You can pass:

    * principal: user principal or service principal
    * keytab_file: absolute path of Keytab file
    * ccache_file: absolute path of credential cache

Basic
~~~~~

krbcontext can be used as a normal context manager simply.

::

    with krbcontext():
        # your code here
        pass

As a regular user
~~~~~~~~~~~~~~~~~

::

    with krbcontext():
        pass

This is the most simplest way. It uses default values. It gets current effective
user name rather than login name, and initialize the default credential cache,
``/tmp/krb5cc_xxx``, where xxx is the current user ID returned by os.getuid method.

Specifying custom values

::

    with krbcontext(principal='qcxhome@PYPI.PYTHON.COM',
                    ccache_file='/tmp/krb5cc_my'):
        pass

    with krbcontext(principal='qcxhome',
                    ccache_file='/tmp/krb5cc_my'):
        pass

Using service Keytab
~~~~~~~~~~~~~~~~~~~~

::

    with krbcontext(using_keytab=True,
                    principal='HTTP/localhost@PYPI.PYTHON.COM'):
        pass

You can also use default values here except the using_keytab and principal.
The default Keytab locates ``/etc/krb5.keytab``, and default credential cache
locates ``/tmp/krb5cc_xxx``, like above.

::

    with krbcontext(using_keytab=True,
                    principal='HTTP/localhost@PYPI.PYTHON.COM'):
                    keytab_file='/etc/httpd/conf/httpd.keytab',
                    ccache_file='/tmp/krb5cc_pid_appname'):
        pass

If you have another Keytab that is be elsewhere and a credential cache for
special purpose, you may pass the keytab_file and ccache_file.
