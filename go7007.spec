#
# TODO:
# - make licensing clear (especially for the firware)
#
# Conditional build:
%bcond_without	dist_kernel	# allow non-distribution kernel
%bcond_without	kernel		# don't build kernel modules
%bcond_without	smp		# don't build SMP module
%bcond_without	userspace	# don't build userspace programs
%bcond_with	verbose		# verbose build (V=1)

%if %{without kernel}
%undefine	with_dist_kernel
%endif

Summary:	Exemplary userspace program for go7007 video capture cards
Summary(pl):	Przyk�adowy program dla kart przechwytywania video go7007
Name:		go7007
Version:	0.9.6
%define		_rel	0.3
Release:	%{_rel}
License:	Public Domain
Group:		Applications/Multimedia
Source0:	http://oss.wischip.com/wis-%{name}-linux-%{version}.tar.bz2
# Source0-md5:	dac06ba7c410ac9ad8a3b2f27a03f7aa
Patch0:		%{name}-hotplug.patch
URL:		http://oss.wischip.com/
%if %{with kernel}
%{?with_dist_kernel:BuildRequires:	kernel-module-build >= 2.6.7}
BuildRequires:	rpmbuild(macros) >= 1.217
%endif
BuildRequires:	linux-libc-headers
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Exemplary userspace program for go7007 video capture cards.

%description -l pl
Przyk�adowy program dla kart przechwytywania video go7007.

%package devel
Summary:	Header files for the go7007 driver
Summary(pl):    Pliki nag��wkowe dla sterownika go7007
Group:          Development/Libraries
Requires:	linux-libc-headers

%description devel
Header files for the go7007 driver.

%description devel -l pl
Pliki nag��wkowe dla sterownika go7007.

%package firmware
Summary:	Firmware for the go7007 driver
Summary(pl):	Firmware dla sterownika go7007
License:	distributable
Group:		System Environment/Kernel
Requires:	fxload

%description firmware
Firmware for the go7007 driver.

%description firmware -l pl
Firmware dla sterownika go7007.

%package -n kernel-extra-go7007
Summary:	Linux driver for go7007
Summary(pl):	Sterownik dla Linuksa do go7007
Release:	%{_rel}@%{_kernel_ver_str}
License:	GPL v2
Group:		Base/Kernel
Requires(post,postun):	/sbin/depmod
%if %{with dist_kernel}
%requires_releq_kernel_up
Requires(postun):	%releq_kernel_up
%endif

%description -n kernel-extra-go7007
This is driver for go7007 for Linux.

This package contains Linux module.

%description -n kernel-extra-go7007 -l pl
Sterownik dla Linuksa do go7007.

Ten pakiet zawiera modu� j�dra Linuksa.

%package -n kernel-smp-extra-go7007
Summary:	Linux SMP driver for go7007
Summary(pl):	Sterownik dla Linuksa SMP do go7007
Release:	%{_rel}@%{_kernel_ver_str}
License:	GPL v2
Group:		Base/Kernel
Requires:	go7007-firmware
Requires(post,postun):	/sbin/depmod
%if %{with dist_kernel}
%requires_releq_kernel_smp
Requires(postun):	%releq_kernel_smp
%endif

%description -n kernel-smp-extra-go7007
This is driver for go7007 for Linux.

This package contains Linux SMP module.

%description -n kernel-smp-extra-go7007 -l pl
Sterownik dla Linuksa do go7007.

Ten pakiet zawiera modu� j�dra Linuksa SMP.

%prep
%setup -q -n wis-%{name}-linux-%{version}
%patch0 -p1

%build

sed 's,@FIRMWARE_DIR@,/lib/firmware,' < hotplug/wis-ezusb.in > hotplug/wis-ezusb

%if %{with userspace}
make -C apps CFLAGS="-I../include"
%endif

%if %{with kernel}
install -d kernel/{ko-up,ko-smp}
# kernel module(s)
for cfg in %{?with_dist_kernel:%{?with_smp:smp} up}%{!?with_dist_kernel:nondist}; do
	if [ ! -r "%{_kernelsrcdir}/config-$cfg" ]; then
		exit 1
	fi
	rm -rf kernel/include/{linux,config,asm}
        rm -f kernel/.config
	install -d kernel/include/{linux,config}
	ln -sf %{_kernelsrcdir}/config-$cfg kernel/.config
	ln -sf %{_kernelsrcdir}/include/linux/autoconf-$cfg.h kernel/include/linux/autoconf.h
	ln -sf %{_kernelsrcdir}/include/asm-%{_target_base_arch} kernel/include/asm
	touch kernel/include/config/MARKER
	
	%{__make} -C %{_kernelsrcdir} clean \
		RCS_FIND_IGNORE="-name '*.ko' -o" \
		M="$PWD/kernel" O="$PWD/kernel" \
		%{?with_verbose:V=1}
	%{__make} -C %{_kernelsrcdir} modules \
		CC="%{__cc}" CPP="%{__cpp}" \
		M="$PWD/kernel" O="$PWD/kernel" \
		%{?with_verbose:V=1}

	mv kernel/*.ko kernel/ko-$cfg
done
%endif

%install
rm -rf $RPM_BUILD_ROOT

install -d $RPM_BUILD_ROOT/lib/firmware/{,ezusb}
install -p firmware/*.bin $RPM_BUILD_ROOT/lib/firmware
install -p firmware/ezusb/*.hex $RPM_BUILD_ROOT/lib/firmware/ezusb

install -d $RPM_BUILD_ROOT%{_sysconfdir}/hotplug/usb
install hotplug/wis-ezusb $RPM_BUILD_ROOT%{_sysconfdir}/hotplug/usb/wis-ezusb
install hotplug/wis.usermap-ezusb $RPM_BUILD_ROOT%{_sysconfdir}/hotplug/usb/wis.usermap

%if %{with userspace}
install -d $RPM_BUILD_ROOT/usr/bin
install apps/gorecord $RPM_BUILD_ROOT/usr/bin
%endif

%if %{with kernel}
install -d $RPM_BUILD_ROOT%{_includedir}/linux
install include/*.h $RPM_BUILD_ROOT%{_includedir}/linux

install -d $RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}{,smp}/extra
cp kernel/ko-%{?with_dist_kernel:up}%{!?with_dist_kernel:nondist}/*.ko \
	$RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}/extra
%if %{with smp} && %{with dist_kernel}
cp kernel/ko-smp/*.ko \
	$RPM_BUILD_ROOT/lib/modules/%{_kernel_ver}smp/extra
%endif
%endif

%clean
rm -rf $RPM_BUILD_ROOT

%post	-n kernel-extra-go7007
%depmod %{_kernel_ver}

%postun	-n kernel-extra-go7007
%depmod %{_kernel_ver}

%post	-n kernel-smp-extra-go7007
%depmod %{_kernel_ver}smp

%postun	-n kernel-smp-extra-go7007
%depmod %{_kernel_ver}smp

%if %{with kernel}
%files -n kernel-extra-go7007
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}/extra/*.ko*

%if %{with smp} && %{with dist_kernel}
%files -n kernel-smp-extra-go7007
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}smp/extra/*.ko*
%endif
%endif

%if %{with userspace}
%files
%defattr(644,root,root,755)
%attr(755,root,root) %{_bindir}/gorecord
%endif

%files devel
%defattr(644,root,root,755)
%{_includedir}/linux/*.h

%files firmware
%defattr(644,root,root,755)
/lib/firmware/*
%attr(755,root,root) %{_sysconfdir}/hotplug/usb/wis-ezusb
%{_sysconfdir}/hotplug/usb/wis.usermap