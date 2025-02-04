# -*- coding: utf-8 -*-
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import base64
import hashlib

from awscrt import checksums
from boto import config

# Caller should specify at least 'fp' or 'data'
# and 'data' is higher priority to use for checksum calculation.
def cal_checksum(fp=None, size=-1, ctype='crc32', data=None, previous_checksum=0):
    checksum = None
    if data is not None:
        rdata = data
    elif fp is not None:
        cpos = fp.tell()
        rdata = fp.read(size)
    if ctype == 'crc32':
        checksum = checksums.crc32(rdata, previous_crc32=previous_checksum)
        checksum = base64.b64encode(checksum.to_bytes(4, 'big')).decode('utf-8')
    elif ctype == 'crc32c':
        checksum = checksums.crc32c(rdata, previous_crc32c=previous_checksum)
        checksum = base64.b64encode(checksum.to_bytes(4, 'big')).decode('utf-8')
    elif ctype == 'crc64nvme':
        checksum = checksums.crc64nvme(rdata, previous_crc64nvme=previous_checksum)
        checksum = base64.b64encode(checksum.to_bytes(8, 'big')).decode('utf-8')
    elif ctype in ['sha1', 'sha256']:
        if ctype == 'sha1':
            h = hashlib.sha1()
        else:
            h = hashlib.sha256()
        if type(rdata) is list:
            for d in rdata:
                h.update(d)
        elif type(rdata) is bytes:
            h.update(rdata)
        dig = h.digest()
        checksum = base64.b64encode(dig).decode('utf-8')
    if fp is not None:
        fp.seek(cpos)
    return checksum

def set_checksum_header(checksum, provider, headers,
                        fp=None, size=-1, data=None):
    """
    Add checksum headers to headers dict if it is not
    set yet and checksum is specified.
    Adding headers:
        x-amz-sdk-checksum-algorithm: CRC32|CRC32C|CRC64NVME|SHA1|SHA256
        x-amz-checksum-{crc32|crc32c|crc64nvme|sha1|sha256}: calculated
                                                   checksum value

    :type checksum: string
    :param checksum: CRC32|CRC32C|CRC64NVME|SHA1|SHA256. The algorithm used to
        create the checksum for the request body.

    :type provider: Provider
    :param provider: The provider for the request.

    :type headers: dict
    :param headers: Additional HTTP headers that will be sent with
        the request.

    :type fp: file
    :param fp: The file object you want to calculate the checksum.

    :type size: int
    :param size: The size of the file object to calculate the checksum.

    :type data: bytes
    :param data: data you want to calculate the checksum.

    """
    headers = headers or {}
    if checksum is None:
        return headers
    # "x-amz-sdk-checksum-algorithm" header: CRC32|CRC32C|CRC64NVME|SHA1|SHA256
    # If key/value already provided in headers dictionary, we will use it as is.
    if provider.sdk_checksum_algorithm_header not in headers:
        headers[provider.sdk_checksum_algorithm_header] = checksum
    # calculate based on the algorithm
    checksum_lower = checksum.lower()
    if checksum_lower in ['crc32', 'crc32c', 'crc64nvme','sha1', 'sha256']:
        calculated_checksum = cal_checksum(fp=fp, size=size, ctype=checksum_lower, data=data)
        # If key/value already provided in headers dictionary, we will use it as is.
        if checksum_lower == 'crc32' and provider.checksum_crc32_header not in headers:
            headers[provider.checksum_crc32_header] = calculated_checksum
        elif checksum_lower == 'crc32c' and provider.checksum_crc32c_header not in headers:
            headers[provider.checksum_crc32c_header] = calculated_checksum
        elif checksum_lower == 'crc64nvme' and provider.checksum_crc64nvme_header not in headers:
            headers[provider.checksum_crc64nvme_header] = calculated_checksum
        elif checksum_lower == 'sha1' and provider.checksum_sha1_header not in headers:
            headers[provider.checksum_sha1_header] = calculated_checksum
        elif checksum_lower == 'sha256' and provider.checksum_sha256_header not in headers:
            headers[provider.checksum_sha256_header] = calculated_checksum
        if config.getbool('Boto', 'either_md5_checksum_headers', True):
            if len(headers.keys() & {provider.checksum_crc32_header,
                                     provider.checksum_crc32c_header,
                                     provider.checksum_crc64nvme_header,
                                     provider.checksum_sha1_header,
                                     provider.checksum_sha256_header}) > 0:
                if 'Content-MD5' in headers:
                    del headers['Content-MD5']
    return headers
