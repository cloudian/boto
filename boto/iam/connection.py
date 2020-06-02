# Copyright (c) 2010-2011 Mitch Garnaat http://garnaat.org/
# Copyright (c) 2010-2011, Eucalyptus Systems, Inc.
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
import boto
import boto.jsonresponse
from boto.compat import json, six
from boto.resultset import ResultSet
from boto.iam.summarymap import SummaryMap
from boto.connection import AWSQueryConnection

DEFAULT_POLICY_DOCUMENTS = {
    'default': {
        'Statement': [
            {
                'Principal': {
                    'Service': ['ec2.amazonaws.com']
                },
                'Effect': 'Allow',
                'Action': ['sts:AssumeRole']
            }
        ]
    },
    'amazonaws.com.cn': {
        'Statement': [
            {
                'Principal': {
                    'Service': ['ec2.amazonaws.com.cn']
                },
                'Effect': 'Allow',
                'Action': ['sts:AssumeRole']
            }
        ]
    },
}
# For backward-compatibility, we'll preserve this here.
ASSUME_ROLE_POLICY_DOCUMENT = json.dumps(DEFAULT_POLICY_DOCUMENTS['default'])


class IAMConnection(AWSQueryConnection):

    APIVersion = '2010-05-08'

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, host='iam.amazonaws.com',
                 debug=0, https_connection_factory=None, path='/', anon=False,
                 security_token=None, validate_certs=True, profile_name=None):
        """
        :type anon: boolean
        :param anon: If this parameter is True, the ``IAMConnection`` object
            will make anonymous requests.
        """
        self.anon = anon
        super(IAMConnection, self).__init__(aws_access_key_id,
                                            aws_secret_access_key,
                                            is_secure, port, proxy,
                                            proxy_port, proxy_user, proxy_pass,
                                            host, debug, https_connection_factory,
                                            path, security_token,
                                            validate_certs=validate_certs,
                                            profile_name=profile_name)

    def _required_auth_capability(self):
        if self.anon:
            return ['query-anon']
        else:
            return ['hmac-v4']

    def get_response(self, action, params, path='/', parent=None,
                     verb='POST', list_marker='Set'):
        """
        Utility method to handle calls to IAM and parsing of responses.
        """
        if not parent:
            parent = self
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            if body:
                e = boto.jsonresponse.Element(list_marker=list_marker,
                                              pythonize_name=True)
                h = boto.jsonresponse.XmlHandler(e, parent)
                h.parse(body)
                return e
            else:
                # Support empty responses, e.g. deleting a SAML provider
                # according to the official documentation.
                return {}
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

    def get_rbac_response(self, action, params, path='/', verb='POST'):
        """
        Utility method to handle calls to IAM and parsing of responses.
        """
        import xml.dom.minidom
        self.APIVersion = None
        response = self.make_request(action, params, path, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == 200:
            if body:
                xml_str = xml.dom.minidom.parseString(body)
                prettyxml = xml_str.toprettyxml()
                return prettyxml
            else:
                # Support empty responses, e.g. deleting a SAML provider
                # according to the official documentation.
                return {}
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error('%s' % body)
            raise self.ResponseError(response.status, response.reason, body)

    #
    # Group methods
    #

    def get_all_groups(self, path_prefix='/', marker=None, max_items=None):
        """
        List the groups that have the specified path prefix.

        :type path_prefix: string
        :param path_prefix: If provided, only groups whose paths match
            the provided prefix will be returned.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {}
        if path_prefix:
            params['PathPrefix'] = path_prefix
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListGroups', params,
                                 list_marker='Groups')

    def get_group(self, group_name, marker=None, max_items=None):
        """
        Return a list of users that are in the specified group.

        :type group_name: string
        :param group_name: The name of the group whose information should
                           be returned.
        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'GroupName': group_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('GetGroup', params, list_marker='Users')

    def create_group(self, group_name, path='/'):
        """
        Create a group.

        :type group_name: string
        :param group_name: The name of the new group

        :type path: string
        :param path: The path to the group (Optional).  Defaults to /.

        """
        params = {'GroupName': group_name,
                  'Path': path}
        return self.get_response('CreateGroup', params)

    def delete_group(self, group_name):
        """
        Delete a group. The group must not contain any Users or
        have any attached policies

        :type group_name: string
        :param group_name: The name of the group to delete.

        """
        params = {'GroupName': group_name}
        return self.get_response('DeleteGroup', params)

    def update_group(self, group_name, new_group_name=None, new_path=None):
        """
        Updates name and/or path of the specified group.

        :type group_name: string
        :param group_name: The name of the new group

        :type new_group_name: string
        :param new_group_name: If provided, the name of the group will be
            changed to this name.

        :type new_path: string
        :param new_path: If provided, the path of the group will be
            changed to this path.

        """
        params = {'GroupName': group_name}
        if new_group_name:
            params['NewGroupName'] = new_group_name
        if new_path:
            params['NewPath'] = new_path
        return self.get_response('UpdateGroup', params)

    def add_user_to_group(self, group_name, user_name):
        """
        Add a user to a group

        :type group_name: string
        :param group_name: The name of the group

        :type user_name: string
        :param user_name: The to be added to the group.

        """
        params = {'GroupName': group_name,
                  'UserName': user_name}
        return self.get_response('AddUserToGroup', params)

    def remove_user_from_group(self, group_name, user_name):
        """
        Remove a user from a group.

        :type group_name: string
        :param group_name: The name of the group

        :type user_name: string
        :param user_name: The user to remove from the group.

        """
        params = {'GroupName': group_name,
                  'UserName': user_name}
        return self.get_response('RemoveUserFromGroup', params)

    def put_group_policy(self, group_name, policy_name, policy_json):
        """
        Adds or updates the specified policy document for the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        :type policy_json: string
        :param policy_json: The policy document.

        """
        params = {'GroupName': group_name,
                  'PolicyName': policy_name,
                  'PolicyDocument': policy_json}
        return self.get_response('PutGroupPolicy', params, verb='POST')

    def get_all_group_policies(self, group_name, marker=None, max_items=None):
        """
        List the names of the policies associated with the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'GroupName': group_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListGroupPolicies', params,
                                 list_marker='PolicyNames')

    def get_group_policy(self, group_name, policy_name):
        """
        Retrieves the specified policy document for the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        """
        params = {'GroupName': group_name,
                  'PolicyName': policy_name}
        return self.get_response('GetGroupPolicy', params, verb='POST')

    def delete_group_policy(self, group_name, policy_name):
        """
        Deletes the specified policy document for the specified group.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to delete.

        """
        params = {'GroupName': group_name,
                  'PolicyName': policy_name}
        return self.get_response('DeleteGroupPolicy', params, verb='POST')

    def get_all_users(self, path_prefix='/', marker=None, max_items=None):
        """
        List the users that have the specified path prefix.

        :type path_prefix: string
        :param path_prefix: If provided, only users whose paths match
            the provided prefix will be returned.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'PathPrefix': path_prefix}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListUsers', params, list_marker='Users')

    #
    # User methods
    #

    def create_user(self, user_name, path='/'):
        """
        Create a user.

        :type user_name: string
        :param user_name: The name of the new user

        :type path: string
        :param path: The path in which the user will be created.
            Defaults to /.

        """
        params = {'UserName': user_name,
                  'Path': path}
        return self.get_response('CreateUser', params)

    def delete_user(self, user_name):
        """
        Delete a user including the user's path, GUID and ARN.

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The name of the user to delete.

        """
        params = {'UserName': user_name}
        return self.get_response('DeleteUser', params)

    def get_user(self, user_name=None):
        """
        Retrieve information about the specified user.

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The name of the user to retrieve.
            If not specified, defaults to user making request.
        """
        params = {}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('GetUser', params)

    def update_user(self, user_name, new_user_name=None, new_path=None):
        """
        Updates name and/or path of the specified user.

        :type user_name: string
        :param user_name: The name of the user

        :type new_user_name: string
        :param new_user_name: If provided, the username of the user will be
            changed to this username.

        :type new_path: string
        :param new_path: If provided, the path of the user will be
            changed to this path.

        """
        params = {'UserName': user_name}
        if new_user_name:
            params['NewUserName'] = new_user_name
        if new_path:
            params['NewPath'] = new_path
        return self.get_response('UpdateUser', params)

    def get_all_user_policies(self, user_name, marker=None, max_items=None):
        """
        List the names of the policies associated with the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListUserPolicies', params,
                                 list_marker='PolicyNames')

    def put_user_policy(self, user_name, policy_name, policy_json):
        """
        Adds or updates the specified policy document for the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        :type policy_json: string
        :param policy_json: The policy document.

        """
        params = {'UserName': user_name,
                  'PolicyName': policy_name,
                  'PolicyDocument': policy_json}
        return self.get_response('PutUserPolicy', params, verb='POST')

    def get_user_policy(self, user_name, policy_name):
        """
        Retrieves the specified policy document for the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to get.

        """
        params = {'UserName': user_name,
                  'PolicyName': policy_name}
        return self.get_response('GetUserPolicy', params, verb='POST')

    def delete_user_policy(self, user_name, policy_name):
        """
        Deletes the specified policy document for the specified user.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type policy_name: string
        :param policy_name: The policy document to delete.

        """
        params = {'UserName': user_name,
                  'PolicyName': policy_name}
        return self.get_response('DeleteUserPolicy', params, verb='POST')

    def get_groups_for_user(self, user_name, marker=None, max_items=None):
        """
        List the groups that a specified user belongs to.

        :type user_name: string
        :param user_name: The name of the user to list groups for.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListGroupsForUser', params,
                                 list_marker='Groups')

    #
    # Access Keys
    #

    def get_all_access_keys(self, user_name, marker=None, max_items=None):
        """
        Get all access keys associated with an account.

        :type user_name: string
        :param user_name: The username of the user

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.
        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListAccessKeys', params,
                                 list_marker='AccessKeyMetadata')

    def create_access_key(self, user_name=None):
        """
        Create a new AWS Secret Access Key and corresponding AWS Access Key ID
        for the specified user.  The default status for new keys is Active

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'UserName': user_name}
        return self.get_response('CreateAccessKey', params)

    def update_access_key(self, access_key_id, status, user_name=None):
        """
        Changes the status of the specified access key from Active to Inactive
        or vice versa.  This action can be used to disable a user's key as
        part of a key rotation workflow.

        If the user_name is not specified, the user_name is determined
        implicitly based on the AWS Access Key ID used to sign the request.

        :type access_key_id: string
        :param access_key_id: The ID of the access key.

        :type status: string
        :param status: Either Active or Inactive.

        :type user_name: string
        :param user_name: The username of user (optional).

        """
        params = {'AccessKeyId': access_key_id,
                  'Status': status}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('UpdateAccessKey', params)

    def delete_access_key(self, access_key_id, user_name=None):
        """
        Delete an access key associated with a user.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type access_key_id: string
        :param access_key_id: The ID of the access key to be deleted.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'AccessKeyId': access_key_id}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('DeleteAccessKey', params)

    #
    # Signing Certificates
    #

    def get_all_signing_certs(self, marker=None, max_items=None,
                              user_name=None):
        """
        Get all signing certificates associated with an account.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        if user_name:
            params['UserName'] = user_name
        return self.get_response('ListSigningCertificates',
                                 params, list_marker='Certificates')

    def update_signing_cert(self, cert_id, status, user_name=None):
        """
        Change the status of the specified signing certificate from
        Active to Inactive or vice versa.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type cert_id: string
        :param cert_id: The ID of the signing certificate

        :type status: string
        :param status: Either Active or Inactive.

        :type user_name: string
        :param user_name: The username of the user
        """
        params = {'CertificateId': cert_id,
                  'Status': status}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('UpdateSigningCertificate', params)

    def upload_signing_cert(self, cert_body, user_name=None):
        """
        Uploads an X.509 signing certificate and associates it with
        the specified user.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type cert_body: string
        :param cert_body: The body of the signing certificate.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'CertificateBody': cert_body}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('UploadSigningCertificate', params,
                                 verb='POST')

    def delete_signing_cert(self, cert_id, user_name=None):
        """
        Delete a signing certificate associated with a user.

        If the user_name is not specified, it is determined implicitly based
        on the AWS Access Key ID used to sign the request.

        :type user_name: string
        :param user_name: The username of the user

        :type cert_id: string
        :param cert_id: The ID of the certificate.

        """
        params = {'CertificateId': cert_id}
        if user_name:
            params['UserName'] = user_name
        return self.get_response('DeleteSigningCertificate', params)

    #
    # Server Certificates
    #

    def list_server_certs(self, path_prefix='/',
                          marker=None, max_items=None):
        """
        Lists the server certificates that have the specified path prefix.
        If none exist, the action returns an empty list.

        :type path_prefix: string
        :param path_prefix: If provided, only certificates whose paths match
            the provided prefix will be returned.

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.

        """
        params = {}
        if path_prefix:
            params['PathPrefix'] = path_prefix
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListServerCertificates',
                                 params,
                                 list_marker='ServerCertificateMetadataList')

    # Preserves backwards compatibility.
    # TODO: Look into deprecating this eventually?
    get_all_server_certs = list_server_certs

    def update_server_cert(self, cert_name, new_cert_name=None,
                           new_path=None):
        """
        Updates the name and/or the path of the specified server certificate.

        :type cert_name: string
        :param cert_name: The name of the server certificate that you want
            to update.

        :type new_cert_name: string
        :param new_cert_name: The new name for the server certificate.
            Include this only if you are updating the
            server certificate's name.

        :type new_path: string
        :param new_path: If provided, the path of the certificate will be
                         changed to this path.
        """
        params = {'ServerCertificateName': cert_name}
        if new_cert_name:
            params['NewServerCertificateName'] = new_cert_name
        if new_path:
            params['NewPath'] = new_path
        return self.get_response('UpdateServerCertificate', params)

    def upload_server_cert(self, cert_name, cert_body, private_key,
                           cert_chain=None, path=None):
        """
        Uploads a server certificate entity for the AWS Account.
        The server certificate entity includes a public key certificate,
        a private key, and an optional certificate chain, which should
        all be PEM-encoded.

        :type cert_name: string
        :param cert_name: The name for the server certificate. Do not
            include the path in this value.

        :type cert_body: string
        :param cert_body: The contents of the public key certificate
            in PEM-encoded format.

        :type private_key: string
        :param private_key: The contents of the private key in
            PEM-encoded format.

        :type cert_chain: string
        :param cert_chain: The contents of the certificate chain. This
            is typically a concatenation of the PEM-encoded
            public key certificates of the chain.

        :type path: string
        :param path: The path for the server certificate.
        """
        params = {'ServerCertificateName': cert_name,
                  'CertificateBody': cert_body,
                  'PrivateKey': private_key}
        if cert_chain:
            params['CertificateChain'] = cert_chain
        if path:
            params['Path'] = path
        return self.get_response('UploadServerCertificate', params,
                                 verb='POST')

    def get_server_certificate(self, cert_name):
        """
        Retrieves information about the specified server certificate.

        :type cert_name: string
        :param cert_name: The name of the server certificate you want
            to retrieve information about.

        """
        params = {'ServerCertificateName': cert_name}
        return self.get_response('GetServerCertificate', params)

    def delete_server_cert(self, cert_name):
        """
        Delete the specified server certificate.

        :type cert_name: string
        :param cert_name: The name of the server certificate you want
            to delete.

        """
        params = {'ServerCertificateName': cert_name}
        return self.get_response('DeleteServerCertificate', params)

    #
    # MFA Devices
    #

    def get_all_mfa_devices(self, user_name, marker=None, max_items=None):
        """
        Get all MFA devices associated with an account.

        :type user_name: string
        :param user_name: The username of the user

        :type marker: string
        :param marker: Use this only when paginating results and only
            in follow-up request after you've received a response
            where the results are truncated.  Set this to the value of
            the Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this only when paginating results to indicate
            the maximum number of groups you want in the response.

        """
        params = {'UserName': user_name}
        if marker:
            params['Marker'] = marker
        if max_items:
            params['MaxItems'] = max_items
        return self.get_response('ListMFADevices',
                                 params, list_marker='MFADevices')

    def enable_mfa_device(self, user_name, serial_number,
                          auth_code_1, auth_code_2):
        """
        Enables the specified MFA device and associates it with the
        specified user.

        :type user_name: string
        :param user_name: The username of the user

        :type serial_number: string
        :param serial_number: The serial number which uniquely identifies
            the MFA device.

        :type auth_code_1: string
        :param auth_code_1: An authentication code emitted by the device.

        :type auth_code_2: string
        :param auth_code_2: A subsequent authentication code emitted
            by the device.

        """
        params = {'UserName': user_name,
                  'SerialNumber': serial_number,
                  'AuthenticationCode1': auth_code_1,
                  'AuthenticationCode2': auth_code_2}
        return self.get_response('EnableMFADevice', params)

    def deactivate_mfa_device(self, user_name, serial_number):
        """
        Deactivates the specified MFA device and removes it from
        association with the user.

        :type user_name: string
        :param user_name: The username of the user

        :type serial_number: string
        :param serial_number: The serial number which uniquely identifies
            the MFA device.

        """
        params = {'UserName': user_name,
                  'SerialNumber': serial_number}
        return self.get_response('DeactivateMFADevice', params)

    def resync_mfa_device(self, user_name, serial_number,
                          auth_code_1, auth_code_2):
        """
        Syncronizes the specified MFA device with the AWS servers.

        :type user_name: string
        :param user_name: The username of the user

        :type serial_number: string
        :param serial_number: The serial number which uniquely identifies
            the MFA device.

        :type auth_code_1: string
        :param auth_code_1: An authentication code emitted by the device.

        :type auth_code_2: string
        :param auth_code_2: A subsequent authentication code emitted
            by the device.

        """
        params = {'UserName': user_name,
                  'SerialNumber': serial_number,
                  'AuthenticationCode1': auth_code_1,
                  'AuthenticationCode2': auth_code_2}
        return self.get_response('ResyncMFADevice', params)

    #
    # Login Profiles
    #

    def get_login_profiles(self, user_name):
        """
        Retrieves the login profile for the specified user.

        :type user_name: string
        :param user_name: The username of the user

        """
        params = {'UserName': user_name}
        return self.get_response('GetLoginProfile', params)

    def create_login_profile(self, user_name, password):
        """
        Creates a login profile for the specified user, give the user the
        ability to access AWS services and the AWS Management Console.

        :type user_name: string
        :param user_name: The name of the user

        :type password: string
        :param password: The new password for the user

        """
        params = {'UserName': user_name,
                  'Password': password}
        return self.get_response('CreateLoginProfile', params)

    def delete_login_profile(self, user_name):
        """
        Deletes the login profile associated with the specified user.

        :type user_name: string
        :param user_name: The name of the user to delete.

        """
        params = {'UserName': user_name}
        return self.get_response('DeleteLoginProfile', params)

    def update_login_profile(self, user_name, password):
        """
        Resets the password associated with the user's login profile.

        :type user_name: string
        :param user_name: The name of the user

        :type password: string
        :param password: The new password for the user

        """
        params = {'UserName': user_name,
                  'Password': password}
        return self.get_response('UpdateLoginProfile', params)

    def create_account_alias(self, alias):
        """
        Creates a new alias for the AWS account.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G

        :type alias: string
        :param alias: The alias to attach to the account.
        """
        params = {'AccountAlias': alias}
        return self.get_response('CreateAccountAlias', params)

    def delete_account_alias(self, alias):
        """
        Deletes an alias for the AWS account.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G

        :type alias: string
        :param alias: The alias to remove from the account.
        """
        params = {'AccountAlias': alias}
        return self.get_response('DeleteAccountAlias', params)

    def get_account_alias(self):
        """
        Get the alias for the current account.

        This is referred to in the docs as list_account_aliases,
        but it seems you can only have one account alias currently.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G
        """
        return self.get_response('ListAccountAliases', {},
                                 list_marker='AccountAliases')

    def get_signin_url(self, service='ec2'):
        """
        Get the URL where IAM users can use their login profile to sign in
        to this account's console.

        :type service: string
        :param service: Default service to go to in the console.
        """
        alias = self.get_account_alias()

        if not alias:
            raise Exception('No alias associated with this account.  Please use iam.create_account_alias() first.')

        resp = alias.get('list_account_aliases_response', {})
        result = resp.get('list_account_aliases_result', {})
        aliases = result.get('account_aliases', [])

        if not len(aliases):
            raise Exception('No alias associated with this account.  Please use iam.create_account_alias() first.')

        # We'll just use the first one we find.
        alias = aliases[0]

        if self.host == 'iam.us-gov.amazonaws.com':
            return "https://%s.signin.amazonaws-us-gov.com/console/%s" % (
                alias,
                service
            )
        elif self.host.endswith('amazonaws.com.cn'):
            return "https://%s.signin.amazonaws.cn/console/%s" % (
                alias,
                service
            )
        else:
            return "https://%s.signin.aws.amazon.com/console/%s" % (
                alias,
                service
            )

    def get_account_summary(self):
        """
        Get the alias for the current account.

        This is referred to in the docs as list_account_aliases,
        but it seems you can only have one account alias currently.

        For more information on account id aliases, please see
        http://goo.gl/ToB7G
        """
        return self.get_object('GetAccountSummary', {}, SummaryMap)

    #
    # IAM Roles
    #

    def add_role_to_instance_profile(self, instance_profile_name, role_name):
        """
        Adds the specified role to the specified instance profile.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to update.

        :type role_name: string
        :param role_name: Name of the role to add.
        """
        return self.get_response('AddRoleToInstanceProfile',
                                 {'InstanceProfileName': instance_profile_name,
                                  'RoleName': role_name})

    def create_instance_profile(self, instance_profile_name, path=None):
        """
        Creates a new instance profile.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to create.

        :type path: string
        :param path: The path to the instance profile.
        """
        params = {'InstanceProfileName': instance_profile_name}
        if path is not None:
            params['Path'] = path
        return self.get_response('CreateInstanceProfile', params)

    def _build_policy(self, assume_role_policy_document=None):
        if assume_role_policy_document is not None:
            if isinstance(assume_role_policy_document, six.string_types):
                # Historically, they had to pass a string. If it's a string,
                # assume the user has already handled it.
                return assume_role_policy_document
        else:

            for tld, policy in DEFAULT_POLICY_DOCUMENTS.items():
                if tld is 'default':
                    # Skip the default. We'll fall back to it if we don't find
                    # anything.
                    continue

                if self.host and self.host.endswith(tld):
                    assume_role_policy_document = policy
                    break

            if not assume_role_policy_document:
                assume_role_policy_document = DEFAULT_POLICY_DOCUMENTS['default']

        # Dump the policy (either user-supplied ``dict`` or one of the defaults)
        return json.dumps(assume_role_policy_document)

    def create_role(self, role_name, assume_role_policy_document=None, path=None,
                    description=None, max_session_duration=None, tags=None):
        """
        Creates a new role for your AWS account.

        The policy grants permission to an EC2 instance to assume the role.
        The policy is URL-encoded according to RFC 3986. Currently, only EC2
        instances can assume roles.

        :type role_name: string
        :param role_name: Name of the role to create.

        :type assume_role_policy_document: ``string`` or ``dict``
        :param assume_role_policy_document: The policy that grants an entity
            permission to assume the role.

        :type path: string
        :param path: The path to the role.

        :type description: string
        :param description: A description of the role

        :type max_session_duration: int or string
        :param max_session_duration: The maximum session duration (in seconds)
               that you want to set for the specified role. If you do not
               specify a value for this setting, the default maximum of one
               hour is applied. This setting can have a value from 1 hour to
               12 hours.
               Anyone who assumes the role from the AWS CLI or API can use the
               DurationSeconds API parameter or the duration-seconds CLI
               parameter to request a longer session. The MaxSessionDuration
               setting determines the maximum duration that can be requested
               using the DurationSeconds parameter. If users don't specify a
               value for the DurationSeconds parameter, their security
               credentials are valid for one hour by default. This applies
               when you use the AssumeRole* API operations or the assume-role*
               CLI operations but does not apply when you use those operations
               to create a console URL. For more information, see Using IAM
               Roles in the IAM User Guide.

        :type tags: dict of key values
        :param tags: A dictionary of tags that you want to attach to the newly
               created role. Each tag consists of a key name and an associated
               value. For more information about tagging, see Tagging IAM
               Identities in the IAM User Guide.
        """
        params = {
            'RoleName': role_name,
            'AssumeRolePolicyDocument': self._build_policy(
                assume_role_policy_document
            ),
        }
        if path is not None:
            params['Path'] = path
        if description is not None:
            params['Description'] = description
        if max_session_duration is not None:
            params['MaxSessionDuration'] = max_session_duration
        if tags is not None:
            idx = 1
            for k, v in tags.items():
                params['Tags.member.%d.Key' % idx] = k
                params['Tags.member.%d.Value' % idx] = v
                idx += 1
        return self.get_response('CreateRole', params, list_marker='Tags')

    def delete_instance_profile(self, instance_profile_name):
        """
        Deletes the specified instance profile. The instance profile must not
        have an associated role.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to delete.
        """
        return self.get_response(
            'DeleteInstanceProfile',
            {'InstanceProfileName': instance_profile_name})

    def delete_role(self, role_name):
        """
        Deletes the specified role. The role must not have any policies
        attached.

        :type role_name: string
        :param role_name: Name of the role to delete.
        """
        return self.get_response('DeleteRole', {'RoleName': role_name})

    def delete_role_policy(self, role_name, policy_name):
        """
        Deletes the specified policy associated with the specified role.

        :type role_name: string
        :param role_name: Name of the role associated with the policy.

        :type policy_name: string
        :param policy_name: Name of the policy to delete.
        """
        return self.get_response(
            'DeleteRolePolicy',
            {'RoleName': role_name, 'PolicyName': policy_name})

    def get_instance_profile(self, instance_profile_name):
        """
        Retrieves information about the specified instance profile, including
        the instance profile's path, GUID, ARN, and role.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to get
            information about.
        """
        return self.get_response('GetInstanceProfile',
                                 {'InstanceProfileName': instance_profile_name})

    def get_role(self, role_name):
        """
        Retrieves information about the specified role, including the role's
        path, GUID, ARN, and the policy granting permission to EC2 to assume
        the role.

        :type role_name: string
        :param role_name: Name of the role associated with the policy.
        """
        return self.get_response('GetRole', {'RoleName': role_name}, list_marker='Tags')

    def get_role_policy(self, role_name, policy_name):
        """
        Retrieves the specified policy document for the specified role.

        :type role_name: string
        :param role_name: Name of the role associated with the policy.

        :type policy_name: string
        :param policy_name: Name of the policy to get.
        """
        return self.get_response('GetRolePolicy',
                                 {'RoleName': role_name,
                                  'PolicyName': policy_name})

    def list_instance_profiles(self, path_prefix=None, marker=None,
                               max_items=None):
        """
        Lists the instance profiles that have the specified path prefix. If
        there are none, the action returns an empty list.

        :type path_prefix: string
        :param path_prefix: The path prefix for filtering the results. For
            example: /application_abc/component_xyz/, which would get all
            instance profiles whose path starts with
            /application_abc/component_xyz/.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items

        return self.get_response('ListInstanceProfiles', params,
                                 list_marker='InstanceProfiles')

    def list_instance_profiles_for_role(self, role_name, marker=None,
                                        max_items=None):
        """
        Lists the instance profiles that have the specified associated role. If
        there are none, the action returns an empty list.

        :type role_name: string
        :param role_name: The name of the role to list instance profiles for.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            Marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {'RoleName': role_name}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListInstanceProfilesForRole', params,
                                 list_marker='InstanceProfiles')

    def list_role_policies(self, role_name, marker=None, max_items=None):
        """
        Lists the names of the policies associated with the specified role. If
        there are none, the action returns an empty list.

        :type role_name: string
        :param role_name: The name of the role to list policies for.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {'RoleName': role_name}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListRolePolicies', params,
                                 list_marker='PolicyNames')

    def list_role_tags(self, role_name, marker=None, max_items=None):
        """
        Lists the tags that are attached to the specified role. The returned
        list of tags is sorted by tag key. For more information about tagging,
        see Tagging IAM Identities in the IAM User Guide.

        :type role_name: string
        :param role_name: The name of the IAM role for which you want to see
            the list of tags.

        :type marker: string
        :param marker: Use this parameter only when paginating results and
            only after you receive a response indicating that the results are
            truncated. Set it to the value of the Marker element in the
            response that you received to indicate where the next call should
            start.

        :type max_items: string
        :param max_items: Use this only when paginating results to indicate
            the maximum number of items that you want in the response. If
            additional items exist beyond the maximum that you specify, the
            IsTruncated response element is true.
            If you do not include this parameter, it defaults to 100. Note
            that IAM might return fewer results, even when more results are
            available. In that case, the IsTruncated response element returns
            true, and Marker contains a value to include in the subsequent
            call that tells the service where to continue from.
        """
        params = {'RoleName': role_name}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListRoleTags', params, list_marker='Tags')

    def list_roles(self, path_prefix=None, marker=None, max_items=None):
        """
        Lists the roles that have the specified path prefix. If there are none,
        the action returns an empty list.

        :type path_prefix: string
        :param path_prefix: The path prefix for filtering the results.

        :type marker: string
        :param marker: Use this parameter only when paginating results, and
            only in a subsequent request after you've received a response
            where the results are truncated. Set it to the value of the
            marker element in the response you just received.

        :type max_items: int
        :param max_items: Use this parameter only when paginating results to
            indicate the maximum number of user names you want in the response.
        """
        params = {}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListRoles', params, list_marker='Roles')

    def put_role_policy(self, role_name, policy_name, policy_document):
        """
        Adds (or updates) a policy document associated with the specified role.

        :type role_name: string
        :param role_name: Name of the role to associate the policy with.

        :type policy_name: string
        :param policy_name: Name of the policy document.

        :type policy_document: string
        :param policy_document: The policy document.
        """
        return self.get_response('PutRolePolicy',
                                 {'RoleName': role_name,
                                  'PolicyName': policy_name,
                                  'PolicyDocument': policy_document})

    def remove_role_from_instance_profile(self, instance_profile_name,
                                          role_name):
        """
        Removes the specified role from the specified instance profile.

        :type instance_profile_name: string
        :param instance_profile_name: Name of the instance profile to update.

        :type role_name: string
        :param role_name: Name of the role to remove.
        """
        return self.get_response('RemoveRoleFromInstanceProfile',
                                 {'InstanceProfileName': instance_profile_name,
                                  'RoleName': role_name})

    def tag_role(self, role_name, tags):
        """
        Adds one or more tags to an IAM role. The role can be a regular role
        or a service-linked role. If a tag with the same key name already
        exists, then that tag is overwritten with the new value.

        :type role_name: string
        :param role_name: Name of the role to tag.

        :type tags: dict of key values
        :param tags: A dictionary of tags that you want to attach to the role. Each
            tag consists of a key name and an associated value. For more
            information about tagging, see Tagging IAM Identities in the IAM
            User Guide.
        """
        params = {'RoleName': role_name}
        idx = 1
        for k, v in tags.items():
            params['Tags.member.%d.Key' % idx] = k
            params['Tags.member.%d.Value' % idx] = v
            idx += 1
        return self.get_response('TagRole', params)

    def untag_role(self, role_name, tag_keys):
        """
        Removes the specified tags from the role. For more information about
        tagging, see Tagging IAM Identities in the IAM User Guide.

        :type role_name: string
        :param role_name: Name of the role to tag.

        :type tag_keys: list of tag key names
        :param tag_keys: A list of tags key names that you want to remove from
            a role. The tags with matching keys are removed from the specified
            role.
        """
        params = {'RoleName': role_name}
        idx = 1
        for k in tag_keys:
            params['TagKeys.member.%d' % idx] = k
            idx += 1
        return self.get_response('UntagRole', params)

    def update_role(self, role_name, description=None, max_session_duration=None):
        """
        Update role description and/or max session duration.

        :type role_name: string
        :param role_name: Name of the role to update.

        :type description: string
        :param description: The new description that you want to apply to the
               specified role.

        :type max_session_duration: int or string
        :param max_session_duration: The maximum session duration (in seconds)
               that you want to set for the specified role. If you do not
               specify a value for this setting, the default maximum of one
               hour is applied. This setting can have a value from 1 hour to
               12 hours.
               Anyone who assumes the role from the AWS CLI or API can use the
               DurationSeconds API parameter or the duration-seconds CLI
               parameter to request a longer session. The MaxSessionDuration
               setting determines the maximum duration that can be requested
               using the DurationSeconds parameter. If users don't specify a
               value for the DurationSeconds parameter, their security
               credentials are valid for one hour by default. This applies
               when you use the AssumeRole* API operations or the assume-role*
               CLI operations but does not apply when you use those operations
               to create a console URL. For more information, see Using IAM
               Roles in the IAM User Guide.
        """
        params = {'RoleName': role_name}
        if description:
            params['Description'] = description
        if max_session_duration:
            params['MaxSessionDuration'] = max_session_duration
        return self.get_response('UpdateRole', params)

    def update_role_description(self, role_name, description):
        """
        Update role description.

        :type role_name: string
        :param role_name: Name of the role to update.

        :type description: string
        :param description: The new description that you want to apply to the
               specified role.
        """
        params = {'RoleName': role_name, 'Description' : description}
        return self.get_response('UpdateRoleDescription', params)

    def update_assume_role_policy(self, role_name, policy_document):
        """
        Updates the policy that grants an entity permission to assume a role.
        Currently, only an Amazon EC2 instance can assume a role.

        :type role_name: string
        :param role_name: Name of the role to update.

        :type policy_document: string
        :param policy_document: The policy that grants an entity permission to
            assume the role.
        """
        return self.get_response('UpdateAssumeRolePolicy',
                                 {'RoleName': role_name,
                                  'PolicyDocument': policy_document})

    def create_saml_provider(self, saml_metadata_document, name):
        """
        Creates an IAM entity to describe an identity provider (IdP)
        that supports SAML 2.0.

        The SAML provider that you create with this operation can be
        used as a principal in a role's trust policy to establish a
        trust relationship between AWS and a SAML identity provider.
        You can create an IAM role that supports Web-based single
        sign-on (SSO) to the AWS Management Console or one that
        supports API access to AWS.

        When you create the SAML provider, you upload an a SAML
        metadata document that you get from your IdP and that includes
        the issuer's name, expiration information, and keys that can
        be used to validate the SAML authentication response
        (assertions) that are received from the IdP. You must generate
        the metadata document using the identity management software
        that is used as your organization's IdP.
        This operation requires `Signature Version 4`_.
        For more information, see `Giving Console Access Using SAML`_
        and `Creating Temporary Security Credentials for SAML
        Federation`_ in the Using Temporary Credentials guide.

        :type saml_metadata_document: string
        :param saml_metadata_document: An XML document generated by an identity
            provider (IdP) that supports SAML 2.0. The document includes the
            issuer's name, expiration information, and keys that can be used to
            validate the SAML authentication response (assertions) that are
            received from the IdP. You must generate the metadata document
            using the identity management software that is used as your
            organization's IdP.
        For more information, see `Creating Temporary Security Credentials for
            SAML Federation`_ in the Using Temporary Security Credentials
            guide.

        :type name: string
        :param name: The name of the provider to create.

        """
        params = {
            'SAMLMetadataDocument': saml_metadata_document,
            'Name': name,
        }
        return self.get_response('CreateSAMLProvider', params)

    def list_saml_providers(self):
        """
        Lists the SAML providers in the account.
        This operation requires `Signature Version 4`_.
        """
        return self.get_response('ListSAMLProviders', {}, list_marker='SAMLProviderList')

    def get_saml_provider(self, saml_provider_arn):
        """
        Returns the SAML provider metadocument that was uploaded when
        the provider was created or updated.
        This operation requires `Signature Version 4`_.

        :type saml_provider_arn: string
        :param saml_provider_arn: The Amazon Resource Name (ARN) of the SAML
            provider to get information about.

        """
        params = {'SAMLProviderArn': saml_provider_arn}
        return self.get_response('GetSAMLProvider', params)

    def update_saml_provider(self, saml_provider_arn, saml_metadata_document):
        """
        Updates the metadata document for an existing SAML provider.
        This operation requires `Signature Version 4`_.

        :type saml_provider_arn: string
        :param saml_provider_arn: The Amazon Resource Name (ARN) of the SAML
            provider to update.

        :type saml_metadata_document: string
        :param saml_metadata_document: An XML document generated by an identity
            provider (IdP) that supports SAML 2.0. The document includes the
            issuer's name, expiration information, and keys that can be used to
            validate the SAML authentication response (assertions) that are
            received from the IdP. You must generate the metadata document
            using the identity management software that is used as your
            organization's IdP.

        """
        params = {
            'SAMLMetadataDocument': saml_metadata_document,
            'SAMLProviderArn': saml_provider_arn,
        }
        return self.get_response('UpdateSAMLProvider', params)

    def delete_saml_provider(self, saml_provider_arn):
        """
        Deletes a SAML provider.

        Deleting the provider does not update any roles that reference
        the SAML provider as a principal in their trust policies. Any
        attempt to assume a role that references a SAML provider that
        has been deleted will fail.
        This operation requires `Signature Version 4`_.

        :type saml_provider_arn: string
        :param saml_provider_arn: The Amazon Resource Name (ARN) of the SAML
            provider to delete.

        """
        params = {'SAMLProviderArn': saml_provider_arn}
        return self.get_response('DeleteSAMLProvider', params)

    #
    # IAM Reports
    #

    def generate_credential_report(self):
        """
        Generates a credential report for an account

        A new credential report can only be generated every 4 hours. If one
        hasn't been generated in the last 4 hours then get_credential_report
        will error when called
        """
        params = {}
        return self.get_response('GenerateCredentialReport', params)

    def get_credential_report(self):
        """
        Retrieves a credential report for an account

        A report must have been generated in the last 4 hours to succeed.
        The report is returned as a base64 encoded blob within the response.
        """
        params = {}
        return self.get_response('GetCredentialReport', params)

    def create_virtual_mfa_device(self, path, device_name):
        """
        Creates a new virtual MFA device for the AWS account.

        After creating the virtual MFA, use enable-mfa-device to
        attach the MFA device to an IAM user.

        :type path: string
        :param path: The path for the virtual MFA device.

        :type device_name: string
        :param device_name: The name of the virtual MFA device.
            Used with path to uniquely identify a virtual MFA device.

        """
        params = {
            'Path': path,
            'VirtualMFADeviceName': device_name
        }
        return self.get_response('CreateVirtualMFADevice', params)

    #
    # IAM password policy
    #

    def get_account_password_policy(self):
        """
        Returns the password policy for the AWS account.
        """
        params = {}
        return self.get_response('GetAccountPasswordPolicy', params)

    def delete_account_password_policy(self):
        """
        Delete the password policy currently set for the AWS account.
        """
        params = {}
        return self.get_response('DeleteAccountPasswordPolicy', params)

    def update_account_password_policy(self, allow_users_to_change_password=None,
                                        hard_expiry=None, max_password_age=None ,
                                        minimum_password_length=None ,
                                        password_reuse_prevention=None,
                                        require_lowercase_characters=None,
                                        require_numbers=None, require_symbols=None ,
                                        require_uppercase_characters=None):
        """
        Update the password policy for the AWS account.

        Notes: unset parameters will be reset to Amazon default settings!
            Most of the password policy settings are enforced the next time your users
            change their passwords. When you set minimum length and character type
            requirements, they are enforced the next time your users change their
            passwords - users are not forced to change their existing passwords, even
            if the pre-existing passwords do not adhere to the updated password
            policy. When you set a password expiration period, the expiration period
            is enforced immediately.

        :type allow_users_to_change_password: bool
        :param allow_users_to_change_password: Allows all IAM users in your account
            to use the AWS Management Console to change their own passwords.

        :type hard_expiry: bool
        :param hard_expiry: Prevents IAM users from setting a new password after
            their password has expired.

        :type max_password_age: int
        :param max_password_age: The number of days that an IAM user password is valid.

        :type minimum_password_length: int
        :param minimum_password_length: The minimum number of characters allowed in
            an IAM user password.

        :type password_reuse_prevention: int
        :param password_reuse_prevention: Specifies the number of previous passwords
            that IAM users are prevented from reusing.

        :type require_lowercase_characters: bool
        :param require_lowercase_characters: Specifies whether IAM user passwords
            must contain at least one lowercase character from the ISO basic Latin
            alphabet (``a`` to ``z``).

        :type require_numbers: bool
        :param require_numbers: Specifies whether IAM user passwords must contain at
            least one numeric character (``0`` to ``9``).

        :type require_symbols: bool
        :param require_symbols: Specifies whether IAM user passwords must contain at
            least one of the following non-alphanumeric characters:
            ``! @ # $ % ^ & * ( ) _ + - = [ ] { } | '``

        :type require_uppercase_characters: bool
        :param require_uppercase_characters: Specifies whether IAM user passwords
            must contain at least one uppercase character from the ISO basic Latin
            alphabet (``A`` to ``Z``).
        """
        params = {}
        if allow_users_to_change_password is not None and type(allow_users_to_change_password) is bool:
            params['AllowUsersToChangePassword'] = str(allow_users_to_change_password).lower()
        if hard_expiry is not None and type(allow_users_to_change_password) is bool:
            params['HardExpiry'] = str(hard_expiry).lower()
        if max_password_age is not None:
            params['MaxPasswordAge'] = max_password_age
        if minimum_password_length is not None:
            params['MinimumPasswordLength'] = minimum_password_length
        if password_reuse_prevention is not None:
            params['PasswordReusePrevention'] = password_reuse_prevention
        if require_lowercase_characters is not None and type(allow_users_to_change_password) is bool:
            params['RequireLowercaseCharacters'] = str(require_lowercase_characters).lower()
        if require_numbers is not None and type(allow_users_to_change_password) is bool:
            params['RequireNumbers'] = str(require_numbers).lower()
        if require_symbols is not None and type(allow_users_to_change_password) is bool:
            params['RequireSymbols'] = str(require_symbols).lower()
        if require_uppercase_characters is not None and type(allow_users_to_change_password) is bool:
            params['RequireUppercaseCharacters'] = str(require_uppercase_characters).lower()
        return self.get_response('UpdateAccountPasswordPolicy', params)

    def create_policy(self, policy_name, policy_document, path='/',
                      description=None):
        """
        Create a policy.

        :type policy_name: string
        :param policy_name: The name of the new policy

        :type policy_document string
        :param policy_document: The document of the new policy

        :type path: string
        :param path: The path in which the policy will be created.
            Defaults to /.

        :type description: string
        :param path: A description of the new policy.

        """
        params = {'PolicyName': policy_name,
                  'PolicyDocument': policy_document,
                  'Path': path}
        if description is not None:
            params['Description'] = str(description)

        return self.get_response('CreatePolicy', params)

    def create_policy_version(
            self,
            policy_arn,
            policy_document,
            set_as_default=None):
        """
        Create a policy version.

        :type policy_arn: string
        :param policy_arn: The ARN of the policy

        :type policy_document string
        :param policy_document: The document of the new policy version

        :type set_as_default: bool
        :param set_as_default: Sets the policy version as default
            Defaults to None.

        """
        params = {'PolicyArn': policy_arn,
                  'PolicyDocument': policy_document}
        if type(set_as_default) == bool:
            params['SetAsDefault'] = str(set_as_default).lower()
        return self.get_response('CreatePolicyVersion', params)

    def delete_policy(self, policy_arn):
        """
        Delete a policy.

        :type policy_arn: string
        :param policy_arn: The ARN of the policy to delete

        """
        params = {'PolicyArn': policy_arn}
        return self.get_response('DeletePolicy', params)

    def delete_policy_version(self, policy_arn, version_id):
        """
        Delete a policy version.

        :type policy_arn: string
        :param policy_arn: The ARN of the policy to delete a version from

        :type version_id: string
        :param version_id: The id of the version to delete

        """
        params = {'PolicyArn': policy_arn,
                  'VersionId': version_id}
        return self.get_response('DeletePolicyVersion', params)

    def get_policy(self, policy_arn):
        """
        Get policy information.

        :type policy_arn: string
        :param policy_arn: The ARN of the policy to get information for

        """
        params = {'PolicyArn': policy_arn}
        return self.get_response('GetPolicy', params)

    def get_policy_version(self, policy_arn, version_id):
        """
        Get policy information.

        :type policy_arn: string
        :param policy_arn: The ARN of the policy to get information for a
            specific version

        :type version_id: string
        :param version_id: The id of the version to get information for

        """
        params = {'PolicyArn': policy_arn,
                  'VersionId': version_id}
        return self.get_response('GetPolicyVersion', params)

    def list_policies(self, marker=None, max_items=None, only_attached=None,
                      path_prefix=None, scope=None):
        """
        List policies of account.

        :type marker: string
        :param marker: A marker used for pagination (received from previous
            accesses)

        :type max_items: int
        :param max_items: Send only max_items; allows paginations

        :type only_attached: bool
        :param only_attached: Send only policies attached to other resources

        :type path_prefix: string
        :param path_prefix: Send only items prefixed by this path

        :type scope: string
        :param scope: AWS|Local.  Choose between AWS policies or your own
        """
        params = {}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        if type(only_attached) == bool:
            params['OnlyAttached'] = str(only_attached).lower()
        if scope is not None:
            params['Scope'] = scope
        return self.get_response(
            'ListPolicies',
            params,
            list_marker='Policies')

    def list_policy_versions(self, policy_arn, marker=None, max_items=None):
        """
        List policy versions.

        :type policy_arn: string
        :param policy_arn: The ARN of the policy to get versions of

        :type marker: string
        :param marker: A marker used for pagination (received from previous
            accesses)

        :type max_items: int
        :param max_items: Send only max_items; allows paginations

        """
        params = {'PolicyArn': policy_arn}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response(
            'ListPolicyVersions',
            params,
            list_marker='Versions')

    def set_default_policy_version(self, policy_arn, version_id):
        """
        Set default policy version.

        :type policy_arn: string
        :param policy_arn: The ARN of the policy to set the default version
            for

        :type version_id: string
        :param version_id: The id of the version to set as default
        """
        params = {'PolicyArn': policy_arn,
                  'VersionId': version_id}
        return self.get_response('SetDefaultPolicyVersion', params)

    def list_entities_for_policy(self, policy_arn, path_prefix=None,
                                 marker=None, max_items=None,
                                 entity_filter=None):
        """
        :type policy_arn: string
        :param policy_arn: The ARN of the policy to get entities for

        :type marker: string
        :param marker: A marker used for pagination (received from previous
            accesses)

        :type max_items: int
        :param max_items: Send only max_items; allows paginations

        :type path_prefix: string
        :param path_prefix: Send only items prefixed by this path

        :type entity_filter: string
        :param entity_filter: Which entity type of User | Role | Group |
            LocalManagedPolicy | AWSManagedPolicy to return

        """
        params = {'PolicyArn': policy_arn}
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if entity_filter is not None:
            params['EntityFilter'] = entity_filter
        return self.get_response('ListEntitiesForPolicy', params,
                                 list_marker=('PolicyGroups',
                                              'PolicyUsers',
                                              'PolicyRoles'))

    def attach_group_policy(self, policy_arn, group_name):
        """
        :type policy_arn: string
        :param policy_arn: The ARN of the policy to attach

        :type group_name: string
        :param group_name: Group to attach the policy to

        """
        params = {'PolicyArn': policy_arn, 'GroupName': group_name}
        return self.get_response('AttachGroupPolicy', params)

    def attach_role_policy(self, policy_arn, role_name):
        """
        :type policy_arn: string
        :param policy_arn: The ARN of the policy to attach

        :type role_name: string
        :param role_name: Role to attach the policy to

        """
        params = {'PolicyArn': policy_arn, 'RoleName': role_name}
        return self.get_response('AttachRolePolicy', params)

    def attach_user_policy(self, policy_arn, user_name):
        """
        :type policy_arn: string
        :param policy_arn: The ARN of the policy to attach

        :type user_name: string
        :param user_name: User to attach the policy to

        """
        params = {'PolicyArn': policy_arn, 'UserName': user_name}
        return self.get_response('AttachUserPolicy', params)

    def detach_group_policy(self, policy_arn, group_name):
        """
        :type policy_arn: string
        :param policy_arn: The ARN of the policy to detach

        :type group_name: string
        :param group_name: Group to detach the policy from

        """
        params = {'PolicyArn': policy_arn, 'GroupName': group_name}
        return self.get_response('DetachGroupPolicy', params)

    def detach_role_policy(self, policy_arn, role_name):
        """
        :type policy_arn: string
        :param policy_arn: The ARN of the policy to detach

        :type role_name: string
        :param role_name: Role to detach the policy from

        """
        params = {'PolicyArn': policy_arn, 'RoleName': role_name}
        return self.get_response('DetachRolePolicy', params)

    def detach_user_policy(self, policy_arn, user_name):
        """
        :type policy_arn: string
        :param policy_arn: The ARN of the policy to detach

        :type user_name: string
        :param user_name: User to detach the policy from

        """
        params = {'PolicyArn': policy_arn, 'UserName': user_name}
        return self.get_response('DetachUserPolicy', params)

    def list_attached_group_policies(self, group_name, marker=None, max_items=None,
                                     path_prefix=None):
        """
        List Attached Group policies.

        :type group_name: string
        :param group_name: The name of the group the policy is associated with.

        :type marker: string
        :param marker: A marker used for pagination (received from previous
            accesses)

        :type max_items: int
        :param max_items: Send only max_items; allows paginations

        :type path_prefix: string
        :param path_prefix: Send only items prefixed by this path
        """
        params = {'GroupName': group_name}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response(
            'ListAttachedGroupPolicies',
            params,
            list_marker='AttachedPolicies')

    def list_attached_role_policies(self, role_name, marker=None, max_items=None,
                                    path_prefix=None):
        """
        List Attached Role policies.

        :type role_name: string
        :param role_name: The name of the role the policy is associated with.

        :type marker: string
        :param marker: Use this parameter only when paginating results and
            only after you receive a response indicating that the results are
            truncated. Set it to the value of the Marker element in the
            response that you received to indicate where the next call should
            start.

        :type max_items: string
        :param max_items: Use this only when paginating results to indicate
            the maximum number of items you want in the response. If additional
            items exist beyond the maximum you specify, the IsTruncated
            response element is true.
            If you do not include this parameter, the number of items defaults
            to 100. Note that IAM might return fewer results, even when there
            are more results available. In that case, the IsTruncated response
            element returns true, and Marker contains a value to include in
            the subsequent call that tells the service where to continue from.

        :type path_prefix: string
        :param path_prefix: The path prefix for filtering the results. This
            parameter is optional. If it is not included, it defaults to a
            slash (/), listing all policies.
        """
        params = {'RoleName': role_name}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response('ListAttachedRolePolicies', params,
                                 list_marker='AttachedPolicies')

    def list_attached_user_policies(self, user_name, marker=None, max_items=None,
                                    path_prefix=None):
        """
        List Attached User policies.

        :type user_name: string
        :param user_name: The name of the user the policy is associated with.

        :type marker: string
        :param marker: A marker used for pagination (received from previous
            accesses)

        :type max_items: int
        :param max_items: Send only max_items; allows paginations

        :type path_prefix: string
        :param path_prefix: Send only items prefixed by this path
        """
        params = {'UserName': user_name}
        if path_prefix is not None:
            params['PathPrefix'] = path_prefix
        if marker is not None:
            params['Marker'] = marker
        if max_items is not None:
            params['MaxItems'] = max_items
        return self.get_response(
            'ListAttachedUserPolicies',
            params,
            list_marker='AttachedPolicies')

    def get_cloudian_bill(self, period, userid=None):
        params = {'BillingPeriod': period}
        if userid is not None:
            params['CanonicalUserId'] = userid
        return self.get_rbac_response('GetCloudianBill', params)

    def get_cloudian_group(self, gid):
        params = {'GroupId': gid}
        return self.get_rbac_response('GetCloudianGroup', params)

    def get_cloudian_group_list(self, prefix=None, limit=None, offset=None):
        params = {}
        if prefix is not None:
            params['Prefix'] = prefix
        if limit is not None:
            params['Limit'] = limit
        if offset is not None:
            params['Offset'] = offset
        return self.get_rbac_response('GetCloudianGroupList', params)

    def get_cloudian_user(self, gid, uid):
        params = {'GroupId': gid, 'UserId': uid}
        return self.get_rbac_response('GetCloudianUser', params)

    def get_cloudian_user_list(self, gid, type, status, prefix=None, limit=None, offset=None):
        params = {'GroupId': gid, 'UserType': type, 'UserStatus': status}
        if prefix is not None:
            params['Prefix'] = prefix
        if limit is not None:
            params['Limit'] = limit
        if offset is not None:
            params['Offset'] = offset
        return self.get_rbac_response('GetCloudianUserList', params)

    def get_cloudian_user_credentials(self, akey):
        params = {'AccessKey': akey}
        return self.get_rbac_response('GetCloudianUserCredentials', params)

    def get_cloudian_user_credentials_list(self, gid=None, uid=None, userid=None, rootonly=None):
        params = {}
        if userid is not None:
            # CanonicalUserId
            params['CanonicalUserId'] = userid
        elif gid is not None and uid is not None:
            params = {'GroupId': gid, 'UserId': uid}
        if rootonly is not None:
            params['RootAccountOnly'] = rootonly
        return self.get_rbac_response('GetCloudianUserCredentialsList', params)

    def get_cloudian_user_credentials_list_active(self, gid, uid):
        params = {'GroupId': gid, 'UserId': uid}
        return self.get_rbac_response('GetCloudianUserCredentialsListActive', params)

    def get_cloudian_qos_limit(self, gid, uid, region=None):
        params = {'GroupId': gid, 'UserId': uid}
        if region is not None:
            params['Region'] = region
        return self.get_rbac_response('GetCloudianQosLimits', params)

    def get_cloudian_system_license(self):
        params = {}
        return self.get_rbac_response('GetCloudianSystemLicense', params)

    def get_cloudian_system_version(self):
        params = {}
        return self.get_rbac_response('GetCloudianSystemVersion', params)

    def get_cloudian_usage(self, op, stime, etime, gra, id=None, userid=None, bucket=None,
                           limit=None, reversed=None, page=None, offset=None, region=None,
                           regionoffset=None):
        params = {}
        if id is not None:
            params['Id'] = id
        elif userid is not None:
            params['CanonicalUserId'] = userid
        elif bucket is not None:
            params['Bucket'] = bucket
        params['Operation'] = op
        if stime:
            params['StartTime'] = stime
        if etime:
            params['EndTime'] = etime
        if gra:
            params['Granularity'] = gra
        if limit is not None:
            params['Limit'] = limit
        if reversed is not None:
            params['IsReversed'] = reversed
        if page is not None:
            params['PageSize'] = page
        if offset is not None:
            params['Offset'] = offset
        if region is not None:
            params['Region'] = region
        if regionoffset is not None:
            params['RegionOffset'] = regionoffset
        return self.get_rbac_response('GetCloudianUsage', params)

    def get_cloudian_monitor_events(self, nodeid, showack=None, limit=None, region=None):
        params = {'NodeId': nodeid}
        if showack is not None:
            params['ShowAck'] = showack
        if limit is not None:
            params['Limit'] = limit
        if region is not None:
            params['Region'] = region
        return self.get_rbac_response('GetCloudianMonitorEvents', params)

    def get_cloudian_monitor_nodelist(self, region=None):
        params = {}
        if region is not None:
            params['Region'] = region
        return self.get_rbac_response('GetCloudianMonitorNodeList', params)

    def get_cloudian_monitor_host(self, nodeid, region=None):
        params = {'NodeId': nodeid}
        if region is not None:
            params['Region'] = region
        return self.get_rbac_response('GetCloudianMonitorHost', params)

    def get_cloudian_monitor_region(self, region=None):
        params = {}
        if region is not None:
            params['Region'] = region
        return self.get_rbac_response('GetCloudianMonitorRegion', params)
