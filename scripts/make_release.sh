#!/bin/bash

# TODO: rerunable without checkout changelog and version changes

release_dir=release
test -e ${release_dir} || mkdir ${release_dir}

specfile=python-krbcontext.spec

name=$(python -c "import krbcontext; print(krbcontext.__name__)")
rel_ver=$(python -c "import krbcontext; print(float(krbcontext.__version__) + 0.1)")
rel_date=$(date --rfc-3339='date')
changelog_items=$(git log --format="- %s (%an)" HEAD...$(git describe --tags --abbrev=0))

# Bump version
function bump_version
{
    sed -i "s/__version__ = '[0-9]\+.[0-9]\+'/__version__ = '${rel_ver}'/" ${name}/__init__.py
}

function update_changelog_rst
{
    changelog_head="${rel_ver} (${rel_date})"
    sep_line=$(python -c "print('-' * len('${changelog_head}'))")
    changelog_head="${changelog_head}
${sep_line}"

    echo "${changelog_head}

${changelog_items}
" | sed -i "3r/dev/stdin" CHANGELOG.rst
}

function update_spec_changelog
{
    local -r name=$(git config --get user.name)
    local -r email=$(git config --get user.email)
    echo "${changelog_items}" > .release-changelog

    rpmdev-bumpspec -n ${rel_ver} -f .release-changelog \
        -u "${name} <${email}>" ${specfile}

    rm .release-changelog
}

function make_release
{
    cp dist/${name}-${rel_ver}.tar.gz ${release_dir}

    local -r srpm_nvr=$(rpm -q --qf "%{NVR}\n" --specfile ${specfile} | head -n 1)
    cp dist/${srpm_nvr}.src.rpm ${release_dir}

    rpm -q --qf "%{NVRA} %{ARCH}\n" --specfile ${specfile} \
        | tail -n 2 \
        | while read -r rpm_nvra arch; do
            cp dist/${arch}/${rpm_nvra}.rpm ${release_dir}
        done
}

bump_version
update_changelog_rst
update_spec_changelog
make rpm doc
make_release
