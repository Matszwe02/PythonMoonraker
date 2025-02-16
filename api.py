import requests

GET = 0
POST = 1
DELETE = 2


class MoonrakerAPI:
    """
    Moonraker API contains all of official Moonraker HTTP API calls.\n\n
    All calls are sorted in the same way as in Moonraker's official documentation:
    - https://moonraker.readthedocs.io/en/latest/external_api/introduction/
    """
    def __init__(self, url: str):
        self.url = url
        self.token = None
        if not self.url.startswith('http'): self.url = 'http://' + self.url
    
    
    def __api_call(self, path:str, method = GET, params: dict = {}, output_format = dict, as_file_upload = False):
        url = self.url + path
        headers = {}
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
        
        for param in params.copy().keys():
            if not params[param]: params.pop(param)
        try:
            if as_file_upload:
                response = requests.post(url, files=params['files'], data=params['data'], headers=headers)
            elif method == GET:
                response = requests.get(url, params=params, headers=headers)
            elif method == POST:
                response = requests.post(url, params=params, headers=headers)
            elif method == DELETE:
                response = requests.delete(url, params=params, headers=headers)
            else:
                raise ValueError("Invalid method")

            response.raise_for_status()
            if output_format == dict:
                return response.json()
            elif output_format == bytes:
                return response.content
            elif output_format == str:
                return response.text

        except requests.exceptions.RequestException as e:
            print(f"API call failed: {e}")
            return None


    def server_info(self):
        return self.__api_call('/server/info')
    
    def server_config(self):
        return self.__api_call('/server/config')
    
    def server_temperature_store(self, include_monitors=False):
        return self.__api_call('/server/temperature_store', params={'include_monitors':include_monitors})
    
    def server_gcode_store(self, count=100):
        return self.__api_call('/server/gcode_store', params={'count':count})
    
    def server_logs_rollover(self, application='moonraker'):
        return self.__api_call('/server/logs/rollover', method=POST, params={'application':application})
    
    def server_restart(self):
        return self.__api_call('/server/restart', method=POST)
    
    def printer_info(self):
        return self.__api_call('/printer/info')
    
    def printer_emergency_stop(self):
        return self.__api_call('/printer/emergency_stop', method=POST)
    
    def printer_restart(self):
        return self.__api_call('/printer/restart', method=POST)
    
    def printer_firmware_restart(self):
        return self.__api_call('/printer/firmware_restart', method=POST)
    
    def printer_objects_list(self):
        return self.__api_call('/printer/objects/list')
    
    def printer_objects_query(self, objects: dict):
        return self.__api_call('/printer/objects/query', method=POST, params={'objects':objects})
    
    def printer_query_endstops_status(self):
        return self.__api_call('/printer/query_endstops/status')
    
    def printer_gcode_script(self, script: str):
        return self.__api_call('/printer/gcode/script', method=POST, params={'script':script})
    
    def printer_gcode_help(self):
        return self.__api_call('/printer/gcode/help')
    
    def printer_print_start(self, filename: str):
        return self.__api_call('/printer/print/start', method=POST, params={'filename':filename})
    
    def printer_print_pause(self):
        return self.__api_call('/printer/print/pause', method=POST)
    
    def printer_print_resume(self):
        return self.__api_call('/printer/print/resume', method=POST)
    
    def printer_print_cancel(self):
        return self.__api_call('/printer/print/cancel', method=POST)
    
    def machine_system_info(self):
        return self.__api_call('/machine/system_info')
    
    def machine_shutdown(self):
        return self.__api_call('/machine/shutdown', method=POST)
    
    def machine_reboot(self):
        return self.__api_call('/machine/reboot', method=POST)
    
    def machine_services_restart(self, service: str):
        return self.__api_call('/machine/services/restart', method=POST, params={'service':service})
    
    def machine_services_stop(self, service: str):
        return self.__api_call('/machine/services/stop', method=POST, params={'service':service})
    
    def machine_services_start(self, service: str):
        return self.__api_call('/machine/services/start', method=POST, params={'service':service})
    
    def machine_proc_stats(self):
        return self.__api_call('/machine/proc_stats')
    
    def machine_sudo_info(self, check_access=False):
        return self.__api_call('/machine/sudo/info', params={'check_access':check_access})
    
    def machine_sudo_password(self, password: str):
        return self.__api_call('/machine/sudo/password', method=POST, params={'password':password})
    
    def machine_peripherals_usb(self):
        return self.__api_call('/machine/peripherals/usb')
    
    def machine_peripherals_serial(self):
        return self.__api_call('/machine/peripherals/serial')
    
    def machine_peripherals_video(self):
        return self.__api_call('/machine/peripherals/video')
    
    def machine_peripherals_canbus(self, interface='can0'):
        return self.__api_call('/machine/peripherals/canbus', params={'interface':interface})
    
    def server_files_list(self, root='gcodes'):
        return self.__api_call('/server/files/list', params={'root':root})
    
    def server_files_roots(self):
        return self.__api_call('/server/files/roots')
    
    def server_files_metadata(self, filename: str):
        return self.__api_call('/server/files/metadata', params={'filename':filename})
    
    def server_files_metadata_post(self, filename: str):
        return self.__api_call('/server/files/metadata', method=POST, params={'filename':filename})
    
    def server_files_thumbnails(self, filename: str):
        return self.__api_call('/server/files/thumbnails', params={'filename':filename})
    
    def server_files_directory(self, path = 'gcodes', extended = False):
        return self.__api_call('/server/files/directory', params={'path':path, 'extended':extended})
    
    def server_files_directory_post(self, path: str):
        return self.__api_call('/server/files/directory', method=POST, params={'path':path})
    
    def server_files_directory_delete(self, path: str, force = False):
        return self.__api_call('/server/files/directory', method=DELETE, params={'path':path, 'force':force})
    
    def server_files_move(self, source: str, dest: str):
        return self.__api_call('/server/files/move', method=POST, params={'source':source, 'dest':dest})
    
    def server_files_copy(self, source: str, dest: str):
        return self.__api_call('/server/files/copy', method=POST, params={'source':source, 'dest':dest})
    
    def server_files_zip(self, items: list[str], dest: str, store_only = False):
        return self.__api_call('/server/files/zip', method=POST, params={'items':items, 'dest':dest, 'store_only':store_only})
    
    def server_files(self, root: str, filename: str):
        return self.__api_call(f'/server/files/{root}/{filename}', output_format=bytes)

    def server_files_upload(self, filename: str, file: bytes, root: str = 'gcodes', path: str = None, checksum: str = None, print: bool = False):
        files = {'file': (filename, file, 'application/octet-stream')}
        data = {'root': root, 'path': path, 'checksum': checksum, 'print': str(print).lower()}
        return self.__api_call('/server/files/upload', POST, params={'files':files, 'data':data}, as_file_upload=True)
    
    def server_files_delete(self, root: str, filename: str):
        return self.__api_call(f'/server/files/{root}/{filename}', method=DELETE)
    
    def server_files_klippy_log(self):
        return self.__api_call(f'/server/files/klippy.log', output_format=bytes)
    
    def server_files_moonraker_log(self):
        return self.__api_call(f'/server/files/moonraker.log', output_format=bytes)
    
    def access_login(self, username: str, password: str, source = 'moonraker'):
        return self.__api_call(f'/access/login', method=POST, params={'username':username, 'password':password, 'source':source})
    
    def access_logout(self):
        return self.__api_call(f'/access/logout', method=POST)
    
    def access_user(self):
        return self.__api_call(f'/access/user')
    
    def access_user_post(self, username: str, password: str):
        return self.__api_call(f'/access/user', method=POST, params={'username':username, 'password':password})
    
    def access_user_delete(self, username: str):
        return self.__api_call(f'/access/user', method=DELETE, params={'username':username})
    
    def access_users_list(self):
        return self.__api_call(f'/access/users/list')
    
    def access_user_password(self, password: str, new_password: str):
        return self.__api_call(f'/access/user/password', method=POST, params={'password':password, 'new_password':new_password})
    
    def access_refresh_jwt(self, refresh_token: str):
        return self.__api_call(f'/access/refresh_jwt', method=POST, params={'refresh_token':refresh_token})
    
    def  access_oneshot_token(self):
        return self.__api_call(f'/access/oneshot_token', output_format=str)
    
    def  access_api_key(self):
        return self.__api_call(f'/access/api_key', output_format=str)
    
    def  access_api_key_post(self):
        return self.__api_call(f'/access/api_key', method=POST, output_format=str)
    
    def server_database_list(self):
        return self.__api_call('/server/database/list')
    
    def server_database_item(self, namespace: str, key: str = None):
        return self.__api_call('/server/database/item', params={'namespace':namespace, 'key':key})
    
    def server_database_item_post(self, namespace: str, key: str, value: any):
        return self.__api_call('/server/database/item', method=POST, params={'namespace':namespace, 'key':key, 'value':value})
    
    def server_database_item_delete(self, namespace: str, key: str):
        return self.__api_call('/server/database/item', method=DELETE, params={'namespace':namespace, 'key':key})
    
    def server_database_compact(self):
        return self.__api_call('/server/database/compact', method=POST)
    
    def server_database_backup_post(self, filename: str):
        return self.__api_call('/server/database/backup', method=POST, params={'filename':filename})
    
    def server_database_backup_delete(self, filename: str):
        return self.__api_call('/server/database/backup', method=DELETE, params={'filename':filename})
    
    def server_database_restore(self, filename: str):
        return self.__api_call('/server/database/restore', method=POST, params={'filename':filename})
    
    def debug_database_list(self):
        return self.__api_call('/debug/database/list')
    
    def debug_database_item(self, namespace: str, key: str = None):
        return self.__api_call('/debug/database/item', params={'namespace':namespace, 'key':key})
    
    def debug_database_item_post(self, namespace: str, key: str, value: any):
        return self.__api_call('/debug/database/item', method=POST, params={'namespace':namespace, 'key':key, 'value':value})
    
    def debug_database_item_delete(self, namespace: str, key: str):
        return self.__api_call('/debug/database/item', method=DELETE, params={'namespace':namespace, 'key':key})
    
    def debug_database_table(self, table: str):
        return self.__api_call('/debug/database/table', params={'table':table})
    
    def server_job_queue_status(self):
        return self.__api_call('/server/job_queue/status')
    
    def server_job_queue_job_post(self, filenames: list[str], reset: bool = False):
        return self.__api_call('/server/job_queue/job', method=POST, params={'filenames':filenames, 'reset':reset})
    
    def server_job_queue_job_delete(self, job_ids: list[str], all: bool = False):
        return self.__api_call('/server/job_queue/job', method=DELETE, params={'job_ids':job_ids, 'all':all})
    
    def server_job_queue_pause(self):
        return self.__api_call('/server/job_queue/pause', method=POST)
    
    def server_job_queue_start(self):
        return self.__api_call('/server/job_queue/start', method=POST)
    
    def server_job_queue_jump(self, job_id: str):
        return self.__api_call('/server/job_queue/jump', method=POST, params={'job_id':job_id})
    
    def server_history_list(self, limit: int = 50, start: int = 0, before: float = None, since: float = None, order: str = "desc"):
        return self.__api_call('/server/history/list', params={'limit':limit, 'start':start, 'before':before, 'since':since, 'order':order})
    
    def server_history_totals(self):
        return self.__api_call('/server/history/totals')
    
    def server_history_reset_totals(self):
        return self.__api_call('/server/history/reset_totals', method=POST)
    
    def server_history_job(self, uid: str):
        return self.__api_call('/server/history/job', params={'uid':uid})
    
    def server_history_job_delete(self, uid: str, all: bool = False):
        return self.__api_call('/server/history/job', method=DELETE, params={'uid':uid, 'all':all})
    
    def server_announcements_list(self, include_dismissed: bool = False):
        return self.__api_call('/server/announcements/list', params={'include_dismissed':include_dismissed})
    
    def server_announcements_update(self):
        return self.__api_call('/server/announcements/update', method=POST)
    
    def server_announcements_dismiss(self, entry_id: str, wake_time: float = None):
        return self.__api_call('/server/announcements/dismiss', method=POST, params={'entry_id':entry_id, 'wake_time':wake_time})
    
    def server_announcements_feeds(self):
        return self.__api_call('/server/announcements/feeds')
    
    def server_announcements_feed_post(self, name: str):
        return self.__api_call('/server/announcements/feed', method=POST, params={'name':name})
    
    def server_announcements_feed_delete(self, name: str):
        return self.__api_call('/server/announcements/feed', method=DELETE, params={'name':name})
    
    def server_webcams_list(self):
        return self.__api_call('/server/webcams/list')
    
    def server_webcams_item(self, uid: str):
        return self.__api_call('/server/webcams/item', params={'uid':uid})
    
    def server_webcams_item_post(self, params: dict):
        return self.__api_call('/server/webcams/item', method=POST, params=params)
    
    def server_webcams_item_delete(self, uid: str):
        return self.__api_call('/server/webcams/item', method=DELETE, params={'uid':uid})
    
    def server_webcams_test(self, uid: str):
        return self.__api_call('/server/webcams/test', method=POST, params={'uid':uid})
    
    def machine_update_status(self):
        return self.__api_call('/machine/update/status')
    
    def machine_update_refresh(self, name: str):
        return self.__api_call('/machine/update/refresh', method=POST, params={'name':name})
    
    def machine_update_upgrade(self, name: str):
        return self.__api_call('/machine/update/upgrade', method=POST, params={'name':name})
    
    def machine_update_recover(self, name: str, hard: bool = False):
        return self.__api_call('/machine/update/recover', method=POST, params={'name':name, 'hard':hard})
    
    def machine_update_rollback(self, name: str):
        return self.__api_call('/machine/update/rollback', method=POST, params={'name':name})
    
    def machine_update_full(self):
        return self.__api_call('/machine/update/full', method=POST)
    
    def machine_update_moonraker(self):
        return self.__api_call('/machine/update/moonraker', method=POST)
    
    def machine_update_klipper(self):
        return self.__api_call('/machine/update/klipper', method=POST)
    
    def machine_update_client(self, name: str):
        return self.__api_call('/machine/update/client', method=POST, params={'name':name})
    
    def machine_update_system(self):
        return self.__api_call('/machine/update/system', method=POST)
    
    def machine_device_power_devices(self):
        return self.__api_call('/machine/device_power/devices')
    
    def machine_device_power_device(self, device: str):
        return self.__api_call('/machine/device_power/device', params={'device':device})
    
    def machine_device_power_device_post(self, device: str, action: str):
        return self.__api_call('/machine/device_power/device', method=POST, params={'device':device, 'action':action})
    
    def machine_device_power_status(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return self.__api_call('/machine/device_power/status', params=params)
    
    def machine_device_power_on(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return self.__api_call('/machine/device_power/on', method=POST, params=params)
    
    def machine_device_power_off(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return self.__api_call('/machine/device_power/off', method=POST, params=params)
    
    def machine_wled_strips(self):
        return self.__api_call('/machine/wled/strips')
    
    def machine_wled_status(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return self.__api_call('/machine/wled/status', params=params)
    
    def machine_wled_on(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return self.__api_call('/machine/wled/on', method=POST, params=params)
    
    def machine_wled_off(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return self.__api_call('/machine/wled/off', method=POST, params=params)
    
    def machine_wled_toggle(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return self.__api_call('/machine/wled/toggle', method=POST, params=params)
    
    def machine_wled_strip(self, strip: str):
        return self.__api_call('/machine/wled/strip', params={'strip':strip})
    
    def machine_wled_strip_post(self, params: dict):
        return self.__api_call('/machine/wled/strip', method=POST, params=params)
    
    def server_sensors_list(self, extended: bool = False):
        return self.__api_call('/server/sensors/list', params={'extended':extended})
    
    def server_sensors_info(self, sensor: str, extended: bool = False):
        return self.__api_call('/server/sensors/info', params={'sensor':sensor, 'extended':extended})
    
    def server_sensors_measurements(self, sensor: str = None):
        return self.__api_call('/server/sensors/measurements', params={'sensor': sensor})
    
    def server_mqtt_publish(self, topic: str, payload: any = None, qos: int = None, retain: bool = False, timeout: float = None):
        params = {'topic': topic, 'payload': payload, 'qos': qos, 'retain': retain, 'timeout': timeout}
        return self.__api_call('/server/mqtt/publish', method=POST, params=params)
    
    def server_mqtt_subscribe(self, topic: str, qos: int = None, timeout: float = None):
        return self.__api_call('/server/mqtt/subscribe', method=POST, params={'topic': topic, 'qos': qos, 'timeout': timeout})
    
    def server_notifiers_list(self):
        return self.__api_call('/server/notifiers/list')
    
    def debug_notifiers_test(self, name: str):
        return self.__api_call('/debug/notifiers/test', method=POST, params={'name': name})
    
    def server_spoolman_status(self):
        return self.__api_call('/server/spoolman/status')
    
    def server_spoolman_spool_id_post(self, spool_id: int = None):
        return self.__api_call('/server/spoolman/spool_id', method=POST, params={'spool_id': spool_id})
    
    def server_spoolman_spool_id(self):
        return self.__api_call('/server/spoolman/spool_id')
    
    def server_spoolman_proxy(self, request_method: str, path: str, query: str = None, body: dict = None, use_v2_response: bool = False):
        return self.__api_call('/server/spoolman/proxy', method=POST, params={'request_method': request_method, 'path': path, 'query': query, 'body': body, 'use_v2_response': use_v2_response})
    
    def server_analysis_status(self):
        return self.__api_call('/server/analysis/status')
    
    def server_analysis_estimate(self, filename: str, estimator_config: str = "", update_metadata: bool = False):
        return self.__api_call('/server/analysis/estimate', method=POST, params={'filename': filename, 'estimator_config': estimator_config, 'update_metadata': update_metadata})
    
    def server_analysis_dump_config(self, dest_config: str = None):
        return self.__api_call('/server/analysis/dump_config', method=POST, params={'dest_config': dest_config})
    
    def api_version(self):
        return self.__api_call('/api/version')
    
    def api_server(self):
        return self.__api_call('/api/server')
    
    def api_login(self):
        return self.__api_call('/api/login')
    
    def api_settings(self):
        return self.__api_call
    
    def api_files_local(self, filename: str, file: bytes, root: str = 'gcodes', path: str = None, checksum: str = None, print: bool = False):
        files = {'file': (filename, file, 'application/octet-stream')}
        data = {'root': root, 'path': path, 'checksum': checksum, 'print': str(print).lower()}
        return self.__api_call('/api/files/upload', POST, params={'files':files, 'data':data}, as_file_upload=True)('/api/settings')
    
    def api_job(self):
        return self.__api_call('/api/job')
    
    def api_printer(self):
        return self.__api_call('/api/printer')
    
    def api_printer_command(self, commands: list[str]):
        return self.__api_call('/api/printer/command', method=POST, params={'commands': commands})
    
    def api_printerprofiles(self):
        return self.__api_call('/api/printerprofiles')
    
    def server_extensions_list(self):
        return self.__api_call('/server/extensions/list')
    
    def server_extensions_request(self, agent: str, method: str, arguments: dict = None):
        return self.__api_call('/server/extensions/request', method=POST, params={'agent': agent, 'method': method, 'arguments': arguments})
