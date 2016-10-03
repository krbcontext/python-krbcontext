Using krbcontext
================

``krbcontext`` does the initialization of credential cache (ticket file) in a
kerberos-related context. It provides a context manager that allows developers
to put codes inside, which needs a Kerberos environment.

As a general step before invoking any Kerberos commands and APIs, you should
configure your Kerberos environment in file ``/etc/krb5.conf`` properly.

You can use ``krbcontext`` with a regular Kerberos user or a service Keytab
file. When you work as a regular user, ``krbcontext`` prompts you to enter
password of your Kerberos account. Whatever in which way, it accepts a set of
default values and specified values.

There are several concepts you must know before using ``krbcontext``, principal
of user and service, service Keytab file, and credential cache (ticket
file). Therefore, the arguments passed to ``krbcontext`` are mapped to these
concepts.

Lazy initialization
-------------------

Before running client's code, ``krbcontext`` checks credential
``krbtgt/REALM@REALM`` in default or specified credential cache to see if it is
necessary to be initialized.

Thread-safe
-----------

If you want krbcontext to initialize credential in Kerberos standard
credenticial cache, or pass a file name to argument ``ccache_file`` explicitly,
krbcontext is thread-safe. However, it is still suggestion that you pass
credentials cache file name for each thread individually.

Dependencies
------------

``krbcontext`` depends on python-krbV_, that is a Python extension module for
Kerberos 5.

If you install ``krbcontext`` using RPM, dependency will be resolved
automatically. If easy_install or pip is used, it is necessary to install
``python-krbV`` manually from software repository. For example,

::

   sudo dnf install python-krbV

As of writing this document, ``python-krbV`` is only available as RPM package
in Fedora, CentOS, and probably RHEL. If you are using non-RPM distributions,
feel free to build it for yourself. Don't be afraid, it should be easy
enough. Please refer to the project's documentation, how to build it is beyond
the scope of this document.

.. _python-krbV: https://fedorahosted.org/python-krbV/

Installation
------------

Using `virtual environment`_ ::

  sudo dnf install python-krbV
  virtualenv --system-site-packages myproject
  . myproject/bin/activate
  pip install python-krbcontext

.. _virtual environment: https://pypi.python.org/pypi/virtualenv/

Usage
-----

Arguments
~~~~~~~~~

using_keytab
    Specify whether using the service Keytab to initialize the credential cache.
    Default is False.

kwargs
    Specify necessary arguments for initializing credential cache. Acceptable
    arguments include:

    * ``principal``: user principal or service principal
    * ``keytab_file``: absolute path of Keytab file
    * ``ccache_file``: absolute path of credential cache

Basic
~~~~~

krbcontext can be used as a normal context manager simply.

::

    with krbContext():
        # your code here
        pass

As a regular user
~~~~~~~~~~~~~~~~~

::

    with krbContext():
        pass

This is the most simplest way. It uses default values. It gets current effective
user name rather than login name, and initialize the default credential cache,
``/tmp/krb5cc_xxx``, where xxx is the current user ID returned by ``os.getuid`` method.

Specifying custom values

::

    with krbContext(principal='qcxhome@EXAMPLE.COM',
                    ccache_file='/tmp/krb5cc_my'):
        pass

    with krbContext(principal='qcxhome',
                    ccache_file='/tmp/krb5cc_my'):
        pass

Using service Keytab
~~~~~~~~~~~~~~~~~~~~

::

    with krbContext(using_keytab=True,
                    principal='HTTP/localhost@EXAMPLE.COM'):
        pass

You can also use default values here except the using_keytab and principal.
The default Keytab locates ``/etc/krb5.keytab``, and default credential cache
locates ``/tmp/krb5cc_xxx``, like above.

::

    with krbContext(using_keytab=True,
                    principal='HTTP/localhost@EXAMPLE.COM',
                    keytab_file='/etc/httpd/conf/httpd.keytab',
                    ccache_file='/tmp/krb5cc_pid_appname'):
        pass

If you have another Keytab that is be elsewhere and a credential cache for
special purpose, you may pass the ``keytab_file`` and ``ccache_file``.

Backward Compatibility
----------------------

``krbcontext`` is deprecated and will be removed in future version. New code
should use ``krbContext`` instead.
