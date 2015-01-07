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

class HSConfiguration(object):
    """
    HyperStore Configuration

    :ivar large_storage: The type of storage to use for HyperStore large storage.
        Current valid values are HSFS, EC.

    :ivar threshold: The size over which an object requires large storage.
    """

    def __init__(self, large_storage=None, threshold=None):
        self.large_storage = large_storage
        self.threshold = threshold

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'LargeStorage':
            self.large_storage = value
        elif name == 'Threshold':
            self.threshold = int(value)
        else:
            setattr(self, name, value)

    def to_xml(self):
        """
        Returns a string containing the XML version of the HyperStore
        configuration.
        """
        s = '<?xml version="1.0" encoding="UTF-8"?>'
        s += '<HSConfiguration xmlns="http://s3.cloudian.com/doc/2013-10-01/">'
        if self.large_storage:
            s += '<LargeStorage>' + self.large_storage + '</LargeStorage>'
        if self.threshold:
            s += '<Threshold>' + str(self.threshold) + '</Threshold>'
        s += '</HSConfiguration>'
        return s
