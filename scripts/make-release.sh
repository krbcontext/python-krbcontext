#!/bin/bash

# This script requires a virtual environment with requirements installed.

script_dir="$(dirname $(realpath "$0"))"

. "$script_dir/util.sh"

cd "$script_dir/.."

rel_date=$(date --rfc-3339='date')
changelog_items=$(git log --format="- %s (%an)" HEAD..."$(git describe --tags --abbrev=0)")

function update_changelog_rst
{
    local -r changelog_head="${package_rel_ver} (${rel_date})"
    local -r sep_line=$(python -c "print('-' * len('${changelog_head}'))")
    echo "${changelog_head}
${sep_line}

${changelog_items}
" | sed -i "3r/dev/stdin" CHANGELOG.rst
}

# Bump version
sed -i "s/^version = [0-9]\+.[0-9]\+$/version = ${package_rel_ver}/" setup.cfg
update_changelog_rst
make doc
python3 setup.py sdist
