ctags:
	@rm -rf tags
	@ctags -R --languages=Python --python-kinds=-im -f tags krbcontext/ test/

sdist:
	@python setup.py sdist

rpm: sdist
	@rpmbuild -D '_sourcedir $(realpath dist)' -ba python-krbcontext.spec

check:
	@flake8 krbcontext/ test/
	@python setup.py test
