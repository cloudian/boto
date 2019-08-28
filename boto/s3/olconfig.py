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

class OLConfiguration(object):
    """
    Object Lock Configuration

    :ivar enabled: Indicates whether this bucket has an Object Lock
        configuration enabled. Valid Values: Enabled

    :ivar mode: The default Object Lock retention mode you want to
        apply to new objects placed in the specified bucket.
        Valid Values: GOVERNANCE | COMPLIANCE

    :ivar days: The number of days that you want to specify for
        the default retention period. Type: Integer

    :ivar years: The number of years that you want to specify for
        the default retention period. Type: Integer
    """

    def __init__(self, enabled=None, mode=None, days=None, years=None):
        self.enabled = enabled
        self.mode = mode
        self.days = days
        self.years = years

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'ObjectLockEnabled':
            self.enabled = value
        elif name == 'Mode':
            self.mode = value
        elif name == 'Days':
            self.days = int(value)
        elif name == 'Years':
            self.years = int(value)
        else:
            setattr(self, name, value)

    def to_xml(self):
        """
        Returns a string containing the XML version of the Object Lock
        configuration.
        """
        s = '<?xml version="1.0" encoding="UTF-8"?>'
        s += '<ObjectLockConfiguration xmlns="http://s3.cloudian.com/doc/2013-10-01/">'
        if self.enabled:
            s += '<ObjectLockEnabled>' + str(self.enabled) + '</ObjectLockEnabled>'
        if self.mode:
            s += '<Rule>'
            s += '<DefaultRetention>'
            s += '<Mode>' + self.mode + '</Mode>'
            if self.days:
                s += '<Days>' + str(self.days) + '</Days>'
            if self.years:
                s += '<Years>' + str(self.years) + '</Years>'
            s += '</DefaultRetention>'
            s += '</Rule>'
        s += '</ObjectLockConfiguration>'
        return s
