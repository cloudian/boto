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

"""
<?xml version="1.0" encoding="UTF-8"?>
<ListInventoryConfigurationsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
  <InventoryConfiguration>
    <Id>test-inventory</Id>
    <IsEnabled>true</IsEnabled>
    <Destination>
      <S3BucketDestination>
        <Format>CSV</Format>
        <AccountId>008377198742</AccountId>
        <Bucket>arn:aws:s3:::aaabn</Bucket>
      </S3BucketDestination>
    </Destination>
    <Schedule>
      <Frequency>Daily</Frequency>
    </Schedule>
    <IncludedObjectVersions>Current</IncludedObjectVersions>
    <OptionalFields>
      <Field>Size</Field>
      <Field>LastModifiedDate</Field>
      <Field>StorageClass</Field>
    </OptionalFields>
  </InventoryConfiguration>
  <InventoryConfiguration>
    <Id>test-inventory2</Id>
    <IsEnabled>true</IsEnabled>
    <Filter>
      <Prefix>hogehoge</Prefix>
    </Filter>
    <Destination>
      <S3BucketDestination>
        <Format>CSV</Format>
        <AccountId>008377198742</AccountId>
        <Bucket>arn:aws:s3:::aaabn</Bucket>
        <Prefix>xxx</Prefix>
        <Encryption>
           <SSE-KMS>
              <KeyId>string</KeyId>
           </SSE-KMS>
           <SSE-S3>
           </SSE-S3>
        </Encryption>
      </S3BucketDestination>
    </Destination>
    <Schedule>
      <Frequency>Weekly</Frequency>
    </Schedule>
    <IncludedObjectVersions>All</IncludedObjectVersions>
    <OptionalFields />
  </InventoryConfiguration>
  <IsTruncated>false</IsTruncated>
  <!-- If ContinuationToken was provided in the request. -->
  <ContinuationToken>XXX</ContinuationToken>
  <!-- if IsTruncated == true -->
  <IsTruncated>true</IsTruncated>
  <NextContinuationToken>YYY</NextContinuationToken>
</ListInventoryConfigurationsResult>
"""

class InventoryFilter(object):
    """
    Specifies an inventory filter. The inventory only includes objects
    that meet the filter's criteria.

    :ivar prefix: The prefix that an object must have to be included
        in the inventory results.
    """
    def __init__(self, prefix=None):
        self.prefix = prefix
    def startElement(self, name, attrs, connection):
        return None
    def endElement(self, name, value, connection):
        if name == 'Prefix':
            self.prefix = value
    def to_xml(self):
        s = ''
        if self.prefix is not None:
            s = '<Filter>'
            s += '<Prefix>%s</Prefix>' % self.prefix
            s += '</Filter>'
        return s

class InventorySchedule(object):
    """
    Specifies the schedule for generating inventory results.

    :ivar frequency: Specifies how frequently inventory results
        are produced. Valid Values: "Daily" | "Weekly"
    """
    def __init__(self, frequency=None):
        self.frequency = frequency
    def startElement(self, name, attrs, connection):
        return None
    def endElement(self, name, value, connection):
        if name == 'Frequency':
            self.frequency = value
    def to_xml(self):
        s = ''
        if self.frequency is not None:
            s = '<Schedule>'
            s += '<Frequency>%s</Frequency>' % self.frequency
            s += '</Schedule>'
        return s

class KMSKeyId(object):
    """
    Specifies the use of SSE-KMS to encrypt delivered inventory reports.

    :ivar kms_keyid: Specifies the ID of the AWS Key Management Service
        (AWS KMS) symmetric customer managed customer master key (CMK)
        to use for encrypting inventory reports.
    """
    def __init__(self, kms_keyid=None):
        self.kms_keyid = kms_keyid
    def startElement(self, name, attrs, connection):
        return None
    def endElement(self, name, value, connection):
        if name == 'KeyId':
            self.kms_keyid = value
    def to_xml(self):
        s = ''
        if self.kms_keyid is not None:
            s += '<SSE-KMS>'
            s += '<KeyId>%s</KeyId>' % self.kms_keyid
            s += '</SSE-KMS>'
        return s

class InventoryEncryption(object):
    """
    Contains the type of server-side encryption used to encrypt
    the inventory results.

    :ivar kms_keyid: Specifies the use of SSE-KMS to encrypt
        delivered inventory reports.

    :ivar s3: Specifies the use of SSE-S3 to encrypt delivered
        inventory reports.
    """
    def __init__(self, kms_keyid=None, s3=None):
        if kms_keyid:
            self.kms_keyid = kms_keyid
        else:
            self.kms_keyid = KMSKeyId()
        self.s3 = s3

    def startElement(self, name, attrs, connection):
        if name == 'SSE-KMS':
            return self.kms_keyid
        return None

    def endElement(self, name, value, connection):
        if name == 'SSE-S3':
            self.s3 = True

    def to_xml(self):
        s = ''
        is_kms = self.kms_keyid.kms_keyid is not None and self.kms_keyid.kms_keyid is not None
        if is_kms or self.s3 is not None:
            s += '<Encryption>'
            if is_kms:
                s += self.kms_keyid.to_xml()
            if self.s3 is not None:
                s += '<SSE-S3>'
                s += '</SSE-S3>'
            s += '</Encryption>'
        return s

