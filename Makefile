sdist:
	@test -e dist && rm -rf dist
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

doc:
	@cd docs && make html

distcheck: doc rpm
