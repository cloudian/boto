# Copyright (c) 2012 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2012 Amazon.com, Inc. or its affiliates.  All Rights Reserved
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
from boto.compat import six
from boto.s3.tagging import Tag

class FilterSet(object):
    """
    Reference:
    https://docs.aws.amazon.com/AmazonS3/latest/userguide/intro-lifecycle-rules.html#intro-lifecycle-rules-filter

    - Specifying a filter based on object tag

    <LifecycleConfiguration>
        <Rule>
            <Filter>
               <Tag>
                  <Key>key</Key>
                  <Value>value</Value>
               </Tag>
            </Filter>
            transition/expiration actions.
        </Rule>
    </LifecycleConfiguration>

    - Specifying a filter based on multiple tags.
      You must wrap the tags in the <AND> element shown in the following example.

    <LifecycleConfiguration>
        <Rule>
          <Filter>
             <And>
                <Tag>
                   <Key>key1</Key>
                   <Value>value1</Value>
                </Tag>
                <Tag>
                   <Key>key2</Key>
                   <Value>value2</Value>
                </Tag>
                 ...
              </And>
          </Filter>
          transition/expiration actions.
        </Rule>
    </Lifecycle>

    - Specifying a filter based on both prefix and one or more tags

    <LifecycleConfiguration>
        <Rule>
            <Filter>
              <And>
                 <Prefix>key-prefix</Prefix>
                 <Tag>
                    <Key>key1</Key>
                    <Value>value1</Value>
                 </Tag>
                 <Tag>
                    <Key>key2</Key>
                    <Value>value2</Value>
                 </Tag>
                  ...
              </And>
            </Filter>
            <Status>Enabled</Status>
            transition/expiration actions.
        </Rule>
    </LifecycleConfiguration>

    - Specifying an empty filter, in which case the rule applies to all objects in the bucket.

    <LifecycleConfiguration>
        <Rule>
            <Filter>
            </Filter>
            <Status>Enabled</Status>
            transition/expiration actions.
        </Rule>
    </LifecycleConfiguration>
    """

    def __init__(self, prefix='', tag_list=[]):
        self.prefix = prefix
        self.tag_list = tag_list

    def startElement(self, name, attrs, connection):
        if name == 'Tag':
            tag = Tag()
            self.tag_list.append(tag)
            return tag
        return None

    def endElement(self, name, value, connection):
        if name == 'Prefix':
            self.prefix = value
        else:
            setattr(self, name, value)

    def add_tag(self, key, value):
        tag = Tag(key, value)
        self.tag_list.append(tag)

    def set_prefix(self, prefix):
        self.prefix = prefix

    def to_xml(self):
        and_tag = False
        if (len(self.tag_list) > 1 or
            (self.prefix != '' and len(self.tag_list) > 0)):
            and_tag = True
        xml = '<Filter>'
        if and_tag:
            xml += '<And>'
        if self.prefix != '':
            xml += '<Prefix>%s</Prefix>' % self.prefix
        for tag in self.tag_list:
            xml += tag.to_xml()
        if and_tag:
            xml += '</And>'
        xml += '</Filter>'
        return xml

