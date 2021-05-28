Using krbcontext
================

``krbcontext`` provides a Kerberos context that you can put code inside, which
requires a valid ticket in credential cache.

``krbcontext`` is able to initialize credential cache automatically on behalf
of you according to the options you specify. It can initialize with keytab or a
regular user's Kerberos name and password.

You can use ``krbcontext`` as a context manager with ``with`` statement, or
call API directly to check credential cache and even initialize by yourself.  

Lazy Initialization
-------------------

Current version of ``krbcontext`` is able to detect whether specified cache is
a valid credential cache file and contains valid and non-expired ticket. So,
only initializes credential cache when it is necessary.

Thread-safe
-----------

``krbcontext`` manages its own threading lock, and it is acquired when entering
context and gets released when exit. It is recommended that you just put the
necessary code, which requires a valid Kerberos ticket, inside context.

Dependencies
------------

``krbcontext`` requires python-gssapi_.

.. _python-gssapi: https://github.com/pythongssapi/python-gssapi

Installation
------------

Inside a virtual environment::

    python3 -m venv myproject
    . myproject/bin/activate
    python3 -m pip install krbcontext

Or, get it from Fedora repositories::

    dnf install python3-krbcontext

Usage
-----

For details of API, please refer to API_. Here are some use cases.

.. _API: api.html

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

This is the most simplest way, which uses default values. It gets current
effective user name, and get ticket and store it into default credential cache.

You can specify specific prinicpal or cache file explicitly.

::

    with krbContext(principal='qcxhome@EXAMPLE.COM',
                    ccache_file='/tmp/krb5cc_my'):
        pass

    with krbContext(principal='qcxhome',
                    ccache_file='/tmp/my_cc'):
        pass

Using service Keytab
~~~~~~~~~~~~~~~~~~~~

::

    with krbContext(using_keytab=True,
                    principal='HTTP/localhost@EXAMPLE.COM'):
        pass

``principal`` must be specified when initialize with keytab. In this example,
``keytab_file`` is omitted, that means to use default keytab file.

::

    with krbContext(using_keytab=True,
                    principal='HTTP/localhost@EXAMPLE.COM',
                    keytab_file='/etc/httpd/conf/httpd.keytab',
                    ccache_file='/tmp/krb5cc_pid_appname'):
        pass

Alternatively, following example shows to ask ``krbContext`` to initialize a
given credential cache file from specified keytab file. This is a general use
case in a service that calls a third-party service's API, which needs to be
authenticated by Kerberos GSSAPI mechanism.


Backward Compatibility
----------------------

``krbcontext`` is deprecated and will be removed in future version. New code
should use ``krbContext`` instead.