class S3BucketDestination(object):
    """
    Contains the bucket name, file format, bucket owner (optional),
    and prefix (optional) where inventory results are published.

    :ivar bname: The Amazon Resource Name (ARN) of the bucket where
        inventory results will be published.

    :ivar account_id: The account ID that owns the destination S3 bucket.
        If no account ID is provided, the owner is not validated before
        exporting data.

    :ivar format: Specifies the output format of the inventory results.
        Valid Values: "CSV" | "ORC" | "Parquet"

    :ivar prefix: The prefix that is prepended to all inventory results.

    :ivar encryption: Contains the type of server-side encryption used
        to encrypt the inventory results.
    """
    def __init__(self, bname=None, account_id=None, format=None, prefix=None,
                 encryption=None):
        self.bname = bname
        self.account_id = account_id
        self.format = format
        self.prefix = prefix
        if encryption:
            self.encryption = encryption
        else:
            self.encryption = InventoryEncryption()

    def startElement(self, name, attrs, connection):
        if name == 'Encryption':
            return self.encryption
        return None

    def endElement(self, name, value, connection):
        if name == 'Bucket':
            self.bname = value
        elif name == 'AccountId':
            self.account_id = value
        elif name == 'Format':
            self.format = value
        elif name == 'Prefix':
            self.prefix = value
        else:
            setattr(self, name, value)

    def to_xml(self):
        s = '<S3BucketDestination>'
        if self.bname is not None:
            s += '<Bucket>%s</Bucket>' % self.bname
        if self.account_id is not None:
            s += '<AccountId>%s</AccountId>' % self.account_id
        if self.format is not None:
            s += '<Format>%s</Format>' % self.format
        if self.prefix is not None:
            s += '<Prefix>%s</Prefix>' % self.prefix
        if self.encryption is not None:
            s += self.encryption.to_xml()
        s += '</S3BucketDestination>'
        return s

class InventoryDestination(object):
    """
    Specifies the inventory configuration for an Amazon S3 bucket.

    :ivar s3_bucket_destination: Contains the bucket name, file format,
        bucket owner (optional), and prefix (optional) where inventory
        results are published.
    """
    def __init__(self, s3_bucket_destination=None):
        if s3_bucket_destination:
            self.s3_bucket_destination = s3_bucket_destination
        else:
            self.s3_bucket_destination = S3BucketDestination()

    def startElement(self, name, attrs, connection):
        if name == 'S3BucketDestination':
            return self.s3_bucket_destination
        return None

    def endElement(self, name, value, connection):
        setattr(self, name, value)

    def to_xml(self):
        s = '<Destination>'
        s += self.s3_bucket_destination.to_xml()
        s += '</Destination>'
        return s

class InventoryOptionalFields(list):
    """
    Contains the optional fields that are included in the inventory results.

    """
    # Valid Values: Size | LastModifiedDate | StorageClass | ETag |
    #               IsMultipartUploaded | ReplicationStatus | EncryptionStatus |
    #               ObjectLockRetainUntilDate | ObjectLockMode | 
    #               ObjectLockLegalHoldStatus | IntelligentTieringAccessTier
    def __init__(self, size=None, last_modified_date=None, storage_class=None,
                 etag=None, is_multipart_uploaded=None, replication_status=None,
                 encryption_status=None, object_lock_retain_until_date=None,
                 object_lock_mode=None, object_lock_legal_hold_status=None,
                 intelligent_tiering_access_tier=None):
        if size is not None:
            self.append("Size")
        if last_modified_date is not None:
            self.append("LastModifiedDate")
        if storage_class is not None:
            self.append("StorageClass")
        if etag is not None:
            self.append("ETag")
        if is_multipart_uploaded is not None:
            self.append("IsMultipartUploaded")
        if replication_status is not None:
            self.append("ReplicationStatus")
        if encryption_status is not None:
            self.append("EncryptionStatus")
        if object_lock_retain_until_date is not None:
            self.append("ObjectLockRetainUntilDate")
        if object_lock_mode is not None:
            self.append("ObjectLockMode")
        if object_lock_legal_hold_status is not None:
            self.append("ObjectLockLegalHoldStatus")
        if intelligent_tiering_access_tier is not None:
            self.append("IntelligentTieringAccessTier")

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'Field':
            self.append(value)

    def to_xml(self):
        s = ''
        if len(self) > 0:
            s += '<OptionalFields>'
            for opt in self:
                s += '<Field>%s</Field>' % opt
            s += '</OptionalFields>'
        return s

