# Copyright (c) 2014 Cloudian Inc. All Rights Reserved
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

class PublicAccessBlock(object):
    """
    Public Access Block Configuration

    :ivar block_public_acls: Specifies whether Amazon S3 should block
        public access control lists (ACLs) for this bucket and objects
        in this bucket. Setting this element to "true" causes the following
        behavior:
        - PUT Bucket acl and PUT Object acl calls fail if the specified ACL is public.
        - PUT Object calls fail if the request includes a public ACL.
        - PUT Bucket calls fail if the request includes a public ACL.

    :ivar ignore_public_acls: Specifies whether Amazon S3 should ignore
        public ACLs for this bucket and objects in this bucket.
        Setting this element to "true" causes Amazon S3 to ignore all public
        ACLs on this bucket and objects in this bucket.

    :ivar block_public_policy: Specifies whether Amazon S3 should block
        public bucket policies for this bucket. Setting this element to "true"
        causes Amazon S3 to reject calls to PUT Bucket policy if the specified
        bucket policy allows public access.

    :ivar restrict_public_buckets: Specifies whether Amazon S3 should
        restrict public bucket policies for this bucket.
        Setting this element to "true" restricts access to this bucket
        to only AWS service principals and authorized users within this account
        if the bucket has a public policy.
    """

    def __init__(self, block_public_acls=None, ignore_public_acls=None,
                 block_public_policy=None, restrict_public_buckets=None):
        self.block_public_acls = block_public_acls
        self.ignore_public_acls = ignore_public_acls
        self.block_public_policy = block_public_policy
        self.restrict_public_buckets = restrict_public_buckets

    def __repr__(self):
        return '<PublicAccessBlockConfiguration: %s, %s, %s, %s>' % (self.block_public_acls,
                                                                     self.ignore_public_acls,
                                                                     self.block_public_policy,
                                                                     self.restrict_public_buckets)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'BlockPublicAcls':
            self.block_public_acls = value
        elif name == 'IgnorePublicAcls':
            self.ignore_public_acls = value
        elif name == 'BlockPublicPolicy':
            self.block_public_policy = value
        elif name == 'RestrictPublicBuckets':
            self.restrict_public_buckets = value
        else:
            setattr(self, name, value)

    def to_xml(self):
        """
        Returns a string containing the XML version of the Public Access
        Block configuration.
        """
        s = '<?xml version="1.0" encoding="UTF-8"?>'
        s += '<PublicAccessBlockConfiguration xmlns="http://s3.cloudian.com/doc/2013-10-01/">'
        if self.block_public_acls is not None:
            s += '<BlockPublicAcls>' + self.block_public_acls + '</BlockPublicAcls>'
        if self.ignore_public_acls is not None:
            s += '<IgnorePublicAcls>' + self.ignore_public_acls + '</IgnorePublicAcls>'
        if self.block_public_policy is not None:
            s += '<BlockPublicPolicy>' + self.block_public_policy + '</BlockPublicPolicy>'
        if self.restrict_public_buckets is not None:
            s += '<RestrictPublicBuckets>' + self.restrict_public_buckets + '</RestrictPublicBuckets>'
        s += '</PublicAccessBlockConfiguration>'
        return s
