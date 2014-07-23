#!/usr/bin/env python2

# Copyright (c) 2011-2013, NVIDIA CORPORATION. All rights reserved.
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
import re
import struct
import sys

def unpack_u32_le(data, offset):
    return struct.unpack('<I', data[offset:(offset+4)])[0]

def unpack_u64_le(data, offset):
    return struct.unpack('<Q', data[offset:(offset+8)])[0]

def hexdump(d, indices):
    s = ''
    for i in indices:
        s += "%02x" % ord(d[i])
    return s

def find_uuid_mbr(dev, pnum, pdata):
    if pnum < 1 or pnum > 0xff:
        raise Exception('Invalid partition number %d' % pnum)

    disk_uuid = unpack_u32_le(pdata, 0x1b8)
    return '%08x-%02x' % (disk_uuid, pnum)

def find_uuid_efi(dev, pnum, pdata):
    gpt_ver = unpack_u32_le(pdata, 512 + 8)
    if gpt_ver != 0x00010000:
        raise Exception('Unexpected GPT version 0x%08x' % gpt_ver)

    num_parts = unpack_u32_le(pdata, 512 + 80)
    if pnum < 1 or pnum > num_parts:
        raise Exception('Invalid partition number %d' % pnum)

    ptable_lba = unpack_u64_le(pdata, 512 + 72)
    ptable_ent_size = unpack_u32_le(pdata, 512 + 84)

    ptable_ent_offset = (ptable_lba * 512) + ((pnum - 1) * ptable_ent_size)

    f = file(dev, 'rb')
    f.seek(ptable_ent_offset )
    type_uuid = f.read(16)
    part_uuid = f.read(16)
    f.close()

    if type_uuid == '\x00' * 16:
        raise Exception('Invalid partition number %d' % pnum)

    s = hexdump(part_uuid, (3, 2, 1, 0))
    s += '-'
    s += hexdump(part_uuid, (5, 4))
    s += '-'
    s += hexdump(part_uuid, (7, 6))
    s += '-'
    s += hexdump(part_uuid, (8, 9))
    s += '-'
    s += hexdump(part_uuid, (10, 11, 12, 13, 14, 15))

    return s

def find_uuid(dev, pnum):
    f = file(dev, 'rb')
    pdata = f.read(2 * 512)
    f.close()

    if pdata[511] != chr(0xaa):
        raise Exception('MBR not present')

    is_efi = pdata[512:520] == "EFI PART"
    if is_efi:
        return find_uuid_efi(dev, pnum, pdata)
    else:
        return find_uuid_mbr(dev, pnum, pdata)

parser = argparse.ArgumentParser(
    description="Determine a partition's (not filesystem's) UUID")

parser.add_argument('--debug', action='store_true',
    help='Turn on debugging prints')

parser.add_argument('device', metavar='DEVICE', type=str,
    help='The partitioned device')

parser.add_argument('pnum', metavar='PART-NUM', type=int,
    help='The partition number')

args = parser.parse_args()
if args.debug: print args

print find_uuid(args.device, args.pnum)
