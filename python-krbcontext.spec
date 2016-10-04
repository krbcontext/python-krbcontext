%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print(get_python_lib())")}

%define src_name krbcontext
%define version 0.3.3
%define release 1

Summary: A Kerberos context manager
Name: python-%{src_name}
Version: %{version}
Release: %{release}%{?dist}
Source0: http://pypi.python.org/packages/source/k/krbcontext/%{src_name}-%{version}.tar.gz
License: GPLv3
Group: Development/Libraries
Url: https://github.com/tkdchen/python-krbcontext
BuildArch: noarch

BuildRequires: python-setuptools

Requires: python-krbV

%description
krbcontext does the initialization of credential cache (ticket file) in a
kerberos-related context. It provides a context manager that allows developers
to put codes inside, which needs a Kerberos environment.

As a general step before invoking any Kerberos commands and APIs, you should
configure your Kerberos environment in file /etc/krb5.conf properly.

You can use krbcontext with a regular Kerberos user or a service Keytab
file. When you work as a regular user, krbcontext prompts you to enter
password of your Kerberos account. Whatever in which way, it accepts a set of
default values and specified values.

There are several concepts you must know before using krbcontext, principal
of user and service, service Keytab file, and credential cache (ticket
file). Therefore, the arguments passed to krbcontext are mapped to these
concepts.

%prep
%setup -q -n %{src_name}-%{version}

%build
%{__python} setup.py build

%install
%{__python} setup.py install -O1 --root=$RPM_BUILD_ROOT

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(-,root,root)
%doc README.rst CHANGES LICENSE
%{python_sitelib}/krbcontext/
%{python_sitelib}/krbcontext-%{version}-*.egg-info

%changelog

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