class Rule(object):
    """
    A Lifecycle rule for an S3 bucket.

    :ivar id: Unique identifier for the rule. The value cannot be longer
        than 255 characters. This value is optional. The server will
        generate a unique value for the rule if no value is provided.

    :ivar prefix: Prefix identifying one or more objects to which the
        rule applies. If prefix is not provided, Boto generates a default
        prefix which will match all objects.

    :ivar filter: For backward compatibility. Default is True.
                  If True, <Filter> element is used.

    :ivar filter_set: An instance of `FilterSet`. This indicates
         a filter based on both the key prefix and one or more tags.

    :ivar status: If 'Enabled', the rule is currently being applied.
        If 'Disabled', the rule is not currently being applied.

    :ivar expiration: An instance of `Expiration`. This indicates
        the lifetime of the objects that are subject to the rule.

    :ivar transition: An instance of `Transition`.  This indicates
        when to transition to a different storage class.

    :ivar abortUpload: An instance of `AbortUpload`. This indicates when
        incomplete multi-part uploads will be aborted.

    :ivar ncExpiration: An instance of `Expiration`. This indicates
        the lifetime of non-current objects that are subject to the rule.

    :ivar ncTransition: An instance of `Transition`. This indicates when
        non-current objects transitions to a different storage class. 

    """
    def __init__(self, id=None, prefix='', filter=True, filter_set=None,
                 status=None, expiration=None, transition=None,
                 abortUpload=None, ncExpiration=None, ncTransition=None):
        self.id = id
        self.prefix = prefix
        self.filter = filter
        self.filter_set = filter_set
        self.status = status
        if isinstance(expiration, six.integer_types):
            # retain backwards compatibility???
            self.expiration = Expiration(days=expiration)
        else:
            # None or object
            self.expiration = expiration

        # retain backwards compatibility
        if isinstance(transition, Transition):
            self.transition = Transitions()
            self.transition.append(transition)
        elif transition:
            self.transition = transition
        else:
            self.transition = Transitions()

        if isinstance(abortUpload, AbortUpload):
            self.abortUpload = abortUpload
        else:
            self.abortUpload = AbortUpload()

        if ncExpiration:
            self.ncExpiration = ncExpiration
        else:
            self.ncExpiration = Expiration()

        if ncTransition:
            self.ncTransition = ncTransition
        else:
            self.ncTransition = Transitions()

    def __repr__(self):
        return '<Rule: %s>' % self.id

    def startElement(self, name, attrs, connection):
        if name == 'Transition':
            return self.transition
        elif name == 'Expiration':
            self.expiration = Expiration()
            return self.expiration
        elif name == 'AbortIncompleteMultipartUpload':
            return self.abortUpload
        elif name == 'NoncurrentVersionTransition':
            return self.ncTransition
        elif name == 'NoncurrentVersionExpiration':
            return self.ncExpiration
        elif name == 'Filter':
            self.filter_set = FilterSet()
            return self.filter_set
        return None

    def endElement(self, name, value, connection):
        if name == 'ID':
            self.id = value
        elif name == 'Prefix':
            self.prefix = value
        elif name == 'Filter':
            self.filter = True
        elif name == 'Status':
            self.status = value
        else:
            setattr(self, name, value)

    def to_xml(self):
        s = '<Rule>'
        if self.id is not None:
            s += '<ID>%s</ID>' % self.id
        if self.filter:
            if self.filter_set is not None:
                s += self.filter_set.to_xml()
        else:
            if self.prefix != '':
                s += '<Prefix>%s</Prefix>' % self.prefix
        s += '<Status>%s</Status>' % self.status
        if self.expiration is not None:
            s += self.expiration.to_xml()
        if self.transition is not None:
            s += self.transition.to_xml()
        if self.abortUpload is not None:
            s += self.abortUpload.to_xml()
        if self.ncTransition is not None:
            s += self.ncTransition.to_xml()
        if self.ncExpiration is not None:
            s += self.ncExpiration.to_xml()
        s += '</Rule>'
        return s

class AbortUpload(object):
    """
    When an incomplete multi-part upload will abort.

    :ivar days: The number of days until the MPU will abort
    """
    def __init__(self, days = None):
        self.days = days
    def startElement(self, name, attrs, connection):
        return None
    def endElement(self, name, value, connection):
        if name == 'DaysAfterInitiation':
            self.days = int(value)
    def __repr__(self):
        how_long = "in: %s days" % self.days
        return '<AbortUpload: %s>' % how_long
    def to_xml(self):
        s = ''
        if self.days is not None:
            s = '<AbortIncompleteMultipartUpload>'
            s += '<DaysAfterInitiation>%s</DaysAfterInitiation>' % self.days
            s += '</AbortIncompleteMultipartUpload>'
        return s

