#!/bin/bash

script_dir="$(dirname $(realpath "$0"))"
pypi_username=tkdchen

. "$script_dir/util.sh"

cd "$script_dir/.."

tarball_file="dist/${package_name}-${package_rel_ver}.tar.gz"

[[ -e "$tarball_file" ]] || python setup.py sdist
twine upload -u "$pypi_username" "$tarball_file"
