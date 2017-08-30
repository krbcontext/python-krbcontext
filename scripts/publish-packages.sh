#!/bin/bash

cd "$(dirname $(realpath $0))/../"

RELEASE_DIR="$(realpath release)"
SPEC=python-krbcontext.spec

name=$(python -c "import ConfigParser; cfg=ConfigParser.RawConfigParser(); cfg.read('setup.cfg'); print(cfg.get('package', 'name'))")
rel_ver=$(python -c "import ConfigParser; cfg=ConfigParser.RawConfigParser(); cfg.read('setup.cfg'); print(cfg.get('package', 'version'))")

twine upload -u tkdchen "${RELEASE_DIR}/${name}-${rel_ver}.tar.gz"

srpm_nvr=$(rpm -q --qf "%{NVR}\n" --specfile ${SPEC} | head -n 1)
copr-cli --config ~/.config/copr-fedora build cqi/python-krbcontext "${RELEASE_DIR}/${srpm_nvr}.src.rpm"
