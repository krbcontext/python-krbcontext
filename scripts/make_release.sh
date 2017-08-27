#!/bin/bash

# TODO: rerunable without checkout changelog and version changes

cd $(dirname $(realpath $0))/..

release_dir=release
test -e ${release_dir} || mkdir ${release_dir}

specfile=python-krbcontext.spec

name=$(python -c "import ConfigParser; cfg=ConfigParser.RawConfigParser(); cfg.read('setup.cfg'); print(cfg.get('package', 'name'))")
rel_ver=$(python -c "import ConfigParser; cfg=ConfigParser.RawConfigParser(); cfg.read('setup.cfg'); print(float(cfg.get('package', 'version'))+0.1)")
rel_date=$(date --rfc-3339='date')
changelog_items=$(git log --format="- %s (%an)" HEAD...$(git describe --tags --abbrev=0))

function bump_version
{
    sed -i "s/^version = [0-9]\+.[0-9]\+$/version = ${rel_ver}/" setup.cfg
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

function gather_release_artifacts
{
    cp dist/${name}-${rel_ver}.tar.gz ${release_dir}

    local -r srpm_nvr=$(rpm -q --qf "%{NVR}\n" --specfile ${specfile} | head -n 1)
    cp dist/${srpm_nvr}.src.rpm ${release_dir}

    rpm -q --qf "%{NVRA} %{ARCH}\n" --specfile ${specfile} \
        | tail -n 2 \
        | while read -r rpm_nvra arch; do
            cp dist/${arch}/${rpm_nvra}.rpm ${release_dir}
        done

    cp -r docs/build/html/ ${release_dir}/docs
}

bump_version
update_changelog_rst
update_spec_changelog
make rpm doc
gather_release_artifacts