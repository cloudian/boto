# Copyright (c) 2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2011, Eucalyptus Systems, Inc.
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

import os
import datetime

import boto.utils
from boto.compat import json


class Credentials(object):
    """
    :ivar access_key: The AccessKeyID.
    :ivar secret_key: The SecretAccessKey.
    :ivar session_token: The session token that must be passed with
                         requests to use the temporary credentials
    :ivar expiration: The timestamp for when the credentials will expire
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.access_key = None
        self.secret_key = None
        self.session_token = None
        self.expiration = None
        self.request_id = None

    @classmethod
    def from_json(cls, json_doc):
        """
        Create and return a new Session Token based on the contents
        of a JSON document.

        :type json_doc: str
        :param json_doc: A string containing a JSON document with a
            previously saved Credentials object.
        """
        d = json.loads(json_doc)
        token = cls()
        token.__dict__.update(d)
        return token

    @classmethod
    def load(cls, file_path):
        """
        Create and return a new Session Token based on the contents
        of a previously saved JSON-format file.

        :type file_path: str
        :param file_path: The fully qualified path to the JSON-format
            file containing the previously saved Session Token information.
        """
        fp = open(file_path)
        json_doc = fp.read()
        fp.close()
        return cls.from_json(json_doc)

    def startElement(self, name, attrs, connection):
        return None

    def endElement(self, name, value, connection):
        if name == 'AccessKeyId':
            self.access_key = value
        elif name == 'SecretAccessKey':
            self.secret_key = value
        elif name == 'SessionToken':
            self.session_token = value
        elif name == 'Expiration':
            self.expiration = value
        elif name == 'RequestId':
            self.request_id = value
        else:
            pass

    def to_dict(self):
        """
        Return a Python dict containing the important information
        about this Session Token.
        """
        return {'access_key': self.access_key,
                'secret_key': self.secret_key,
                'session_token': self.session_token,
                'expiration': self.expiration,
                'request_id': self.request_id}

    def save(self, file_path):
        """
        Persist a Session Token to a file in JSON format.

        :type path: str
        :param path: The fully qualified path to the file where the
            the Session Token data should be written.  Any previous
            data in the file will be overwritten.  To help protect
            the credentials contained in the file, the permissions
            of the file will be set to readable/writable by owner only.
        """
        fp = open(file_path, 'w')
        json.dump(self.to_dict(), fp)
        fp.close()
        os.chmod(file_path, 0o600)

    def is_expired(self, time_offset_seconds=0):
        """
        Checks to see if the Session Token is expired or not.  By default
        it will check to see if the Session Token is expired as of the
        moment the method is called.  However, you can supply an
        optional parameter which is the number of seconds of offset
        into the future for the check.  For example, if you supply
        a value of 5, this method will return a True if the Session
        Token will be expired 5 seconds from this moment.

        :type time_offset_seconds: int
        :param time_offset_seconds: The number of seconds into the future
            to test the Session Token for expiration.
        """
        now = datetime.datetime.utcnow()
        if time_offset_seconds:
            now = now + datetime.timedelta(seconds=time_offset_seconds)
        ts = boto.utils.parse_ts(self.expiration)
        delta = ts - now
        return delta.total_seconds() <= 0


class FederationToken(object):
    """
    :ivar credentials: A Credentials object containing the credentials.
    :ivar federated_user_arn: ARN specifying federated user using credentials.
    :ivar federated_user_id: The ID of the federated user using credentials.
    :ivar packed_policy_size: A percentage value indicating the size of
                             the policy in packed form
    """

    def __init__(self, parent=None):
        self.parent = parent
        self.credentials = None
        self.federated_user_arn = None
        self.federated_user_id = None
        self.packed_policy_size = None
        self.request_id = None

    def startElement(self, name, attrs, connection):
        if name == 'Credentials':
            self.credentials = Credentials()
            return self.credentials
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Arn':
            self.federated_user_arn = value
        elif name == 'FederatedUserId':
            self.federated_user_id = value
        elif name == 'PackedPolicySize':
            self.packed_policy_size = int(value)
        elif name == 'RequestId':
            self.request_id = value
        else:
            pass

class AssumedRole(object):
    """
    :ivar user: The assumed role user.
    :ivar credentials: A Credentials object containing the credentials.
    """
    def __init__(self, connection=None, credentials=None, user=None):
        self._connection = connection
        self.credentials = credentials
        self.user = user

    def startElement(self, name, attrs, connection):
        if name == 'Credentials':
            self.credentials = Credentials()
            return self.credentials
        elif name == 'AssumedRoleUser':
            self.user = User()
            return self.user

    def endElement(self, name, value, connection):
        pass

class AssumedRoleWithSAML(AssumedRole):
    """
    :ivar user: The assumed role user.
    :ivar credentials: A Credentials object containing the credentials.
    :ivar audience: The value of the Recipient attribute of the
          SubjectConfirmationData element of the SAML assertion.
    :ivar issuer: The value of the Issuer element of the SAML assertion.
    :ivar name_qualifier: A hash value based on the concatenation of the
          Issuer response value, the AWS account ID, and the friendly name
          (the last part of the ARN) of the SAML provider in IAM. The
          combination of NameQualifier and Subject can be used to uniquely
          identify a federated user.
          The following pseudocode shows how the hash value is calculated:
            BASE64(SHA1("issuer" + "123456789012" + "/MySAMLIdP"))
    :ivar packed_policy_size: A percentage value that indicates the packed
          size of the session policies and session tags combined passed in the
          request. The request fails if the packed size is greater than 100
          percent, which means the policies and tags exceeded the allowed
          space. Integer.
    :ivar subject: The value of the NameID element in the Subject element of
          the SAML assertion.
    :ivar subject_type: The format of the name ID, as defined by the Format
          attribute in the NameID element of the SAML assertion. Typical
          examples of the format are transient or persistent. If the format
          includes the prefix urn:oasis:names:tc:SAML:2.0:nameid-format, that
          prefix is removed. For example,
          urn:oasis:names:tc:SAML:2.0:nameid-format:transient is returned as
          transient. If the format includes any other prefix, the format is
          returned with no modifications.
    """
    def __init__(self, connection=None, credentials=None, user=None):
        super(AssumedRoleWithSAML, self).__init__(connection, credentials, user)
        self.audience = None
        self.issuer = None
        self.name_qualifier = None
        self.packed_policy_size = None
        self.subject = None
        self.subject_type = None

    def endElement(self, name, value, connection):
        super(AssumedRoleWithSAML, self).endElement(name, value, connection)
        if name == 'Audience':
            self.audience = value
        elif name == 'Issuer':
            self.issuer = value
        elif name == 'NameQualifier':
            self.name_qualifier = value
        elif name == 'PackedPolicySize':
            self.packed_policy_size = int(value)
        elif name == 'Subject':
            self.subject = value
        elif name == 'SubjectType':
            self.subject_type = value

class User(object):
    """
    :ivar arn: The arn of the user assuming the role.
    :ivar assume_role_id: The identifier of the assumed role.
    """
    def __init__(self, arn=None, assume_role_id=None):
        self.arn = arn
        self.assume_role_id = assume_role_id

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Arn':
            self.arn = value
        elif name == 'AssumedRoleId':
            self.assume_role_id = value


class DecodeAuthorizationMessage(object):
    """
    :ivar request_id: The request ID.
    :ivar decoded_message: The decoded authorization message (may be JSON).
    """
    def __init__(self, request_id=None, decoded_message=None):
        self.request_id = request_id
        self.decoded_message = decoded_message

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'requestId':
            self.request_id = value
        elif name == 'DecodedMessage':
            self.decoded_message = value

class Identity(object):
    """
    :ivar arn: The AWS ARN associated with the calling entity.
    :ivar user_id: The unique identifier of the calling entity.
    :ivar account: The AWS account ID number of the account that owns or
                   contains the calling entity.
    """
    def __init__(self, parent=None):
        self.parent = parent
        self.arn = None
        self.user_id = None
        self.account = None
        self.request_id = None

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Arn':
            self.arn = value
        elif name == 'UserId':
            self.user_id = value
        elif name == 'Account':
            self.account = value
        elif name == 'RequestId':
            self.request_id = value
        else:
            pass

