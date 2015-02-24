Usage
=====

This project provides a script which generates a U-Boot boot script for
Tegra devices running upstream U-Boot.

Some simple invocations are:

    ./gen-uboot-script.py

        Generates a boot.scr that may be placed in /boot on a disk.
        This assumes that the U-Boot variable "rootpart" specifies the
        partition number of the root file-system, and that /boot is simply
        a sub-directory of the root file-system.

    ./gen-uboot-script.py --type net --partuuid XXX

        Generates a boot.scr that may be placed into /var/lib/tftpboot on a
        TFTP server, for use with the U-Boot comamnd "run bootcmd_dhcp". This
        script loads the kernel, DTB, and optional initrd over TFTP, then
        boots Linux using the specified root filesystem.

Numerous options are available; run the following to get help:

    ./gen-uboot-script.py --help

Also included is part-uuid.py, which determines the partition UUID of a disk
partition. This may be used to provide the parameter to gen-uboot-script.py's
--partuuid option. A simple invocation is:

    ./part-uuid.py /dev/sdc 1

        Prints the partition UUID of partition 1 on /dev/sdc.

The standard blkid command may be used to determine a partition's filesystem
UUID, for use with gen-uboot-script.py's --fsuuid option.

Submitting Changes
==================

To submit patches to this project, please use the following commands:

* git format-patch --subject-prefix="uboot scripts PATCH"

  Creates a patch file from your git commit.

* git send-email --to linux-tegra@vger.kernel.org *.patch

  Sends the patch by email to the Tegra mailing list.

Even though the primary upstream repository for this project is hosted on
github, contributions aren't accepted via github pull requests. Github pull
requests would bypass public code review on the project mailing list.

Patches should be signed off (include a signed-off-by line) to indicate your
acceptance of the code's license (see the license header in each file). See
http://developercertificate.org/ for details of what signed-off-by implies.
