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


define get_cur_rel_ver
$(shell grep "^version = [0-9]\+\.[0-9]\+" setup.cfg | cut -d' ' -f3)
endef

release: distcheck
	@sh -e scripts/make_release.sh
	@echo
	@echo "Release files are in release directory."
	@echo "Remember to commit local changes to version and changelog!"
	@echo
	@echo "Next steps:"
	@echo "git commit -s -m \"$(call get_cur_rel_ver) Release\""
	@echo "git tag -m \"$(call get_cur_rel_ver) Release\" v$(call get_cur_rel_ver)"
	@echo "twine-3 upload -u tkdchen release/krbcontext-$(call get_cur_rel_ver).tar.gz"
	@echo "Push documentation to tkdchen.github.io"
.PHONY: release