class Expiration(object):
    """
    When an object will expire.

    :ivar days: The number of days until the object expires

    :ivar date: The date when the object will expire. Must be
        in ISO 8601 format.
    """
    def __init__(self, days=None, date=None, ncDays = None, eodm = None):
        self.days = days
        self.date = date
        self.noncurrentDays = ncDays
        self.eodm = eodm

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Days':
            self.days = int(value)
        elif name == 'Date':
            self.date = value
        elif name == 'NoncurrentDays':
            self.noncurrentDays = value
        elif name == 'ExpiredObjectDeleteMarker':
            self.eodm = value

    def __repr__(self):
        if self.days is None:
            how_long = "on: %s" % self.date
        else:
            how_long = "in: %s days" % self.days
        return '<Expiration: %s>' % how_long

    def to_xml(self):
        s = ''
        if self.noncurrentDays is not None:
            s = '<NoncurrentVersionExpiration>'
            s += '<NoncurrentDays>%s</NoncurrentDays>' % self.noncurrentDays
            s += '</NoncurrentVersionExpiration>'
        
        if self.days is not None or self.date is not None or self.eodm is not None:
            s = '<Expiration>'
            if self.days is not None and self.noncurrentDays is None:
                s += '<Days>%s</Days>' % self.days
            elif self.date is not None and self.noncurrentDays is None:
                s += '<Date>%s</Date>' % self.date
            elif self.eodm is not None:
                s += '<ExpiredObjectDeleteMarker>%s</ExpiredObjectDeleteMarker>' % self.eodm
            s += '</Expiration>'
        return s

class Transition(object):
    """
    A transition to a different storage class.

    :ivar days: The number of days until the object should be moved.

    :ivar date: The date when the object should be moved.  Should be
        in ISO 8601 format.

    :ivar storage_class: The storage class to transition to.  Valid
        values are GLACIER, STANDARD_IA.
    """
    def __init__(self, days=None, date=None, ncDays=None, storage_class=None):
        self.days = days
        self.date = date
        self.storage_class = storage_class
        self.ncDays = ncDays
        #print "days = %s, date = %s, ncDays = %s, storage_class = %s" % (days, date, ncDays, storage_class)
    def __repr__(self):
        if self.days is None:
            how_long = "on: %s" % self.date
        else:
            how_long = "in: %s days" % self.days
        return '<Transition: %s, %s>' % (how_long, self.storage_class)

    def to_xml(self):
        s = ''
        if self.ncDays is not None:
            s = '<NoncurrentVersionTransition>'
            s += '<StorageClass>%s</StorageClass>' % self.storage_class
            s += '<NoncurrentDays>%s</NoncurrentDays>' % self.ncDays
            s += '</NoncurrentVersionTransition>'
        elif self.days is not None or self.date is not None:
            s = '<Transition>'
            s += '<StorageClass>%s</StorageClass>' % self.storage_class
            if self.days is not None:
                s += '<Days>%s</Days>' % self.days
            elif self.date is not None:
                s += '<Date>%s</Date>' % self.date
            s += '</Transition>'
        return s