class Inventory(object):
    """
    Specifies the inventory configuration for an Amazon S3 bucket.

    :ivar id: The ID used to identify the inventory configuration.

    :ivar is_enabled: Specifies whether the inventory is enabled or disabled.
        If set to "true", an inventory list is generated.
        If set to "false", no inventory list is generated.

    :ivar included_object_versions: Object versions to include in the inventory list.
        If set to "All", the list includes all the object versions, which adds
        the version-related fields VersionId, IsLatest, and DeleteMarker to the list.
        If set to "Current", the list does not contain these version-related fields.
        Valid Values: "All" | "Current".

    :ivar filter: Specifies an inventory filter. The inventory only includes objects
        that meet the filter's criteria.

    :ivar schedule: Specifies the schedule for generating inventory results.

    :ivar destination: Contains information about where to publish
        the inventory results.

    :ivar optional_fields: Contains the optional fields that are included
        in the inventory results.
    """
    def __init__(self, id=None, is_enabled=None,
                 included_object_versions=None,
                 filter=None,  schedule=None,
                 destination=None, optional_fields=None):
        self.id = id
        self.is_enabled = is_enabled
        self.included_object_versions = included_object_versions
        if filter:
            self.filter = filter
        else:
            self.filter = InventoryFilter()
        if schedule:
            self.schedule = schedule
        else:
            self.schedule = InventorySchedule()
        if destination:
            self.destination = destination
        else:
            self.destination = InventoryDestination()
        if optional_fields:
            self.optional_fields = optional_fields
        else:
            self.optional_fields = InventoryOptionalFields()

    def startElement(self, name, attrs, connection):
        if name == 'Filter':
            return self.filter
        elif name == 'Schedule':
            return self.schedule
        elif name == 'Destination':
            return self.destination
        elif name == 'OptionalFields':
            return self.optional_fields
        return None

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value
        elif name == 'IsEnabled':
            self.is_enabled = value
        elif name == 'IncludedObjectVersions':
            self.included_object_versions = value
        else:
            setattr(self, name, value)

    def to_xml(self, list=False):
        if list:
            s = '<InventoryConfiguration>'
        else:
            s = '<InventoryConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
        if self.id is not None:
            s += '<Id>%s</Id>' % self.id
        if self.is_enabled is not None:
            s += '<IsEnabled>%s</IsEnabled>' % self.is_enabled
        if self.filter is not None:
            s += self.filter.to_xml()
        if self.destination is not None:
            s += self.destination.to_xml()
        if self.schedule is not None:
            s += self.schedule.to_xml()
        if self.included_object_versions is not None:
            s += '<IncludedObjectVersions>%s</IncludedObjectVersions>' % self.included_object_versions
        if self.optional_fields is not None:
            s += self.optional_fields.to_xml()
        s += '</InventoryConfiguration>'
        return s

class InventoryConfiguration(list):
    """
    A container for the inventories associated with a Bucket Inventory Configuration.
    """
    def __init__(self):
        self.is_truncated = None
        self.continuation_token = None
        self.next_continuation_token = None

    def startElement(self, name, attrs, connection):
        if name == 'InventoryConfiguration':
            inventory = Inventory()
            self.append(inventory)
            return inventory
        return None

    def endElement(self, name, value, connection):
        if name == 'IsTruncated':
            self.is_truncated = value
        elif name == 'ContinuationToken':
            self.continuation_token = value
        elif name == 'NextContinuationToken':
            self.next_continuation_token = value
        else:
            setattr(self, name, value)

    def to_xml(self):
        s = ''
        s += '<ListInventoryConfigurationsResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">'
        for inventory in self:
            s += inventory.to_xml(list=True)
        if self.is_truncated is not None:
            s += '<IsTruncated>%s</IsTruncated>' % self.is_truncated
        if self.continuation_token is not None:
            s += '<ContinuationToken>%s</ContinuationToken>' % self.continuation_token
        if self.next_continuation_token is not None:
            s += '<NextContinuationToken>%s</NextContinuationToken>' % self.next_continuation_token
        s += '</ListInventoryConfigurationsResult>'
        return s

    def add_inventory(self, id=None, is_enabled=None, included_object_versions=None,
                      filter=None, schedule=None, destination=None, optional_fields=None):
        """
        Add an inventory to this Bucket Inventory Configuration.

        :type id: str
        :param id: The ID used to identify the inventory configuration.

        :type is_enabled: str
        :param is_enabled: Specifies whether the inventory is enabled or disabled.
            If set to "true", an inventory list is generated.
            If set to "false", no inventory list is generated.

        :type included_object_versions: str
        :param included_object_versions: Object versions to include in the inventory list.
            If set to "All", the list includes all the object versions, which adds
            the version-related fields VersionId, IsLatest, and DeleteMarker to the list.
            If set to "Current", the list does not contain these version-related fields.
            Valid Values: "All" | "Current".

        :type filter: InventoryFilter
        :param filter: Specifies an inventory filter. The inventory only includes objects
            that meet the filter's criteria.

        :type schedule: InventorySchedule
        :param schedule: Specifies the schedule for generating inventory results.

        :type destination: InventoryDestination
        :param destination: Contains information about where to publish
            the inventory results.

        :type optional_fields: InventoryOptionalFields
        :param optional_fields: Contains the optional fields that are included
            in the inventory results.
        """
        inventory = Inventory(id, is_enabled, included_object_versions,
                              filter, schedule, destination, optional_fields)
        self.append(inventory)
