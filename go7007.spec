#
# TODO:
# - make licensing clear (especially for the firmware)
# - optflags for apps
#
# Conditional build:
%bcond_without	dist_kernel	# allow non-distribution kernel
%bcond_without	kernel		# don't build kernel modules
%bcond_without	up		# don't build UP module
%bcond_without	smp		# don't build SMP module
%bcond_without	userspace	# don't build userspace programs
%bcond_with	verbose		# verbose build (V=1)

%if !%{with kernel}
%undefine	with_dist_kernel
%endif

%define		_rel	0.1
Summary:	Exemplary userspace program for go7007 video capture cards
Summary(pl.UTF-8):	Przykładowy program dla kart przechwytywania obrazu go7007
Name:		go7007
Version:	0.9.7
Release:	%{_rel}
License:	Public Domain
Group:		Applications/Multimedia
Source0:	http://oss.wischip.com/wis-%{name}-linux-%{version}.tar.bz2
# Source0-md5:	eeae2af09c9563fb58a841517d669eb9
Source1:	%{name}-udev.rules
Patch0:		%{name}-hotplug.patch
Patch1:		%{name}-gorecord.patch
URL:		http://oss.wischip.com/
%if %{with kernel}
%{?with_dist_kernel:BuildRequires:	kernel-module-build >= 3:2.6.7}
BuildRequires:	rpmbuild(macros) >= 1.217
%endif
BuildRequires:	linux-libc-headers
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%description
Exemplary userspace program for go7007 video capture cards.

%description -l pl.UTF-8
Przykładowy program dla kart przechwytywania obrazu go7007.

%package devel
Summary:	Header files for the go7007 driver
Summary(pl.UTF-8):	Pliki nagłówkowe dla sterownika go7007
Group:		Development/Libraries
Requires:	linux-libc-headers

%description devel
Header files for the go7007 driver.

%description devel -l pl.UTF-8
Pliki nagłówkowe dla sterownika go7007.

%package firmware
Summary:	Firmware for the go7007 driver
Summary(pl.UTF-8):	Firmware dla sterownika go7007
License:	distributable
Group:		Base/Kernel
Requires:	fxload

%description firmware
Firmware for the go7007 driver.

%description firmware -l pl.UTF-8
Firmware dla sterownika go7007.

%package -n kernel-extra-go7007
Summary:	Linux driver for go7007
Summary(pl.UTF-8):	Sterownik dla Linuksa do go7007
Release:	%{_rel}@%{_kernel_ver_str}
License:	GPL v2
Group:		Base/Kernel
Requires(post,postun):	/sbin/depmod
%if %{with dist_kernel}
%requires_releq_kernel_up
Requires(postun):	%releq_kernel_up
%endif
Requires:	go7007-firmware

%description -n kernel-extra-go7007
This is driver for go7007 for Linux.

This package contains Linux module.

%description -n kernel-extra-go7007 -l pl.UTF-8
Sterownik dla Linuksa do go7007.

Ten pakiet zawiera moduł jądra Linuksa.

%package -n kernel-smp-extra-go7007
Summary:	Linux SMP driver for go7007
Summary(pl.UTF-8):	Sterownik dla Linuksa SMP do go7007
Release:	%{_rel}@%{_kernel_ver_str}
License:	GPL v2
Group:		Base/Kernel
Requires(post,postun):	/sbin/depmod
%if %{with dist_kernel}
%requires_releq_kernel_smp
Requires(postun):	%releq_kernel_smp
%endif
Requires:	go7007-firmware

%description -n kernel-smp-extra-go7007
This is driver for go7007 for Linux.

This package contains Linux SMP module.

%description -n kernel-smp-extra-go7007 -l pl.UTF-8
Sterownik dla Linuksa do go7007.

Ten pakiet zawiera moduł jądra Linuksa SMP.

%prep
%setup -q -n wis-%{name}-linux-%{version}
%patch0 -p1
%patch1 -p1

%build
%if %{with userspace}
sed 's,@FIRMWARE_DIR@,/lib/firmware,' < hotplug/wis-ezusb.in > hotplug/wis-ezusb

%{__make} -C apps \
	CFLAGS="-I../include -I/usr/include/ncurses"
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

%if %{with userspace}
install -d $RPM_BUILD_ROOT/lib/firmware/ezusb
install -p firmware/*.bin $RPM_BUILD_ROOT/lib/firmware
install -p firmware/ezusb/*.hex $RPM_BUILD_ROOT/lib/firmware/ezusb

install -d $RPM_BUILD_ROOT%{_sysconfdir}/hotplug/usb
install hotplug/wis-ezusb $RPM_BUILD_ROOT%{_sysconfdir}/hotplug/usb/wis-ezusb
install hotplug/wis.usermap-ezusb $RPM_BUILD_ROOT%{_sysconfdir}/hotplug/usb/wis.usermap

install -d $RPM_BUILD_ROOT%{_bindir}
install apps/gorecord $RPM_BUILD_ROOT%{_bindir}

install -d $RPM_BUILD_ROOT%{_includedir}/linux
install include/*.h $RPM_BUILD_ROOT%{_includedir}/linux

install -d $RPM_BUILD_ROOT%{_sysconfdir}/udev/rules.d
install %{SOURCE1} $RPM_BUILD_ROOT%{_sysconfdir}/udev/rules.d/100-go7007.rules
%endif

%if %{with kernel}
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
%if %{with up} || %{without dist_kernel}
%files -n kernel-extra-go7007
%defattr(644,root,root,755)
/lib/modules/%{_kernel_ver}/extra/*.ko*
%endif

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

%files devel
%defattr(644,root,root,755)
%{_includedir}/linux/*.h

%files firmware
%defattr(644,root,root,755)
/lib/firmware/*
%attr(755,root,root) %{_sysconfdir}/hotplug/usb/wis-ezusb
%{_sysconfdir}/hotplug/usb/wis.usermap
%{_sysconfdir}/udev/rules.d/100-go7007.rules
%endif
