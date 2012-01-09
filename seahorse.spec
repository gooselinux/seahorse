Name: 		seahorse
Version: 	2.28.1
Release:        4%{?dist}
Summary:	A GNOME application for managing encryption keys
Group: 		User Interface/Desktops
# seahorse is GPLv2+
# libcryptui is LGPLv2+
License:        GPLv2+ and LGPLv2+
URL:            http://projects.gnome.org/seahorse/
Source:         http://download.gnome.org/sources/seahorse/2.28/%{name}-%{version}.tar.bz2
BuildRoot: 	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:  desktop-file-utils
BuildRequires:  gettext
BuildRequires:  gpgme-devel >= 1.0
BuildRequires:  gnupg2
BuildRequires:  libgnome-devel
BuildRequires:  libgnomeui-devel
BuildRequires:  scrollkeeper
BuildRequires:  libsoup-devel
BuildRequires:  openldap-devel
BuildRequires:  gnome-panel-devel
BuildRequires:  libnotify-devel
BuildRequires:  openssh-clients
BuildRequires:  gnome-doc-utils >= 0.3.2
BuildRequires:  gnome-keyring-devel >= 2.25.5
BuildRequires:  avahi-devel
BuildRequires:  avahi-glib-devel
BuildRequires:	intltool
Requires(post): desktop-file-utils
Requires(post): GConf2
Requires(post): scrollkeeper
Requires(post): shared-mime-info
Requires(postun): desktop-file-utils
Requires(postun): scrollkeeper
Requires(postun): shared-mime-info

# https://bugzilla.redhat.com/show_bug.cgi?id=474419
Requires:       pinentry-gtk

Obsoletes: gnome-keyring-manager

# https://bugzilla.gnome.org/show_bug.cgi?id=604541
# https://bugzilla.redhat.com/show_bug.cgi?id=547454
Patch0: property-get.patch

%description
Seahorse is a graphical interface for managing and using encryption keys.
It also integrates with nautilus, gedit and other places for encryption
operations.


%package devel
Summary: Header files and libraries required to develop with seahorse
Group: Development/Libraries
Requires: pkgconfig >= 1:0.14
Requires: %{name} = %{version}-%{release}
Requires: gtk-doc

%description devel
The seahorse-devel package contains the header files for the libcryptui
library that belongs to seahorse.

%prep
%setup -q
%patch0 -p1 -b .property-get

%build
GNUPG=/usr/bin/gpg2 ; export GNUPG ; %configure --disable-scrollkeeper

# drop unneeded direct library deps with --as-needed
# libtool doesn't make this easy, so we do it the hard way
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
sed -i -e 's/ -shared / -Wl,-O1,--as-needed\0 /g' -e 's/    if test "$export_dynamic" = yes && test -n "$export_dynamic_flag_spec"; then/      func_append compile_command " -Wl,-O1,--as-needed"\n      func_append finalize_command " -Wl,-O1,--as-needed"\n\0/' libtool

make %{?_smp_mflags}
# cleanup permissions for files that go into debuginfo
find . -type f -name "*.c" -exec chmod a-x {} ';'

%install
rm -rf ${RPM_BUILD_ROOT}

export GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL=1
make install DESTDIR=$RPM_BUILD_ROOT
#mkdir -p $RPM_BUILD_ROOT/etc/X11/xinit/xinitrc.d/
#install -m 755 %{SOURCE1} $RPM_BUILD_ROOT/etc/X11/xinit/xinitrc.d/seahorse-agent.sh


unset GCONF_DISABLE_MAKEFILE_SCHEMA_INSTALL
%find_lang seahorse --with-gnome --all-name

# seahorse has no description in startup applications
# https://bugzilla.redhat.com/show_bug.cgi?id=573022
# Copy the "Manage your passwords and encryption keys" description and all translations
grep '^Comment' ${RPM_BUILD_ROOT}%{_datadir}/applications/seahorse.desktop >> ${RPM_BUILD_ROOT}%{_sysconfdir}/xdg/autostart/seahorse-daemon.desktop

desktop-file-install --vendor fedora --delete-original  \
  --dir ${RPM_BUILD_ROOT}%{_datadir}/applications       \
  --add-category GNOME                                  \
  --add-category Utility                                \
  --add-category X-Fedora                               \
  ${RPM_BUILD_ROOT}%{_datadir}/applications/seahorse.desktop

