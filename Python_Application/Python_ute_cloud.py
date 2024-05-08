# -*- coding: utf-8 -*-
"""
:created on: '12/5/14'

:copyright: NSN
:author: Bartłomiej Idzikowski
:contact: bartlomiej.idzikowski@nokia.com
:guide:
http://files.ute.nsn-rdnet.net/package_documentation/ute_cloud_reservation_api/api/ute_cloud_reservation_api.html#ute_cloud_reservation_api.api.CloudReservationApi.extend_reservation
"""

import logging
from ute_cloud_common_api.common import CloudCommonApi
from ute_cloud_common_api.exception import ApiParametersValidationFailException, ApiActionNotPermittedException, ApiTooManyRequestsException
from ute_cloud_reservation_api.exception import ApiCloudReservationException, ApiMaxReservationCountExceededException, \
    ApiTooEarlyExtendAttemptException, ApiWrongReservationStatusFoundException, ApiDeactivatedTestlineFoundException, \
    ApiTestlineRestrictedAccessFoundException, ApiMaxExtendTimeExceededException


_logger = logging.getLogger(__name__)


class CloudReservationApi(CloudCommonApi):
    API_EXCEPTIONS = {
        100: ApiActionNotPermittedException,
        200: ApiParametersValidationFailException,
        300: ApiCloudReservationException,
        301: ApiMaxReservationCountExceededException,
        302: ApiTooEarlyExtendAttemptException,
        303: ApiWrongReservationStatusFoundException,
        304: ApiDeactivatedTestlineFoundException,
        305: ApiTestlineRestrictedAccessFoundException,
        306: ApiMaxExtendTimeExceededException,
        429: ApiTooManyRequestsException,
    }

    def __request(self, resource, data, method='post'):
        return self._request(resource, data, CloudReservationApi.API_EXCEPTIONS, method)

    def create_reservation(self, testline_type, enb_build=None, ute_build=None, sysimage_build=None, test_repository_revision=None,
                           state=None, duration=None, tags=None, share_with=None):
        """Create reservation.

        :param string testline_type: Testline types eg. CLOUD_F. The value of this field must be provided.
        :param string enb_build: eNB build name. By default latest active.
        :param string ute_build: Version of UTE package. By default latest active.
        :param sysimage_build: System image version. By default latest active.
        :param string test_repository_revision: Test repository revision. By default latest revision (HEAD).
        :param string state: eNB state which should be achieved eg. configured, commissioned. By default configured.
        :param integer duration: Testline reservation duration in minutes. Maximum is 420. By default 60.
        :param list tags: List of tags names. There must be exactly one scope tag provided.
        :param list share_with: List of users who will be granted access to newly created reservation. By default empty.
        :type: share_with: list of str, each str is User`s username
        :rtype: integer
        :return: Reservation id.

        """
        resource = 'reservation/create'

        request_data = {
            "testline_type": testline_type,
            "enb_build": enb_build,
            "ute_build": ute_build,
            "sysimage_build": sysimage_build,
            "test_repository_revision": test_repository_revision,
            "state": state,
            "duration": duration,
            "tags": tags,
            "share_with": share_with,
        }
        return self.__request(resource, request_data)

    def extend_reservation(self, reservation_id, duration=None):
        """Extend ongoing reservation.

        :param reservation_id: Reservation id.
        :param duration: Duration in minutes between 1 and 180. Default: 60.
        """
        resource = 'reservation/extend'

        request_data = {
            "id": reservation_id,
            "duration": duration
        }
        print("...extend...")
        return self.__request(resource, request_data)

    def share_reservation(self, reservation_id, users):
        """Share reservation with other users so that they can extend, release and see reservation details.

        :param reservation_id: Reservation id.
        :param users: Users who will be granted access to Reservation.
        :type: users: list of str, each str is User`s username
        """

        resource = 'reservation/add_sharing_users'

        request_data = {
            "id": reservation_id,
            "share_with": users
        }
        return self.__request(resource, request_data)

    def get_reservation_status(self, reservation_id):
        """Get reservation status as text.

        Status list:
          - 'Pending for testline'
          - 'Testline assigned'
          - 'Confirmed'
          - 'Finished'
          - 'Canceled'

        :param integer reservation_id: Reservation id.
        :rtype: string
        """
        resource = 'reservation/status'
        request_data = {"id": reservation_id}
        return self.__request(resource, request_data, method='get')

    def get_reservation_details(self, reservation_id):
        """Get reservation details.

        Test line address, user and password are returned only for: reservation owner and reservation share with users

        :param integer reservation_id: Reservation id.
        :rtype: dict
        :return:

        .. code-block:: python

            rs['id']                        # reservation id
            rs['user']                      # reservation requestor username
            rs['status']                    # reservation status
            rs['testline_type']             # reservation requested testline_type
            rs['enb_build']                 # eNB build name
            rs['ute_build']                 # ute linux package build version
            rs['sysimage_build']            # system image build name
            rs['test_repository_revision']  # test repository revision
            rs['add_date']                  # reservation add date
            rs['start_date']                # reservation start date
            rs['end_date']                  # reservation end date
            rs['testline']['name']          # reservation test line name
            rs['testline']['site']          # reservation test line site
            rs['testline']['address']       # reservation test line address. If testline has more VM, master VM address will be provided.
            rs['testline']['user']          # reservation test line user
            rs['testline']['password']      # reservation test line password
            rs['tags']                      # reservation tags

        """
        resource = 'reservation/details'
        request_data = {"id": reservation_id}
        return self.__request(resource, request_data, method='get')

    def release_reservation(self, reservation_id):
        """Release reservation. Reservation will be canceled/finished depends on reservation status.

        :param integer reservation_id: Reservation id.
        :rtype: integer
        :return: Reservation id.
        """
        resource = 'reservation/release'
        request_data = {"id": reservation_id}
        return self.__request(resource, request_data)

    def get_available_tl_count_group_by_type(self):
        """Get available test line count grouped by TL type.

        :rtype: dict
        :return: Dict where key is testline type and value is number of available test lines. eg. {"CLOUD_F": 10}
        """
        resource = 'metric/get_available_tl_count_group_by_type'
        request_data = {}
        return self.__request(resource, request_data, method='get')

    def get_available_tl_count(self):
        """Get available test line count.

        :rtype: int

        """
        resource = 'metric/get_available_tl_count'
        request_data = {}
        return self.__request(resource, request_data, method='get')

    def get_testline_type_details(self, name):
        """Get testline type details.

        :param string name: Testline type name.
        :rtype: dict
        :return:

        .. code-block:: python

            details['name']                     # testline type name
            details['agent']                    # testline type related agent name
            details['active']                   # whether if testline type is active
            details['compatibility_regex']      # regex that defines testline type compatible enbbuild
            details['states']                   # list of avialable testline type states
        """
        resource = 'testline_type/details'
        request_data = {"name": name}
        return self.__request(resource, request_data, method='get')

    def list_my_reservations(self, status=None, offset=0, limit=10, shared=False):
        """List all user reservation ids sorted by add date descending (newest on top).

        :param string status: Reservation status is optional parameter. Possible values are listed below. Default: None. List reservation ids
            regardless of its status.

            Status list:
              - 'Pending for testline'
              - 'Testline assigned'
              - 'Confirmed'
              - 'Finished'
              - 'Canceled'
        :param integer offset: Skip first offset ids. Default: 0.
        :param integer limit: No more than limit ids will be returned. Default: 10.
        :param boolean shared: If True include reservations shared with user. Default: False

        :Example:
            - list_my_reservations() - list first 10 user reservation ids regardless of its status.
            - list_my_reservations(status='Finished') - list first 10 user reservation ids that have 'Finished' status.
            - list_my_reservations(offset=5) - list 10 user reservation ids from 6 to 15.
            - list_my_reservations(offset=10, limit=5) - list 5 user reservation ids from 11 to 15.

        :rtype: list
        :return: List with user reservation ids.
        """
        resource = 'reservation/list'
        request_data = {
            'status': status,
            'offset': offset,
            'limit': limit,
            'shared': shared
        }
        print("...list...")
        return self.__request(resource, request_data, method='get')

    def get_available_testlines_by_types_for_user(self, user=None, testline_type=None):
        """
        Get testlines available for `user` and group them by types. If `testline_type` passed - get available testlines for `user` for this specific
        `testline_type` only.

        :param string user:          string representing username. Default: requestor.
        :param string testline_type: string representing `testline_type` name. Default: None.

        :Example:
            - get_available_testlines_by_types_for_user() - get all available `testlines` ids for requestor and group them by types.
            - get_available_testlines_by_types_for_user(testline_type='CLOUD_F') - get all available `testlines` ids for `CLOUD_F` type for requestor.
            - get_available_testlines_by_types_for_user(user='username') - get all available `testlines` ids for `user` and group them by types.
            - get_available_testlines_by_types_for_user(user='username', testline_type='CLOUD_F') - get all available `testlines` ids for `CLOUD_F`
                                                                                                    type for `user`.

        :rtype:     dict
        :return:    Return dictionary with `testline types` as a keys and values are ids of `testlines` which ara available for `user` OR ids of
                    available testlines for specific `testline_type` for `user`.
        """

        resource = 'metric/get_available_testlines_by_types_for_user'
        request_data = {"user": user, 'testline_type': testline_type}
        return self.__request(resource, request_data, method='get')

    def reserve_quick_reservation(self, reservation_id):
        """
        Reserve pre-prepared quick reservation

        :param reservation_id: Quick reservation id

        :return: Dictionary with reservation status
        """

        resource = 'reservation/quick/create'
        request_data = {"id": reservation_id}
        return self.__request(resource, request_data)

    def list_available_quick_reservations(self):
        """
        List prepared reservations which can be reserved.

        :return: Returns available reservations as a list of dictionaries. Each dictionary contains:

        .. code-block:: python

            'ute_build'             # assigned ute_build
            'testline'              # assigned testline name
            'id'                    # reservation id
            'enb_build'             # enb_build:tag
            'testline_type'         # testline type name
        """
        resource = 'reservation/quick/list_available_reservations'

        return self.__request(resource, {}, method='get')

    def list_enb_builds(self, active=True, branch=None, name=None, promotion=None, supported_hardware=None, tag=None, testline_type=None,
                        ute_version=None, limit=10, offset=0):
        """
        List builds from the newest one and according to filtering parameters passed.


        :param bool active:                 parameter indicating whether returned builds are active or not. Default: True.
        :param string branch:               string containing branch name. Default: None (meaning any branch).
        :param string name:                 string containing regex to filter by build name. If passed, result will contain this particular builds
                                            details if it exists. Empty result instead. Default: None.
        :param string promotion:            string representing eNB build's promotion.
        :param list supported_hardware:     list containing supported_hardware name(s) to filter eNB builds by. Default: None.
        :param string tag:                  ENBBuild's tag. Default: None.
        :param string testline_type:        testline type name to get builds for. Default: None.
        :param string ute_version:          UTE build version.
        :param integer limit:               limit=len(list) to be returned. Default: 10.
        :param integer offset:              offset for list of eNB builds. Default: 0.

        :return: List consists of eNB builds that are not blacklisted, tagged as base and filtered by valid passed kwargs.
        Each dictionary is in the form of:

        .. code-block:: python

            dict['active']                  # True/False.
            dict['add_date']                # date when eNB build was added.
            dict['branch']                  # branch name
            dict['name']                    # eNB build name
            dict['promotion']               # eNB build's promotion string. If never promoted: None.
            dict['status']                  # status: Active/Removed.
            dict['supported_hardware']      # name of hardware that is supported by eNB build
            dict['tag']                     # tag
            dict['ute_version']             # UTE build version name.

        """

        resource = 'enb_build/list'
        request_data = {'active': active, 'branch': branch, 'name': name, 'promotion': promotion, 'supported_hardware': supported_hardware,
                        'tag': tag, 'testline_type': testline_type, 'ute_version': ute_version, 'limit': limit, 'offset': offset}

        return self.__request(resource, request_data, method='get')


# 创建 CloudReservationApi 的实例
api_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiaDR6aGFuZyIsImV4cGlyZXMiOjE3MTc2NDI2NjAuOTgwMjA4Nn0.U068FYN7JqxUG-Mg1_JE-othJnpHAGG_e8Y6mYCfKno"
api_instance = CloudReservationApi(api_token)

# 预约 ID 和延长时长
reservation_id = '4e01f08d-fb4a-4d14-84c7-3eab22d06ce4'
duration = 60  # 假设我们需要延长 60 分钟

# 调用 extend_reservation 方法
try:
    # response = api_instance.extend_reservation(reservation_id, duration)
    # response_get = api_instance.get_reservation_status(int(reservation_id))
    response_list = api_instance.list_my_reservations(status='Confirmed')
    print("Reservation extended successfully:", response_list)
except Exception as e:
    print("Failed to extend reservation:", str(e))
