%define __os_install_post %{nil}
%define uek %( uname -r | egrep -i uek | wc -l | awk '{print $1}' )
%define rpm_arch %( uname -p )
%define rpm_author Jason W. Plummer
%define rpm_author_email jason.plummer@ingramcontent.com
%define distro_id %( lsb_release -is )
%define distro_ver %( lsb_release -rs )
%define distro_major_ver %( echo "%{distro_ver}" | awk -F'.' '{print $1}' )
%define source_url http://suricata-ids.org/download/

Summary: a high performance Network IDS, IPS and Network Security Monitoring engine
Name: suricata
Release: 1.EL%{distro_major_ver}
License: GNU
Group: Security/Tools
BuildRoot: %{_tmppath}/%{name}-root

# This does a scrape of the %{source_url} looking for something approaching a non-beta download link
#%define latest_stable_release %( elinks -dump %{source_url} | egrep ".*[0-9].*\.\ http.*%{name}.*\.gz$" | egrep -v "beta" | sort | tail -1 | awk '{print $NF}' )
# JB - Actually, for now we want the beta until 2.1 stable is released
%define latest_stable_release http://www.openinfosecfoundation.org/download/suricata-2.1beta2.tar.gz

URL: %{latest_stable_release}

# This will produce the version of the tar.gz ball detected earlier, or rpmbuild will fail right away
%define latest_stable_version %( echo "%{latest_stable_release}" | awk -F'/' '{print $NF}' | sed -e 's/.tar.gz$//g' | awk -F'-' '{print $NF}' )

Version: %{latest_stable_version}

# These BuildRequires can be found in Base
BuildRequires: gcc, gcc-c++, automake, autoconf, libtool, make
BuildRequires: wget, gzip, /usr/bin/lsb_release, elinks
BuildRequires: pcre, pcre-devel
BuildRequires: libyaml, libyaml-devel
BuildRequires: libpcap, libpcap-devel
BuildRequires: libnfnetlink, libnfnetlink-devel 
BuildRequires: libcap-ng, libcap-ng-devel 
BuildRequires: nspr, nspr-devel 
BuildRequires: nss, nss-devel, nss-util, nss-util-devel 
BuildRequires: file, file-devel 
BuildRequires: zlib, zlib-devel 
BuildRequires: python-argparse python-simplejson python-setuptools python-distutils-extra
 
# This block handles Oracle Linux UEK .vs. EL BuildRequires
#%if %{uek}
#BuildRequires: kernel-uek-devel, kernel-uek-headers
#%else
#BuildRequires: kernel-devel, kernel-headers
#%endif
# These BuildRequires can be found in EPEL
BuildRequires: jansson, jansson-devel 
BuildRequires: libnet, libnet-devel 
BuildRequires: GeoIP, GeoIP-devel 

# These Requires can be found in Base
Requires: libyaml                >= 0
Requires: zlib                   >= 0
Requires: libnfnetlink           >= 1
Requires: nss                    >= 3.16
Requires: nss-util               >= 3.16
Requires: nspr                   >= 4.10
# These Requires can be found in EPEL
Requires: jansson                >= 2
Requires: libnet                 >= 1
Requires: libcap                 >= 2.16
Requires: libcap-ng              >= 0.6
Requires: pcre                   >= 7.8
Requires: GeoIP                  >= 1
Requires: python-argparse        >= 1.2
Requires: python-simplejson      >= 0.6
Requires: python-setuptools      >= 0.9
Requires: python-distutils-extra >= 1

Provides: libhtp

%define install_base /usr/local/%{name}
%define install_dir %{install_base}/%{version}

Source0: %{url}
#Source1: /usr/src/redhat/SOURCES/suricata_init_script

%description
Top 3 Reasons You Should Try Suricata:
1. Highly Scalable - Suricata is multi threaded. This means you can run 
one instance and it will balance the load of processing across every 
processor on a sensor Suricata is configured to use. This allows commodity 
hardware to achieve 10 gigabit speeds on real life traffic without 
sacrificing ruleset coverage.
2. Protocol Identification - The most common protocols are automatically 
recognized by Suricata as the stream starts, thus allowing rule writers to 
write a rule to the protocol, not to the port expected. This makes Suricata 
a Malware Command and Control Channel hunter like no other. Off port HTTP 
CnC channels, which normally slide right by most IDS systems, are child’s 
play for Suricata! Furthermore, thanks to dedicated keywords you can match 
on protocol fields which range from http URI to a SSL certificate identifier.
3. File Identification, MD5 Checksums, and File Extraction - Suricata can 
identify thousands of file types while crossing your network! Not only can 
you identify it, but should you decide you want to look at it further you 
can tag it for extraction and the file will be written to disk with a meta 
data file describing the capture situation and flow. The file’s MD5 checksum 
is calculated on the fly, so if you have a list of md5 hashes you want to 
keep in your network, or want to keep out, Suricata can find it.

