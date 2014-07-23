#!/usr/bin/env python2

# Copyright (c) 2013, NVIDIA CORPORATION. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import argparse
import os
import sys

parser = argparse.ArgumentParser(
    description='Generate a U-Boot boot script')

parser.add_argument('--debug', action='store_true',
    help='turn on debugging prints')

parser.add_argument('--type', choices=['disk', 'net'], default='disk',
    help='type of boot-script to generate; defaults to disk')

parser.add_argument('-o', dest='outfile', default='boot.scr',
    help='output filename; defaults to boot.scr')

parser.add_argument('--initrd',
    help='initrd filename to load; defaults to no initrd')

parser.add_argument('--partuuid',
    help='root partition (not filesystem) UUID. Not applicable if an initrd ' +
         'is used. Defaults to auto-detection based on rootpart U-Boot ' +
         'environment variable')

parser.add_argument('--fsuuid',
    help='root filesystem UUID. Not applicable if an initrd ' +
         'is used. Defaults to auto-detection based on rootpart U-Boot ' +
         'environment variable')

parser.add_argument('--ro', action='store_const', const='ro', dest='rorw',
    help='initially mount root filesystem read-only')

parser.add_argument('--rw', action='store_const', const='rw', dest='rorw',
    help='initially mount root filesystem read-write (default)')

parser.add_argument('--no-con-ttyS0', action='store_true',
    help='Disable console on ttyS0 UART')

parser.add_argument('--no-con-tty1', action='store_true',
    help='Disable console on tty1 VT')

parser.add_argument('--earlyprintk', action='store_true',
    help='Enable early printk')

# loglevel=8 ignore_loglevel 
parser.add_argument('--noisy', action='store_true',
    help='Enable noisy kernel log output, ignoring log level')

parser.add_argument('--cmdline',
    help='Extra command-line options')

args = parser.parse_args()
if args.debug: print args

if args.initrd:
    if args.partuuid or args.fsuuid:
        raise Exception('--initrd used; --partuuid and --fsuuid should not be');

if args.type == 'net':
    if not args.initrd and not (args.partuuid or args.fsuuid):
        raise Exception('--type net used without initrd; --part/fsuuid should be')

if args.partuuid and args.fsuuid:
    raise Exception('--partuuid and --fsuuid should not be used together')

if not args.rorw:
    args.rorw = 'rw'

outfile_tmp = args.outfile + '.tmp'
f = file(outfile_tmp, 'wt')

if args.initrd:
    root = 'root=/dev/ram'
elif args.partuuid:
    root = 'root=PARTUUID=' + args.partuuid
elif args.fsuuid:
    root = 'root=UUID=' + args.fsuuid
else:
    f.write('part uuid ${devtype} ${devnum}:${rootpart} uuid\n')
    root = 'root=PARTUUID=${uuid}'

if args.type == 'net':
    f.write('dhcp\n')
    load='tftpboot'
    prefix=''
else:
    load='load ${devtype} ${devnum}:${rootpart}'
    prefix='/boot/'

f.write(load + ' ${kernel_addr_r} ' + prefix + 'zImage\n')

if args.initrd:
    f.write(load + ' ${ramdisk_addr_r} ' + prefix + args.initrd + '\n')
    f.write('ramdisk=${ramdisk_addr_r}:0x${filesize}\n')
    f.write('setenv initrd_high 0xffffffff\n')
    ramdisk = '${ramdisk}'
else:
    ramdisk = '-'

f.write('''\
if test -n "${fdtfile}"; then
    set _fdt ${fdtfile};
else
    set _fdt ${soc}-${board}${boardver}.dtb;
fi
''')
f.write(load + ' ${fdt_addr_r} ' + prefix + '${_fdt}\n')
f.write('set _fdt\n')

bootargs = ''
if not args.no_con_ttyS0:
    bootargs += 'console=ttyS0,115200n8 '
if not args.no_con_tty1:
    bootargs += 'console=tty1 '
if args.noisy:
    bootargs += 'ignore_loglevel '
if args.earlyprintk:
    bootargs += 'earlyprintk '
bootargs += args.rorw + ' rootwait ' + root + ' '
if args.cmdline:
    bootargs += args.cmdline + ' '
bootargs += '${extra_bootargs}'

f.write('setenv bootargs ' + bootargs + '\n')
f.write('bootz ${kernel_addr_r} ' + ramdisk + ' ${fdt_addr_r}\n')

f.close()

cmd = 'mkimage -A arm -O linux -T script -C none -a 0 -e 0 -n "Tegra Boot Script" -d ' + outfile_tmp + ' ' + args.outfile
print '+ ' + cmd
ret = os.system(cmd)
if ret:
    sys.exit(1)
