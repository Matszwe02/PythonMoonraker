import json
import websockets
import random


class MoonrakerWS:
    """
    Moonraker API contains all of official Moonraker JSON-RPC API calls.\n\n
    All calls are sorted in the same way as in Moonraker's official documentation:
    - https://moonraker.readthedocs.io/en/latest/external_api/introduction/
    """
    def __init__(self, url: str):
        self.url = url
        self.username = None
        self.password = None
        self.ws = None
        if not self.url.startswith('ws://'):
            self.url = 'ws://' + self.url
        if ':' not in self.url.replace('://', ''):
            self.url += ':7125'
        if not self.url.endswith('/websocket'):
            self.url = self.url.rstrip('/') + '/websocket'

    async def ws_connect(self):
        """Establish WebSocket connection"""
        try:
            self.ws = await websockets.connect(self.url)
        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
            self.ws = None


    async def ws_close(self):
        """Close WebSocket connection"""
        if self.ws:
            await self.ws.close()
            self.ws = None


    async def __ws_call(self, path:str, params: dict = {}):
        if not self.ws:
            print("WebSocket connection not established.")
            return None
        
        for param in params.copy().keys():
            if not params[param]: params.pop(param)
        if self.username: params['username'] = self.username
        if self.password: params['password'] = self.password
        try:
            await self.ws.send(json.dumps({
                "jsonrpc": "2.0",
                "method": path.lstrip('/').replace('/', '.'),
                "params": params,
                "id": random.randint(0, 99999999)
            }))
            response = json.loads(await self.ws.recv())
            return response.get('result', {})
            # print("Server Info Response:", response)
        except Exception as e:
            print(f"Websocket Error: {e}")


    async def server_info(self):
        return await self.__ws_call('/server/info')
    
    async def server_config(self):
        return await self.__ws_call('/server/config')
    
    async def server_temperature_store(self, include_monitors=False):
        return await self.__ws_call('/server/temperature_store', params={'include_monitors':include_monitors})
    
    async def server_gcode_store(self, count=100):
        return await self.__ws_call('/server/gcode_store', params={'count':count})
    
    async def server_logs_rollover(self, application='moonraker'):
        return await self.__ws_call('/server/logs/rollover', params={'application':application})
    
    async def server_restart(self):
        return await self.__ws_call('/server/restart')
    
    async def printer_info(self):
        return await self.__ws_call('/printer/info')
    
    async def printer_emergency_stop(self):
        return await self.__ws_call('/printer/emergency_stop')
    
    async def printer_restart(self):
        return await self.__ws_call('/printer/restart')
    
    async def printer_firmware_restart(self):
        return await self.__ws_call('/printer/firmware_restart')
    
    async def printer_objects_list(self):
        return await self.__ws_call('/printer/objects/list')
    
    async def printer_objects_query(self, objects: dict):
        return await self.__ws_call('/printer/objects/query', params={'objects':objects})
    
    async def printer_objects_subscribe(self, objects: dict):
        return await self.__ws_call('/printer/objects/subscribe', params={'objects':objects})
    
    async def printer_query_endstops_status(self):
        return await self.__ws_call('/printer/query_endstops/status')
    
    async def printer_gcode_script(self, script: str):
        return await self.__ws_call('/printer/gcode/script', params={'script':script})
    
    async def printer_gcode_help(self):
        return await self.__ws_call('/printer/gcode/help')
    
    async def printer_print_start(self, filename: str):
        return await self.__ws_call('/printer/print/start', params={'filename':filename})
    
    async def printer_print_pause(self):
        return await self.__ws_call('/printer/print/pause')
    
    async def printer_print_resume(self):
        return await self.__ws_call('/printer/print/resume')
    
    async def printer_print_cancel(self):
        return await self.__ws_call('/printer/print/cancel')
    
    async def machine_system_info(self):
        return await self.__ws_call('/machine/system_info')
    
    async def machine_shutdown(self):
        return await self.__ws_call('/machine/shutdown')
    
    async def machine_reboot(self):
        return await self.__ws_call('/machine/reboot')
    
    async def machine_services_restart(self, service: str):
        return await self.__ws_call('/machine/services/restart', params={'service':service})
    
    async def machine_services_stop(self, service: str):
        return await self.__ws_call('/machine/services/stop', params={'service':service})
    
    async def machine_services_start(self, service: str):
        return await self.__ws_call('/machine/services/start', params={'service':service})
    
    async def machine_proc_stats(self):
        return await self.__ws_call('/machine/proc_stats')
    
    async def machine_sudo_info(self, check_access=False):
        return await self.__ws_call('/machine/sudo/info', params={'check_access':check_access})
    
    async def machine_sudo_password(self, password: str):
        return await self.__ws_call('/machine/sudo/password', params={'password':password})
    
    async def machine_peripherals_usb(self):
        return await self.__ws_call('/machine/peripherals/usb')
    
    async def machine_peripherals_serial(self):
        return await self.__ws_call('/machine/peripherals/serial')
    
    async def machine_peripherals_video(self):
        return await self.__ws_call('/machine/peripherals/video')
    
    async def machine_peripherals_canbus(self, interface='can0'):
        return await self.__ws_call('/machine/peripherals/canbus', params={'interface':interface})
    
    async def server_files_list(self, root='gcodes'):
        return await self.__ws_call('/server/files/list', params={'root':root})
    
    async def server_files_roots(self):
        return await self.__ws_call('/server/files/roots')
    
    async def server_files_metadata(self, filename: str):
        return await self.__ws_call('/server/files/metadata', params={'filename':filename})
    
    async def server_files_metadata_post(self, filename: str):
        return await self.__ws_call('/server/files/metadata', params={'filename':filename})
    
    async def server_files_thumbnails(self, filename: str):
        return await self.__ws_call('/server/files/thumbnails', params={'filename':filename})
    
    async def server_files_directory(self, path = 'gcodes', extended = False):
        return await self.__ws_call('/server/files/directory', params={'path':path, 'extended':extended})
    
    async def server_files_directory_post(self, path: str):
        return await self.__ws_call('/server/files/directory', params={'path':path})
    
    async def server_files_directory_delete(self, path: str, force = False):
        return await self.__ws_call('/server/files/directory', params={'path':path, 'force':force})
    
    async def server_files_move(self, source: str, dest: str):
        return await self.__ws_call('/server/files/move', params={'source':source, 'dest':dest})
    
    async def server_files_copy(self, source: str, dest: str):
        return await self.__ws_call('/server/files/copy', params={'source':source, 'dest':dest})
    
    async def server_files_zip(self, items: list[str], dest: str, store_only = False):
        return await self.__ws_call('/server/files/zip', params={'items':items, 'dest':dest, 'store_only':store_only})
    
    async def server_files_delete(self, root: str, filename: str):
        return await self.__ws_call(f'/server/files/{root}/{filename}')
    
    async def server_files_klippy_log(self):
        return await self.__ws_call(f'/server/files/klippy.log', output_format=bytes)
    
    async def server_files_moonraker_log(self):
        return await self.__ws_call(f'/server/files/moonraker.log', output_format=bytes)
    
    async def access_login(self, username: str, password: str, source = 'moonraker'):
        return await self.__ws_call(f'/access/login', params={'username':username, 'password':password, 'source':source})
    
    async def access_logout(self):
        return await self.__ws_call(f'/access/logout')
    
    async def access_user(self):
        return await self.__ws_call(f'/access/user')
    
    async def access_user_post(self, username: str, password: str):
        return await self.__ws_call(f'/access/user', params={'username':username, 'password':password})
    
    async def access_user_delete(self, username: str):
        return await self.__ws_call(f'/access/user', params={'username':username})
    
    async def access_users_list(self):
        return await self.__ws_call(f'/access/users/list')
    
    async def access_user_password(self, password: str, new_password: str):
        return await self.__ws_call(f'/access/user/password', params={'password':password, 'new_password':new_password})
    
    async def access_refresh_jwt(self, refresh_token: str):
        return await self.__ws_call(f'/access/refresh_jwt', params={'refresh_token':refresh_token})
    
    async def  access_oneshot_token(self):
        return await self.__ws_call(f'/access/oneshot_token', output_format=str)
    
    async def  access_api_key(self):
        return await self.__ws_call(f'/access/api_key', output_format=str)
    
    async def  access_api_key_post(self):
        return await self.__ws_call(f'/access/api_key', output_format=str)
    
    async def server_database_list(self):
        return await self.__ws_call('/server/database/list')
    
    async def server_database_item(self, namespace: str, key: str = None):
        return await self.__ws_call('/server/database/item', params={'namespace':namespace, 'key':key})
    
    async def server_database_item_post(self, namespace: str, key: str, value: any):
        return await self.__ws_call('/server/database/item', params={'namespace':namespace, 'key':key, 'value':value})
    
    async def server_database_item_delete(self, namespace: str, key: str):
        return await self.__ws_call('/server/database/item', params={'namespace':namespace, 'key':key})
    
    async def server_database_compact(self):
        return await self.__ws_call('/server/database/compact')
    
    async def server_database_backup_post(self, filename: str):
        return await self.__ws_call('/server/database/backup', params={'filename':filename})
    
    async def server_database_backup_delete(self, filename: str):
        return await self.__ws_call('/server/database/backup', params={'filename':filename})
    
    async def server_database_restore(self, filename: str):
        return await self.__ws_call('/server/database/restore', params={'filename':filename})
    
    async def debug_database_list(self):
        return await self.__ws_call('/debug/database/list')
    
    async def debug_database_item(self, namespace: str, key: str = None):
        return await self.__ws_call('/debug/database/item', params={'namespace':namespace, 'key':key})
    
    async def debug_database_item_post(self, namespace: str, key: str, value: any):
        return await self.__ws_call('/debug/database/item', params={'namespace':namespace, 'key':key, 'value':value})
    
    async def debug_database_item_delete(self, namespace: str, key: str):
        return await self.__ws_call('/debug/database/item', params={'namespace':namespace, 'key':key})
    
    async def debug_database_table(self, table: str):
        return await self.__ws_call('/debug/database/table', params={'table':table})
    
    async def server_job_queue_status(self):
        return await self.__ws_call('/server/job_queue/status')
    
    async def server_job_queue_job_post(self, filenames: list[str], reset: bool = False):
        return await self.__ws_call('/server/job_queue/job', params={'filenames':filenames, 'reset':reset})
    
    async def server_job_queue_job_delete(self, job_ids: list[str], all: bool = False):
        return await self.__ws_call('/server/job_queue/job', params={'job_ids':job_ids, 'all':all})
    
    async def server_job_queue_pause(self):
        return await self.__ws_call('/server/job_queue/pause')
    
    async def server_job_queue_start(self):
        return await self.__ws_call('/server/job_queue/start')
    
    async def server_job_queue_jump(self, job_id: str):
        return await self.__ws_call('/server/job_queue/jump', params={'job_id':job_id})
    
    async def server_history_list(self, limit: int = 50, start: int = 0, before: float = None, since: float = None, order: str = "desc"):
        return await self.__ws_call('/server/history/list', params={'limit':limit, 'start':start, 'before':before, 'since':since, 'order':order})
    
    async def server_history_totals(self):
        return await self.__ws_call('/server/history/totals')
    
    async def server_history_reset_totals(self):
        return await self.__ws_call('/server/history/reset_totals')
    
    async def server_history_job(self, uid: str):
        return await self.__ws_call('/server/history/job', params={'uid':uid})
    
    async def server_history_job_delete(self, uid: str, all: bool = False):
        return await self.__ws_call('/server/history/job', params={'uid':uid, 'all':all})
    
    async def server_announcements_list(self, include_dismissed: bool = False):
        return await self.__ws_call('/server/announcements/list', params={'include_dismissed':include_dismissed})
    
    async def server_announcements_update(self):
        return await self.__ws_call('/server/announcements/update')
    
    async def server_announcements_dismiss(self, entry_id: str, wake_time: float = None):
        return await self.__ws_call('/server/announcements/dismiss', params={'entry_id':entry_id, 'wake_time':wake_time})
    
    async def server_announcements_feeds(self):
        return await self.__ws_call('/server/announcements/feeds')
    
    async def server_announcements_feed_post(self, name: str):
        return await self.__ws_call('/server/announcements/feed', params={'name':name})
    
    async def server_announcements_feed_delete(self, name: str):
        return await self.__ws_call('/server/announcements/feed', params={'name':name})
    
    async def server_webcams_list(self):
        return await self.__ws_call('/server/webcams/list')
    
    async def server_webcams_item(self, uid: str):
        return await self.__ws_call('/server/webcams/item', params={'uid':uid})
    
    async def server_webcams_item_post(self, params: dict):
        return await self.__ws_call('/server/webcams/item', params=params)
    
    async def server_webcams_item_delete(self, uid: str):
        return await self.__ws_call('/server/webcams/item', params={'uid':uid})
    
    async def server_webcams_test(self, uid: str):
        return await self.__ws_call('/server/webcams/test', params={'uid':uid})
    
    async def machine_update_status(self):
        return await self.__ws_call('/machine/update/status')
    
    async def machine_update_refresh(self, name: str):
        return await self.__ws_call('/machine/update/refresh', params={'name':name})
    
    async def machine_update_upgrade(self, name: str):
        return await self.__ws_call('/machine/update/upgrade', params={'name':name})
    
    async def machine_update_recover(self, name: str, hard: bool = False):
        return await self.__ws_call('/machine/update/recover', params={'name':name, 'hard':hard})
    
    async def machine_update_rollback(self, name: str):
        return await self.__ws_call('/machine/update/rollback', params={'name':name})
    
    async def machine_update_full(self):
        return await self.__ws_call('/machine/update/full')
    
    async def machine_update_moonraker(self):
        return await self.__ws_call('/machine/update/moonraker')
    
    async def machine_update_klipper(self):
        return await self.__ws_call('/machine/update/klipper')
    
    async def machine_update_client(self, name: str):
        return await self.__ws_call('/machine/update/client', params={'name':name})
    
    async def machine_update_system(self):
        return await self.__ws_call('/machine/update/system')
    
    async def machine_device_power_devices(self):
        return await self.__ws_call('/machine/device_power/devices')
    
    async def machine_device_power_device(self, device: str):
        return await self.__ws_call('/machine/device_power/device', params={'device':device})
    
    async def machine_device_power_device_post(self, device: str, action: str):
        return await self.__ws_call('/machine/device_power/device', params={'device':device, 'action':action})
    
    async def machine_device_power_status(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return await self.__ws_call('/machine/device_power/status', params=params)
    
    async def machine_device_power_on(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return await self.__ws_call('/machine/device_power/on', params=params)
    
    async def machine_device_power_off(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return await self.__ws_call('/machine/device_power/off', params=params)
    
    async def machine_wled_strips(self):
        return await self.__ws_call('/machine/wled/strips')
    
    async def machine_wled_status(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/status', params=params)
    
    async def machine_wled_on(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/on', params=params)
    
    async def machine_wled_off(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/off', params=params)
    
    async def machine_wled_toggle(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/toggle', params=params)
    
    async def machine_wled_strip(self, strip: str):
        return await self.__ws_call('/machine/wled/strip', params={'strip':strip})
    
    async def machine_wled_strip_post(self, params: dict):
        return await self.__ws_call('/machine/wled/strip', params=params)
    
    async def server_sensors_list(self, extended: bool = False):
        return await self.__ws_call('/server/sensors/list', params={'extended':extended})
    
    async def server_sensors_info(self, sensor: str, extended: bool = False):
        return await self.__ws_call('/server/sensors/info', params={'sensor':sensor, 'extended':extended})
    
    async def server_sensors_measurements(self, sensor: str = None):
        return await self.__ws_call('/server/sensors/measurements', params={'sensor': sensor})
    
    async def server_mqtt_publish(self, topic: str, payload: any = None, qos: int = None, retain: bool = False, timeout: float = None):
        params = {'topic': topic, 'payload': payload, 'qos': qos, 'retain': retain, 'timeout': timeout}
        return await self.__ws_call('/server/mqtt/publish', params=params)
    
    async def server_mqtt_subscribe(self, topic: str, qos: int = None, timeout: float = None):
        return await self.__ws_call('/server/mqtt/subscribe', params={'topic': topic, 'qos': qos, 'timeout': timeout})
    
    async def server_notifiers_list(self):
        return await self.__ws_call('/server/notifiers/list')
    
    async def debug_notifiers_test(self, name: str):
        return await self.__ws_call('/debug/notifiers/test', params={'name': name})
    
    async def server_spoolman_status(self):
        return await self.__ws_call('/server/spoolman/status')
    
    async def server_spoolman_spool_id_post(self, spool_id: int = None):
        return await self.__ws_call('/server/spoolman/spool_id', params={'spool_id': spool_id})
    
    async def server_spoolman_spool_id(self):
        return await self.__ws_call('/server/spoolman/spool_id')
    
    async def server_spoolman_proxy(self, request_method: str, path: str, query: str = None, body: dict = None, use_v2_response: bool = False):
        return await self.__ws_call('/server/spoolman/proxy', params={'request_method': request_method, 'path': path, 'query': query, 'body': body, 'use_v2_response': use_v2_response})
    
    async def server_analysis_status(self):
        return await self.__ws_call('/server/analysis/status')
    
    async def server_analysis_estimate(self, filename: str, estimator_config: str = "", update_metadata: bool = False):
        return await self.__ws_call('/server/analysis/estimate', params={'filename': filename, 'estimator_config': estimator_config, 'update_metadata': update_metadata})
    
    async def server_analysis_dump_config(self, dest_config: str = None):
        return await self.__ws_call('/server/analysis/dump_config', params={'dest_config': dest_config})
    
    async def api_version(self):
        return await self.__ws_call('/api/version')
    
    async def api_server(self):
        return await self.__ws_call('/api/server')
    
    async def api_login(self):
        return await self.__ws_call('/api/login')
    
    async def api_settings(self):
        return await self.__ws_call
    
    async def api_files_local(self, filename: str, file: bytes, root: str = 'gcodes', path: str = None, checksum: str = None, print: bool = False):
        files = {'file': (filename, file, 'application/octet-stream')}
        data = {'root': root, 'path': path, 'checksum': checksum, 'print': str(print).lower()}
        return await self.__ws_call('/api/files/upload', params={'files':files, 'data':data}, as_file_upload=True)('/api/settings')
    
    async def api_job(self):
        return await self.__ws_call('/api/job')
    
    async def api_printer(self):
        return await self.__ws_call('/api/printer')
    
    async def api_printer_command(self, commands: list[str]):
        return await self.__ws_call('/api/printer/command', params={'commands': commands})
    
    async def api_printerprofiles(self):
        return await self.__ws_call('/api/printerprofiles')
    
    async def server_extensions_list(self):
        return await self.__ws_call('/server/extensions/list')
    
    async def server_extensions_request(self, agent: str, method: str, arguments: dict = None):
        return await self.__ws_call('/server/extensions/request', params={'agent': agent, 'method': method, 'arguments': arguments})
