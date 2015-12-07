OPENWRTRELEASE=229d60fdb45c34902d402938e231c006f7c73931
PASSWORD=zeergeheim

BUILDDIR=build

PWH=$(shell mkpasswd --method=md5 --salt=vb1tLY1r ${PASSWORD})

all: openwrt-image
	@echo
	@echo
	@echo
	@echo the root password is \"${PASSWORD}\", sure you do not want to change it?!

#only fetch to have a clean tree
openwrt-origin: 
	git clone http://git.openwrt.org/14.07/openwrt.git openwrt-origin

#patch it, some sources use git as protocol which doesn't work through our proxy
openwrt-preparedworkdir: openwrt-origin openwrt-patch/* 
	git clone openwrt-origin openwrt || echo Clone directory performed earlier
	(cd openwrt; git checkout ${OPENWRTRELEASE})
	(cd openwrt; git apply ../openwrt-patch/0001-Remove-all-git-protocol-fetches.patch) || echo Patching done
	cp openwrt-patch/001-MostBlock.mk openwrt/target/linux/x86/generic/profiles/
	cp openwrt-patch/liotarget.mk openwrt/package/kernel/linux/modules/
	cp openwrt-patch/965-readonly-linux.patch openwrt/target/linux/generic/patches-3.10/
	(cd openwrt; ./scripts/feeds update -a)
	(cd openwrt; ./scripts/feeds install python python-curl python-json python-sqlite3 simplejson strongswan strongswan-utils sdparm smartmontools)
#Ugly method to include new Makefile for libffi (this one is part of the feeds)
	cp openwrt-patch/Makefile openwrt/feeds/packages/libs/libffi/
	touch openwrt-preparedworkdir

openwrt/files:
	(cd openwrt; ln -s ../files . || echo Link allready exists)

#For syntax checking etc. This improves turn around during development as you do not need to
#reboot the client to find an error in some basic python script
checkpython:
	[ ! -e /usr/bin/pychecker ] || pychecker `find files -name \*.py`

openwrt: openwrt-preparedworkdir openwrt-config kernel-config-3.10 openwrt/files
	cp openwrt-config openwrt/.config
	-[ "${CONFIG_LOCALMIRROR}" != "" ] && echo CONFIG_LOCALMIRROR=\"${CONFIG_LOCALMIRROR}\" >>openwrt/.config
	cp kernel-config-3.10 openwrt/target/linux/x86/config-3.10
	make -C openwrt oldconfig

files/etc/shadow: files/etc/shadow.default
	cat files/etc/shadow.default | sed 's~__PWHASH__~${PWH}~g' >files/etc/shadow

${BUILDDIR}:
	mkdir ${BUILDDIR}

target-cli: ${BUILDDIR} ${BUILDDIR}/configshell  ${BUILDDIR}/rtslib ${BUILDDIR}/targetcli
	echo clone done
	
${BUILDDIR}/configshell:
	git clone https://github.com/Datera/configshell.git ${BUILDDIR}/configshell

${BUILDDIR}/rtslib:
	git clone https://github.com/Datera/rtslib.git ${BUILDDIR}/rtslib

${BUILDDIR}/targetcli:
	git clone https://github.com/Datera/targetcli.git ${BUILDDIR}/targetcli

openwrt-image: openwrt files/etc/shadow checkpython
	make V=s -C openwrt

#for development only (these files are also in the openwrt-image)
#WARNING if the initrd.img contains obsolete files this may be very difficult to
#detect. ALWAYS copy both files
#scp initrd.img openwrt/bin/x86/openwrt-x86-generic-ramfs.bzImage 
openwrt-ramfsoverlay: files ${BUILDDIR} checkpython
	cd files; find . | cpio -H newc -o > ../build/initrd.img

testing-ramfsoverlay: openwrt-ramfsoverlay
	cd testing/ramfs_files/ ; find . | cpio -H newc -o > ../../build/testingrd-extra.img
	cat build/initrd.img build/testingrd-extra.img >build/testingrd.img

install: openwrt-image
	mkdir -p ${DESTDIR}/usr/bin/
	mkdir -p ${DESTDIR}/usr/share/misc/raqetclient/
	cp authoring/raqet ${DESTDIR}/usr/bin/
	cp openwrt/bin/x86/openwrt-x86-generic-ramfs.bzImage ${DESTDIR}/usr/share/misc/raqetclient/

uninstall: openwrt-image
	rm ${DESTDIR}/usr/bin/raqet
	rm -rf ${DESTDIR}/usr/share/misc/raqetclient/

test: testing-ramfsoverlay
	-./authoring/raqet -p secret --clientid testingclient --server http://10.0.2.2:8080  \
		--output build/testbuild.iso --target iso \
		--kernel ./openwrt/bin/x86/openwrt-x86-generic-ramfs.bzImage \
		--initrdextra build/testingrd.img
	-(cd testing; ./runtest)

run-using-tap: testing-ramfsoverlay
	echo type reboot to exit
	sleep 5
	./authoring/raqet -p secret --clientid testingclient --server http://192.168.13.1:5555 \
		--output build/testbuild.iso --target iso \
		--kernel ./openwrt/bin/x86/openwrt-x86-generic-ramfs.bzImage \
		--initrdextra build/initrd.img --plainiscsiinitiator 192.168.13.1/32
	(cd testing; sudo ./qemu-client-tap)


clean:
	-rm -rf build
	-rm -rf testing/stub_webserver.pyc
	-rm files/etc/shadow
	find files -name \*.pyc -exec rm {} \;

debiansourcepkg: dist_clean
	tar czf ../raqetclient_0.1.orig.tar.gz --exclude .git --exclude debian .
	dpkg-buildpackage -S

debianbinarypkg:
	dpkg-buildpackage -b

dist_clean: clean
	rm -rf openwrt-origin
	rm -rf openwrt-preparedworkdir
	rm -rf openwrt
