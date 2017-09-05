Release Notes
=============

0.8 (2017-09-05)
----------------

SPEC file passes package review in Fedora and ``python-krbcontext`` is now a
new Fedora package. SPEC file is updated according to review feedback from
Fedora packager. From this update, ``python-krbcontext`` RPMs will be built for
current supported Fedora releases as well as ``epel7``.

Use ``__future__.absolute_import`` in ``krbcontext.__init__``.

New script for publishing documentation.

0.7 (2017-08-30)
----------------

Enhance scripts for making new release, publishing packages to PyPI, and
building RPMs in Fedora Copr.

Fix a bug in ``init_with_keytab`` that is ``client_keytab`` is not used
correctly. And also fix tests to use ``assert_has_calls`` correctly.

0.6 (2017-08-27)
----------------

This is a quick and small release after version ``0.5`` by fixing a bug of
reading package distribution metadata.

0.5 (2017-08-27)
----------------

Add new target ``distcheck`` into ``Makefile``. This is used for checking
whether there is any problems that would block making a new release.

Add script to make it super easy to prepare a new release, just run ``make
release`` and all artifacts will be created properly and placed in a dedicated
directory named ``release`` at the root directory of project.

0.4 (2017-08-26)
----------------

Migrate to ``python-gssapi``. ``python-krbV`` is no longer used.

``krbcontext`` is compatible with Python 3.

0.3.3 (legacy)
--------------

``0.3.3`` is a legacy version, any new programs should use versions ``> 0.3.3``.
