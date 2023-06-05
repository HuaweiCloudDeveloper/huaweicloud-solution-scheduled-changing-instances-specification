# coding: utf-8

from huaweicloudsdkcore.auth.credentials import BasicCredentials
from huaweicloudsdkecs.v2.region.ecs_region import EcsRegion
from huaweicloudsdkcore.exceptions import exceptions
from huaweicloudsdkecs.v2 import *
import traceback


def handler(event, context):
    log = context.getLogger()
    flag, result = check_configuration(context)
    if flag is False:
        return result
    processor = Processor(context)
    try:
        return processor.batch_change_specification()
    except:
        log.error("failed to batch change specification"
                  f"exception：{traceback.format_exc()}")


def check_configuration(context):
    ak = context.getSecurityAccessKey()
    sk = context.getSecuritySecretKey()
    if not ak or not sk:
        ak = context.getUserData('ak', '').strip()
        sk = context.getUserData('sk', '').strip()
        if not ak or not sk:
            return False, 'ak or sk is empty'
    return True, ""


class Processor:
    def __init__(self, context=None):
        self.log = context.getLogger()
        self.ecs_client = get_ecs_client(context)
        self.id_list = context.getUserData('ecs_ids').strip().split()
        self.ecs_flavor = context.getUserData('ecs_flavor').strip()

    def change_specification(self, server_id):
        request = ResizePostPaidServerRequest()
        request.server_id = server_id
        resizebody = ResizePostPaidServerOption(flavor_ref=self.ecs_flavor)
        request.body = ResizePostPaidServerRequestBody(resize=resizebody)
        response = self.ecs_client.resize_post_paid_server(request)
        return response

    def batch_change_specification(self):
        successful_server_lst_ids = []
        failed_server_lst_ids = []
        response_list = []
        flag_ = True
        for server_id in self.id_list:
            try:
                response = self.change_specification(server_id)
                response_list.append(response)
                successful_server_lst_ids.append(server_id)
            except exceptions.ClientRequestException as e:
                flag_ = False
                failed_server_lst_ids.append(server_id)
                self.log.error(f"Failed to change specification, ecs id:{server_id},"
                               f"status_code:{e.status_code}, "
                               f"request_id:{e.request_id}, "
                               f"error_code:{e.error_code}, "
                               f"error_msg:{e.error_msg}")
        self.log.info(f"Successful to change specification, ecs ids:{' '.join(successful_server_lst_ids)}")
        if flag_ is False:
            self.log.error(f"failed to change specification, ecs ids:{' '.join(failed_server_lst_ids)}")
        response_data = self.result_format_processing(response_list)
        return response_data

    @staticmethod
    def result_format_processing(response):
        info = str(response)
        info_dict = {
            "statusCode": 200,
            "isBase64Encoded": False,
            "headers": {},
            "body": info
        }
        return info_dict


def get_ecs_client(context):
    ak = context.getSecurityAccessKey()
    sk = context.getSecuritySecretKey()
    st = context.getSecurityToken()
    project_id = context.getProjectID()
    credentials = BasicCredentials(ak, sk, project_id).with_security_token(st)
    ecs_client = EcsClient.new_builder() \
        .with_credentials(credentials) \
        .with_region(EcsRegion.value_of("ap-southeast-3")) \
        .build()
    return ecs_client
