Release Notes
=============

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
