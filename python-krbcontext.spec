%define src_name krbcontext

Summary: A Kerberos context manager
Name: python-%{src_name}
Version: 0.4
Release: 1%{?dist}
Source0: https://files.pythonhosted.org/packages/source/k/%{name}/%{src_name}-%{version}.tar.gz
License: GPLv3
Group: Development/Libraries
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

%package -n python2-%{src_name}
Summary: A Kerberos context manager

BuildRequires: python-devel
BuildRequires: python-setuptools
BuildRequires: python-gssapi
# For running test
BuildRequires: python2-mock
BuildRequires: python-flake8
BuildRequires: python-pytest-cov
BuildRequires: python2-pytest

Requires: python-gssapi

%description -n python2-%{src_name}
krbcontext provides a Kerberos context that you can put code inside, which
requires a valid ticket in credential cache.

krbcontext is able to initialize credential cache automatically on behalf
of you according to the options you specify. It can initialize with keytab or a
regular user's Kerberos name and password.

You can use krbcontext as a context manager with with statement, or
call API directly to check credential cache and even initialize by yourself.

%package -n python3-%{src_name}
Summary: A Kerberos context manager

BuildRequires: python3-setuptools
BuildRequires: python3-devel
BuildRequires: python3-gssapi
# For running test
BuildRequires: python3-flake8
BuildRequires: python3-mock
BuildRequires: python3-pytest
BuildRequires: python3-pytest-cov

Requires: python3-gssapi

%description -n python3-%{src_name}
krbcontext provides a Kerberos context that you can put code inside, which
requires a valid ticket in credential cache.

krbcontext is able to initialize credential cache automatically on behalf
of you according to the options you specify. It can initialize with keytab or a
regular user's Kerberos name and password.

You can use krbcontext as a context manager with with statement, or
call API directly to check credential cache and even initialize by yourself.

%prep
%setup -q -n %{src_name}-%{version}

%build
%py2_build
%py3_build

%install
%py2_install
%py3_install

%check
PYTHONPATH=. py.test test/
PYTHONPATH=. py.test-3 test/

%clean
rm -rf $RPM_BUILD_ROOT

%files -n python2-%{src_name}
%defattr(-,root,root)
%doc README.rst CHANGELOG.rst LICENSE docs/
%{python2_sitelib}/krbcontext/
%{python2_sitelib}/krbcontext-%{version}-*.egg-info

%files -n python3-%{src_name}
%defattr(-,root,root)
%doc README.rst CHANGELOG.rst LICENSE docs/
%{python3_sitelib}/krbcontext/
%{python3_sitelib}/krbcontext-%{version}-*.egg-info

%changelog
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
