#!/bin/bash

# `make doc' is required to run in advance.

cd "$(dirname $(realpath $0))/../"

author=$(python -c "import ConfigParser; cfg=ConfigParser.RawConfigParser(); cfg.read('setup.cfg'); print(cfg.get('package', 'author'))")
email=$(python -c "import ConfigParser; cfg=ConfigParser.RawConfigParser(); cfg.read('setup.cfg'); print(cfg.get('package', 'email'))")
rel_ver=$(python -c "import ConfigParser; cfg=ConfigParser.RawConfigParser(); cfg.read('setup.cfg'); print(cfg.get('package', 'version'))")

RELEASE_DIR="$(realpath release)"
mkdir ${RELEASE_DIR}/docs
cp -r docs/build/html/* ${RELEASE_DIR}/docs/

# All rest things happen in release directory.

cd "${RELEASE_DIR}"

git clone git@github.com:krbcontext/krbcontext.github.io.git

cp -r docs/* krbcontext.github.io/

cd krbcontext.github.io/
git config user.name "${author}"
git config user.email "${email}"

git add *
git commit -s -m "Update doc for ${rel_ver} release"
git push origin HEAD:master
