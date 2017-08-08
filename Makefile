sdist:
	@python setup.py sdist

srpm: sdist
	@rpmbuild \
		--define '_sourcedir $(realpath dist)' \
		--define '_srcrpmdir $(realpath dist)' -bs python-krbcontext.spec

rpm: srpm
	@rpmbuild \
		--define '_sourcedir $(realpath dist)' \
		--define '_rpmdir $(realpath dist)' -ba python-krbcontext.spec

check:
	@tox