class Transitions(list):
    """
    A container for the transitions associated with a Lifecycle's Rule configuration.
    """
    def __init__(self):
        self.transition_properties = 3
        self.current_transition_property = 1
        self.temp_days = None
        self.temp_date = None
        self.temp_storage_class = None
        self.temp_ncDays = None

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Days':
            self.temp_days = int(value)
        elif name == 'Date':
            self.temp_date = value
        elif name == 'StorageClass':
            self.temp_storage_class = value
        elif name == 'NoncurrentDays':
            self.temp_ncDays = int(value)

        # the XML does not contain a <Transitions> tag
        # but rather N number of <Transition> tags not
        # structured in any sort of hierarchy.
        if self.current_transition_property == self.transition_properties:
            self.append(Transition(self.temp_days, self.temp_date, self.temp_ncDays, self.temp_storage_class))
            self.temp_days = self.temp_date = self.temp_storage_class = None
            self.current_transition_property = 1
        else:
            self.current_transition_property += 1

    def to_xml(self):
        """
        Returns a string containing the XML version of the Lifecycle
        configuration as defined by S3.
        """
        s = ''
        for transition in self:
            s += transition.to_xml()
        return s

    def add_transition(self, days=None, date=None, ncDays=None,
                       storage_class = None):
        """
        Add a transition to this Lifecycle configuration.  This only adds
        the rule to the local copy.  To install the new rule(s) on
        the bucket, you need to pass this Lifecycle config object
        to the configure_lifecycle method of the Bucket object.

        :ivar days: The number of days until the object should be moved.

        :ivar date: The date when the object should be moved.  Should be
            in ISO 8601 format.

        :ivar storage_class: The storage class to transition to.  Valid
            values are GLACIER, STANDARD_IA.
        """
        transition = Transition(days, date, ncDays, storage_class)
        self.append(transition)

    def __first_or_default(self, prop):
        for transition in self:
            return getattr(transition, prop)
        return None

    # maintain backwards compatibility so that we can continue utilizing
    # 'rule.transition.days' syntax
    @property
    def days(self):
        return self.__first_or_default('days')

    @property
    def date(self):
        return self.__first_or_default('date')

    @property
    def storage_class(self):
        return self.__first_or_default('storage_class')


class Lifecycle(list):
    """
    A container for the rules associated with a Lifecycle configuration.
    """

    def __init__(self):
        self.tieringinfo = None
        self.compare = None
        self.retain = None

    def startElement(self, name, attrs, connection):
        if name == 'Rule':
            rule = Rule()
            self.append(rule)
            return rule
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)

    def to_xml(self):
        """
        Returns a string containing the XML version of the Lifecycle
        configuration as defined by S3.
        """
        s = '<?xml version="1.0" encoding="UTF-8"?>'
        s += '<LifecycleConfiguration>'
        for rule in self:
            s += rule.to_xml()
        s += '</LifecycleConfiguration>'
        return s

    def add_rule(self, id=None, prefix='', filter=True, filter_set=None,
                 status='Enabled', expiration=None, transition=None,
                 abortUpload=None, ncExpiration = None, ncTransition = None):
        """
        Add a rule to this Lifecycle configuration.  This only adds
        the rule to the local copy.  To install the new rule(s) on
        the bucket, you need to pass this Lifecycle config object
        to the configure_lifecycle method of the Bucket object.

        :type id: str
        :param id: Unique identifier for the rule. The value cannot be longer
            than 255 characters. This value is optional. The server will
            generate a unique value for the rule if no value is provided.

        :type prefix: str
        :iparam prefix: Prefix identifying one or more objects to which the
            rule applies.

        :type filter: bool
        :iparam filter: If True, <Filter> and </Filter> elements will
            be added in lifecycle xml rule.

        :type filter_set: FilterSet
        :iparam filter_set: Indicates a filter based on both the key prefix
            and one or more tags.

        :type status: str
        :param status: If 'Enabled', the rule is currently being applied.
            If 'Disabled', the rule is not currently being applied.

        :type transition: Transitions
        :param transition: Indicates when an object transitions to a
            different storage class.

        :type ncTransition: Transitions
        : param ncTransition: Indicates when a non-current object transitions
            to a different storage class.

        :type abortUpload: AbortUpload
        :param abortUpload: Indicates when an incomplete multi-part upload
            to be terminated.

        :type expiration: Expiration
        :param expiration: Indicates when an object expires, in either a 
            certain number of days or at a certain date. 

        :type ncExpiration: Expiration
        :param ncExpiration: Indicates when a non-current object expires, in 
            number of days of becoming non-current. Also indicates if the 
            expired delete markers shall be automatically expired.

        """
        rule = Rule(id, prefix, filter, filter_set, status, expiration,
                    transition, abortUpload, ncExpiration, ncTransition)
        self.append(rule)