# nuke the icon cache
rm -f ${RPM_BUILD_ROOT}/usr/share/icons/hicolor/icon-theme.cache

find ${RPM_BUILD_ROOT} -type f -name "*.la" -exec rm -f {} ';'
find ${RPM_BUILD_ROOT} -type f -name "*.a" -exec rm -f {} ';'

# save some space: only one screenshot is actually used, and it is
# identical in all languages
cd ${RPM_BUILD_ROOT}/usr/share/gnome/help/seahorse
for d in *; do
  if [ -d $d -a "$d" != "C" ]; then
    rm $d/figures/*
    ln -s ../../C/figures/seahorse-window.png $d/figures/seahorse-window.png
  fi
done

%clean
rm -rf ${RPM_BUILD_ROOT}


%post
/sbin/ldconfig
export GCONF_CONFIG_SOURCE=`gconftool-2 --get-default-source`
gconftool-2 \
     --makefile-install-rule \
     %{_sysconfdir}/gconf/schemas/%{name}.schemas > /dev/null || :
scrollkeeper-update -q ||:
update-mime-database %{_datadir}/mime/ > /dev/null
update-desktop-database %{_datadir}/applications > /dev/null 2>&1 || :
touch --no-create %{_datadir}/icons/hicolor || :
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
   %{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :
fi



%postun
/sbin/ldconfig
scrollkeeper-update -q ||:
update-mime-database %{_datadir}/mime/ > /dev/null
update-desktop-database %{_datadir}/applications > /dev/null 2>&1 || :
touch --no-create %{_datadir}/icons/hicolor || :
if [ -x %{_bindir}/gtk-update-icon-cache ]; then
   %{_bindir}/gtk-update-icon-cache --quiet %{_datadir}/icons/hicolor || :
fi


%files -f %{name}.lang
%defattr(-,root,root,-)
%doc AUTHORS COPYING NEWS README TODO
%{_bindir}/*
%dir %{_datadir}/%{name}
%{_datadir}/%{name}/*
%{_datadir}/applications/*.desktop
%{_datadir}/icons/hicolor/*/apps/seahorse.png
%{_datadir}/icons/hicolor/*/apps/seahorse-preferences.png
%{_datadir}/pixmaps/*
%{_mandir}/man1/*.gz
%dir %{_libdir}/seahorse
%{_libdir}/seahorse/*
%{_libdir}/libcryptui*.so.*
%{_sysconfdir}/gconf/schemas/*
%{_datadir}/dbus-1/services/org.gnome.seahorse.service
%{_sysconfdir}/xdg/autostart/seahorse-daemon.desktop

%files devel
%defattr(-,root,root,-)
%{_libdir}/libcryptui.so
%{_includedir}/libcryptui
%{_libdir}/pkgconfig/cryptui-0.0.pc
%{_datadir}/gtk-doc/html/libcryptui
%{_datadir}/gtk-doc/html/libseahorse

%changelog
* Mon Mar 15 2010 Tomas Bzatek <tbzatek@redhat.com> 2.28.1-4
- Better description for the autostart daemon (#573022)

* Tue Jan 12 2010 Tomas Bzatek <tbzatek@redhat.com> 2.28.1-3
- Spec file cleanup, fix rpaths

* Tue Dec 15 2009 Tomas Bzatek <tbzatek@redhat.com> 2.28.1-2
- Fix a wrong use of gdk_property_get that can lead to crashes (#547454)

* Mon Oct 19 2009 Tomas Bzatek <tbzatek@redhat.com> 2.28.1-1
- Update to 2.28.1

* Tue Sep 22 2009 Tomas Bzatek <tbzatek@redhat.com> 2.28.0-1
- Update to 2.28.0

* Mon Sep 14 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.92-1
- Update to 2.27.92

* Wed Aug 26 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.90-2
- Make seahorse respect the button-images setting

* Tue Aug 11 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.90-1
- Update to 2.27.90

* Thu Aug  6 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.5-2
- Bring the password tab back

* Tue Jul 28 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.5-1
- Update to 2.27.5

* Mon Jul 27 2009 Matthias Clasen <mclasen@redhat.com> - 2.27.1-4
- Drop unneeded direct deps

* Sun Jul 26 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.27.1-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_12_Mass_Rebuild

* Mon Jun  1 2009 Tomas Bzatek <tbzatek@redhat.com> 2.27.1-2
- Require pinentry-gtk (#474419)

* Mon May  4 2009 Tomas Bzatek <tbzatek@redhat.com> 2.27.1-1
- Update to 2.27.1

* Sun Apr 12 2009 Matthias Clasen <mclasen@redhat.com> 2.26.1-1
- Update to 2.26.1
- See http://download.gnome.org/sources/seahorse/2.26/seahorse-2.26.1.news

* Fri Apr 10 2009 Matthias Clasen <mclasen@redhat.com> 2.26.0-2
- Fix directory ownership

* Mon Mar 16 2009 Tomas Bzatek <tbzatek@redhat.com> 2.26.0-1
- Update to 2.26.0

* Mon Mar  2 2009 Tomas Bzatek <tbzatek@redhat.com> 2.25.92-1
- Update to 2.25.92

* Wed Feb 25 2009 Fedora Release Engineering <rel-eng@lists.fedoraproject.org> - 2.25.91-2
- Rebuilt for https://fedoraproject.org/wiki/Fedora_11_Mass_Rebuild

* Sat Feb 14 2009 Matthias Clasen <mclasen@redhat.com> 2.25.91-1
- Update to 2.25.91

* Tue Feb  3 2009 Matthias Clasen <mclasen@redhat.com> 2.25.90-1
- Update to 2.25.90

* Wed Jan  7 2009 Matthias Clasen <mclasen@redhat.com> 2.25.4-1
- Update to 2.25.4

* Mon Dec 22 2008 Tomas Bzatek <tbzatek@redhat.com> 2.25.3-1
- Update to 2.25.3

* Tue Dec  2 2008 Matthias Clasen <mclasen@redhat.com> 2.25.1-3
- Rebuild for pkg-config provides

* Mon Dec  1 2008 Tomas Bzatek <tbzatek@redhat.com> 2.25.1-2
- Mark Seahorse as an official replacement for gnome-keyring-manager

* Thu Nov 13 2008 Matthias Clasen <mclasen@redhat.com> 2.25.1-1
- Update to 2.25.1

* Sun Oct 19 2008 Matthias Clasen <mclasen@redhat.com> 2.24.1-1
- Update to 2.24.1

* Thu Oct  9 2008 Matthias Clasen <mclasen@redhat.com> 2.24.0-3
- Save some space

* Sun Sep 21 2008 Matthias Clasen <mclasen@redhat.com> 2.24.0-2
- Update to 2.24.0

* Sun Sep  7 2008 Matthias Clasen <mclasen@redhat.com> 2.23.92-1
- Update to 2.23.92

* Thu Sep  4 2008 Matthias Clasen <mclasen@redhat.com> 2.23.91-1
- Update to 2.23.91

* Sat Aug 30 2008 Michel Salim <salimma@fedoraproject.org> 2.23.90-2
- Patch configure to detect gpg2 binary

* Sat Aug 23 2008 Matthias Clasen <mclasen@redhat.com> 2.23.90-1
- Update to 2.23.90

* Tue Aug  5 2008 Matthias Clasen <mclasen@redhat.com> 2.23.6-1
- Update to 2.23.6
- Split off a -devel package

* Tue Jul 22 2008 Matthias Clasen <mclasen@redhat.com> 2.23.5-1
- Update to 2.23.5

* Mon Apr  7 2008 Matthias Clasen <mclasen@redhat.com> 2.22.1-1
- Update to 2.22.1

* Mon Mar 10 2008 Matthias Clasen <mclasen@redhat.com> 2.22.0-1
- Update to 2.22.0

* Tue Feb 26 2008 Matthias Clasen <mclasen@redhat.com> 2.21.92-1
- Update to 2.21.92

* Fri Feb 15 2008 Matthias Clasen <mclasen@redhat.com> 2.21.90-2
- Rebuild

* Tue Jan 29 2008 Seth Vidal <skvidal at fedoraproject.org> 2.21.90-1
- 2.21.90
- rebuild for new libsoup


* Mon Jan  7 2008 Seth Vidal <skvidal at fedoraproject.org> 2.21.4-2
- drop in seahorse-agent.sh to xinit - closes bug 427466 but will mean
  that seahorse agent will start if it is installed - even on kde or xfce
  desktops :(

* Thu Jan  3 2008 Seth Vidal <skvidal at fedoraproject.org> 2.21.4-1
- upgrade to 2.21.4


* Sat Dec  1 2007 Matt Domsch <mdomsch at fedoraproject.org> 2.21.3-1
- upgrade to 2.21.3
- enable avahi integration
- rpmlint cleanups: remove rpath, unneeded .so, tag config files

* Wed Aug 22 2007 Seth Vidal <skvidal at fedoraproject.org>
- fix license tag
- rebuild for fun!

* Fri Jul 20 2007 Seth Vidal <skvidal at fedoraproject.org>
- disable gedit plugin in rawhide, for now :(

* Tue Jun 26 2007 Seth Vidal <skvidal at fedoraproject.org>
- update to 1.0.1

* Sun Aug 13 2006 Seth Vidal <skvidal at linux.duke.edu>
- re-enable gedit
- update to 0.8.1

* Tue Mar  7 2006 Seth Vidal <skvidal at linux.duke.edu>
- added openldap-devel buildreq to hopefully close bug # 184124

* Thu Feb 23 2006 Seth Vidal <skvidal at linux.duke.edu>
- Patch from John Thacker for rh bug #182694 


* Mon Jan 16 2006 Seth Vidal <skvidal at linux.duke.edu> - 0.8-2
- added configure patch for it to build
- disable gedit plugins until seahorse gets fixed to work with gedit 2.13+

* Wed Oct 26 2005 Seth Vidal <skvidal@phy.duke.edu> - 0.8-1
- 0.8

* Thu Jul 28 2005 Seth Vidal <skvidal@phy.duke.edu> - 0.7.9-1
- 0.7.9

* Wed May 25 2005 Jeremy Katz <katzj@redhat.com> - 0.7.7-3
- make sure all files are included
- BR nautilus-devel

* Sun May 22 2005 Jeremy Katz <katzj@redhat.com> - 0.7.7-2
- rebuild on all arches

* Thu May  5 2005 Seth Vidal <skvidal@phy.duke.edu> 0.7.7-1
- 0.7.7

* Tue Apr 19 2005 Seth Vidal <skvidal at phy.duke.edu> 0.7.6-4
- something innocuous to test on


* Fri Apr  7 2005 Michael Schwendt <mschwendt[AT]users.sf.net>
- rebuilt

* Fri Feb 25 2005 Phillip Compton <pcompton[AT]proteinmedia.com> 0.7.6-2
- desktop entry fixes.

* Fri Feb 25 2005 Phillip Compton <pcompton[AT]proteinmedia.com> 0.7.6-1
- 0.7.6.

* Mon Nov 09 2003 Phillip Compton <pcompton[AT]proteinmedia.com> 0:0.7.3-0.fdr.5
- BuildReq scrollkeeper.

* Wed Oct 22 2003 Phillip Compton <pcompton[AT]proteinmedia.com> 0:0.7.3-0.fdr.4
- Uncommented .la removal.

* Sun Sep 21 2003 Phillip Compton <pcompton[AT]proteinmedia.com> 0:0.7.3-0.fdr.3
- Grabbed new copy os source from upstream.
- Fixed path on Source0, to allow direct download.
- BuildReq desktop-file-utils.

* Sun Sep 21 2003 Phillip Compton <pcompton[AT]proteinmedia.com> 0:0.7.3-0.fdr.2
- Fixed file permission on source tarball.
- Fixed Group.
- Removed aesthetic comments.
- Brought more in line with current spec template.

* Sun Aug 17 2003 Phillip Compton <pcompton[AT]proteinmedia.com> 0:0.7.3-0.fdr.1
- Fedorification.
- Added path to Source0.
- Added URL.
- buildroot -> RPM_BUILD_ROOT.
- BuildReq libgnomeui-devel, eel2-devel, gpgme03-devel.
- BuildReq gettext.
- post Req GConf2.
- post/postun Req scrollkeeper.
- .la/.a removal.
- cosmetic changes.

* Fri May 02 2003 Matthew Hall <matt@ecsc.co.uk> 0.7.3-1
- 0.7.3 Release

* Wed Apr 23 2003 Matthew Hall <matt@ecsc.co.uk> 0.7.1-3
- Rebuilt against gpgme 0.3.15

* Sat Apr 12 2003 Matthew Hall <matt@ecsc.co.uk> 0.7.1-2
- RedHat 9 Rebuild

* Sun Jan 26 2003 Matthew Hall <matt@ecsc.co.uk>
- New Spec File