%build
cd ~/rpmbuild/BUILD
wget %{url}
zcat %{name}-%{version}.tar.gz | tar xvf -
cd ~/rpmbuild/BUILD/%{name}-%{version}
eval cpu_count=`egrep "^physical id" /proc/cpuinfo | sort -u | wc -l | awk '{print $1}'`
if [ ${cpu_count} -gt 0 ]; then
    export MAKEFLAGS="-j${cpu_count}"
fi
./configure --prefix=%{install_dir} \
            --enable-unix-socket --enable-profiling --enable-geoip \
            --with-libnss-libraries=/usr/lib64 --with-libnss-includes=/usr/include/nss3 \
            --with-libnspr-libraries=/usr/lib64 --with-libnspr-includes=/usr/include/nspr4 \
            --enable-af-packet --disable-gccmarch-native
make

%install
rm -rf %{buildroot}
cd ~/rpmbuild/BUILD/%{name}-%{version}
# Populate %{buildroot}
make DESTDIR=%{buildroot} install
# NOTE: At the time of this RPM spec file creation, the install-conf and 
#       install-full make directives do not honor DESTDIR, which means
#       that their operations will download content to the local directory
#       specified by %{install_dir} above
make DESTDIR=%{buildroot} install-conf
make DESTDIR=%{buildroot} install-full
# Copy locally downloaded content into DESTDIR:
rsync -avHS --progress %{install_dir} %{buildroot}%{install_base}
# Then blow away the local copy
rm -rf %{install_base}
# Insert init script
#mkdir -p %{buildroot}/etc/rc.d/init.d && cp %{SOURCE1} %{buildroot}/etc/rc.d/init.d/suricata
# Build packaging manifest
rm -rf /tmp/MANIFEST.%{name}* > /dev/null 2>&1
echo '%defattr(-,root,root)' > /tmp/MANIFEST.%{name}
chown -R root:root %{buildroot} > /dev/null 2>&1
cd %{buildroot}
find . -depth -type d -exec chmod 755 {} \;
find . -depth -type f -exec chmod 644 {} \;
for i in `find . -depth -type f | sed -e 's/\ /zzqc/g'` ; do
    filename=`echo "${i}" | sed -e 's/zzqc/\ /g'`
    eval is_exe=`file "${filename}" | egrep -i "executable" | wc -l | awk '{print $1}'`
    if [ "${is_exe}" -gt 0 ]; then
        chmod 555 "${filename}"
    fi
done
find . -type f -or -type l | sed -e 's/\ /zzqc/' -e 's/^.//' -e '/^$/d' > /tmp/MANIFEST.%{name}.tmp
for i in `awk '{print $0}' /tmp/MANIFEST.%{name}.tmp` ; do
    filename=`echo "${i}" | sed -e 's/zzqc/\ /g'`
    dir=`dirname "${filename}"`
    echo "${dir}/*"
done | sort -u >> /tmp/MANIFEST.%{name}

%post
# Activate init script
#if [ /etc/rc.d/init.d/suricata ]; then
#    /sbin/chkconfig --add suricata && /sbin/chkconfig suricata on
#fi
# Create suricata var directories
if [ ! -d "%{install_dir}/var" ]; then
    mkdir -p "%{install_dir}/var/{log,run}/suricata"
    mkdir -p "%{install_dir}/var/log/suricata/{files,certs}"
fi
exit 0

%postun
# Get rid of any residual detritus
if [ -d "%{install_base}" ]; then
    rm -rf %{install_base} > /dev/null 2>&1
fi
exit 0

%files -f /tmp/MANIFEST.%{name}
%{buildroot}/%{install_base}/usr/local/suricata/%{version}/lib/libhtp-*

%changelog
%define today %( date +%a" "%b" "%d" "%Y )
* %{today} %{rpm_author} <%{rpm_author_email}>
- built version %{version} for %{distro_id} %{distro_ver}

