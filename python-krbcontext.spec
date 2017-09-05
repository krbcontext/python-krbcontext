%global src_name krbcontext

Summary: A Kerberos context manager
Name: python-%{src_name}
Version: 0.8
Release: 1%{?dist}
Source0: https://files.pythonhosted.org/packages/source/k/%{src_name}/%{src_name}-%{version}.tar.gz
License: GPLv3
Url: https://github.com/krbcontext/python-krbcontext
BuildArch: noarch

%description
krbcontext provides a Kerberos context that you can put code inside, which
requires a valid ticket in credential cache.

krbcontext is able to initialize credential cache automatically on behalf
of you according to the options you specify. It can initialize with keytab or a
regular user's Kerberos name and password.

You can use krbcontext as a context manager with with statement, or
call API directly to check credential cache and even initialize by yourself.

# Build Python 2 package for Fedora and only for RHEL7

%package -n python2-%{src_name}
Summary: A Kerberos context manager

%if 0%{?rhel}
BuildRequires: python-devel
BuildRequires: python-setuptools
# For running test
BuildRequires: python-flake8
BuildRequires: pytest
# BuildRequires: python2-pytest-cov
%else
BuildRequires: python2-devel
BuildRequires: python2-setuptools
# For running test
BuildRequires: python2-flake8
BuildRequires: python2-pytest
# BuildRequires: python-pytest-cov
%endif

BuildRequires: python-gssapi
BuildRequires: python2-mock

Requires: python-gssapi
%{?python_provide:%python_provide python2-%{src_name}}

%description -n python2-%{src_name}
krbcontext provides a Kerberos context that you can put code inside, which
requires a valid ticket in credential cache.

krbcontext is able to initialize credential cache automatically on behalf
of you according to the options you specify. It can initialize with keytab or a
regular user's Kerberos name and password.

You can use krbcontext as a context manager with with statement, or
call API directly to check credential cache and even initialize by yourself.

# Only build Python 3 package for Fedora

%if 0%{?fedora}
%package -n python3-%{src_name}
Summary: A Kerberos context manager

BuildRequires: python3-setuptools
BuildRequires: python3-devel
BuildRequires: python3-gssapi
# For running test
BuildRequires: python3-flake8
BuildRequires: python3-mock
BuildRequires: python3-pytest
#BuildRequires: python3-pytest-cov

Requires: python3-gssapi
%{?python_provide:%python_provide python%{python3_pkgversion}-%{src_name}}

%description -n python3-%{src_name}
krbcontext provides a Kerberos context that you can put code inside, which
requires a valid ticket in credential cache.

krbcontext is able to initialize credential cache automatically on behalf
of you according to the options you specify. It can initialize with keytab or a
regular user's Kerberos name and password.

You can use krbcontext as a context manager with with statement, or
call API directly to check credential cache and even initialize by yourself.

%endif
# end of Python 3 package

%prep
%setup -q -n %{src_name}-%{version}

%build
%py2_build

%if 0%{?fedora}
%py3_build
%endif

%install
%py2_install

%if 0%{?fedora}
%py3_install
%endif

%check
PYTHONPATH=. py.test-%{python2_version} test/

%if 0%{?fedora}
PYTHONPATH=. py.test-%{python3_version} test/
%endif

%files -n python2-%{src_name}
%doc README.rst CHANGELOG.rst docs/
%license LICENSE
%{python2_sitelib}/krbcontext/
%{python2_sitelib}/krbcontext-%{version}-*.egg-info

%if 0%{?fedora}
%files -n python3-%{src_name}
%doc README.rst CHANGELOG.rst docs/
%license LICENSE
%{python3_sitelib}/krbcontext/
%{python3_sitelib}/krbcontext-%{version}-*.egg-info
%endif

%changelog
* Tue Sep 05 2017 Chenxiong Qi <qcxhome@gmail.com> - 0.8-1
- Fix SPEC (Chenxiong Qi)
- Use __future__.absolute_import (Chenxiong Qi)
- Fix and enhance maintanence scripts (Chenxiong Qi)

* Wed Aug 30 2017 Chenxiong Qi <qcxhome@gmail.com> - 0.7-1
- Remove unused meta info (Chenxiong Qi)
- Fix init_with_keytab and tests (Chenxiong Qi)
- Add script for publishing packages (Chenxiong Qi)
- Refine make release script (Chenxiong Qi)

* Sun Aug 27 2017 Chenxiong Qi <qcxhome@gmail.com> - 0.6-1
- Fix reading package info (Chenxiong Qi)

* Sat Aug 26 2017 Chenxiong Qi <qcxhome@gmail.com> - 0.5-1
- Add script for making release (Chenxiong Qi)
- Add distcheck to Makefile (Chenxiong Qi)
- Refine doc settings (Chenxiong Qi)
- Easy to set project info (Chenxiong Qi)
- Bump version to 4.0 in doc (Chenxiong Qi)

* Sat Aug 26 2017 Chenxiong Qi <qcxhome@gmail.com> - 0.4-1
- Migrate to python-gssapi
- Compatible with Python 3

* Thu Mar 13 2014 Chenxiong Qi <cqi@redhat.com> - 0.3.3-1
- Change README.txt to README.rst
- Fix: logic error of KRB5CCNAME maintenance during initialization
- Fix testcase of getting default credential cache

* Fri Jan 18 2013 Chenxiong Qi <cqi@redhat.com> - 0.3.1-1
- Thread-safe credentials cache initialization

* Thu Jan 10 2013 Chenxiong Qi <cqi@redhat.com> - 0.3.0-1
- Lazy initialization of credential cache.
- Refactor all code
- Rewrite all unittest
- Improve SPEC
- Improve configuration of Python package distribution
- Update documentation

* Mon Jul 30 2012 Chenxiong Qi <cqi@redhat.com> - 0.2-1
- Initial package
