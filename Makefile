SPEC=python-krbcontext.spec
DIST_DIR=$(realpath dist)

doc:
	@cd docs && make html

sdist:
	@test -e dist && rm -rf dist
	@python setup.py sdist

srpm: sdist
	@rpmbuild \
		--define '_sourcedir $(DIST_DIR)' \
		--define '_srcrpmdir $(DIST_DIR)' \
		-bs ${SPEC}

rpm: srpm
	@rpmbuild \
		--define '_sourcedir $(DIST_DIR)' \
		--define '_rpmdir $(DIST_DIR)' \
		-ba ${SPEC}

check:
	@tox

distcheck: doc rpm

release: distcheck
	@sh -e scripts/make_release.sh
	@echo "Release files are in release directory."
	@echo "Remember to commit local changes to version and changelog!"
.PHONY: release