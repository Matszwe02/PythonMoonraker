import json
import websockets
import random
import asyncio
import threading
from typing import Callable, Any


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
        self._event_loop = None
        self._loop_thread = None
        self._message_handler: Callable = None
        self._receive_task = None

        if not self.url.startswith('ws://'):
            self.url = 'ws://' + self.url
        if ':' not in self.url.replace('://', ''):
            self.url += ':7125'
        if not self.url.endswith('/websocket'):
            self.url = self.url.rstrip('/') + '/websocket'

    def _run_async_in_thread(self, coro):
        """Runs an async coroutine in the dedicated event loop thread."""
        if not self._event_loop or not self._loop_thread.is_alive():
            raise RuntimeError("WebSocket loop is not running. Call start_websocket_loop first.")
        
        # Submit the coroutine to the event loop and wait for its result
        future = asyncio.run_coroutine_threadsafe(coro, self._event_loop)
        return future.result()

    async def _async_ws_connect(self):
        """Establish WebSocket connection (async version)"""
        try:
            self.ws = await websockets.connect(self.url)
            print(f"Successfully connected to WebSocket: {self.url}")
            return True
        except Exception as e:
            print(f"Error connecting to WebSocket: {e}")
            self.ws = None
            return False

    def ws_connect(self):
        """Establish WebSocket connection (sync wrapper)"""
        return self._run_async_in_thread(self._async_ws_connect())

    async def _async_ws_close(self):
        """Close WebSocket connection (async version)"""
        if self.ws:
            await self.ws.close()
            self.ws = None
            print("WebSocket connection closed.")

    def ws_close(self):
        """Close WebSocket connection (sync wrapper)"""
        if self._loop_thread and self._loop_thread.is_alive():
            self._run_async_in_thread(self._async_ws_close())
        else:
            print("WebSocket loop not running, no connection to close.")


    async def _async_ws_receive(self):
        """Receive and process messages (async version)"""
        while True:
            if not self.ws:
                print("WebSocket not connected, attempting to reconnect...")
                if not await self._async_ws_connect():
                    await asyncio.sleep(5) # Wait before retrying
                    continue

            try:
                message = await self.ws.recv()
                data = json.loads(message)
                if self._message_handler:
                    # If the handler is async, await it. Otherwise, just call it.
                    if asyncio.iscoroutinefunction(self._message_handler):
                        await self._message_handler(data)
                    else:
                        self._message_handler(data)
            except websockets.exceptions.ConnectionClosedOK:
                print("WebSocket connection closed gracefully.")
                self.ws = None
                break
            except websockets.exceptions.ConnectionClosedError as e:
                print(f"WebSocket connection closed with error: {e}, attempting to reconnect...")
                self.ws = None
                await asyncio.sleep(5) # Wait before retrying
            except Exception as e:
                print(f"Error receiving message: {e}")
                await asyncio.sleep(1) # Avoid busy-waiting on errors


    def start_websocket_loop(self, message_handler: Callable):
        """
        Starts the asyncio event loop in a separate thread and establishes
        the WebSocket connection, then begins receiving messages.
        """
        if self._loop_thread and self._loop_thread.is_alive():
            print("WebSocket loop is already running.")
            return

        self._message_handler = message_handler
        self._event_loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(target=self._run_loop_forever, daemon=True)
        self._loop_thread.start()
        
        # Schedule initial connection and receive task in the new loop
        self._run_async_in_thread(self._initial_setup())


    async def _initial_setup(self):
        """Internal async method to connect and start receiving."""
        await self._async_ws_connect()
        if self.ws:
            self._receive_task = self._event_loop.create_task(self._async_ws_receive())

    def _run_loop_forever(self):
        """Target function for the thread to run the asyncio event loop."""
        asyncio.set_event_loop(self._event_loop)
        self._event_loop.run_forever()

    def stop_websocket_loop(self):
        """Stops the asyncio event loop and closes the WebSocket connection."""
        if self._event_loop and self._event_loop.is_running():
            # Cancel the receive task if it's running
            if self._receive_task:
                self._event_loop.call_soon_threadsafe(self._receive_task.cancel)
            
            # Close the websocket connection
            self._event_loop.call_soon_threadsafe(lambda: asyncio.create_task(self._async_ws_close()))
            
            # Stop the event loop
            self._event_loop.call_soon_threadsafe(self._event_loop.stop)
            self._loop_thread.join(timeout=5) # Wait for the thread to finish
            if self._loop_thread.is_alive():
                print("Warning: WebSocket loop thread did not terminate gracefully.")
            print("WebSocket loop stopped.")
        else:
            print("WebSocket loop is not running.")


    async def __ws_call(self, path:str, params: dict = {}, as_file_upload: bool = False, output_format: Any = None):
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
            return None


    def server_info(self):
        return self._run_async_in_thread(self._async_server_info())
    def server_config(self):
        return self._run_async_in_thread(self._async_server_config())
    def server_temperature_store(self, include_monitors=False):
        return self._run_async_in_thread(self._async_server_temperature_store(include_monitors))
    def server_gcode_store(self, count=100):
        return self._run_async_in_thread(self._async_server_gcode_store(count))
    def server_logs_rollover(self, application='moonraker'):
        return self._run_async_in_thread(self._async_server_logs_rollover(application))
    def server_restart(self):
        return self._run_async_in_thread(self._async_server_restart())
    def printer_info(self):
        return self._run_async_in_thread(self._async_printer_info())
    def printer_emergency_stop(self):
        return self._run_async_in_thread(self._async_printer_emergency_stop())
    def printer_restart(self):
        return self._run_async_in_thread(self._async_printer_restart())
    def printer_firmware_restart(self):
        return self._run_async_in_thread(self._async_printer_firmware_restart())
    def printer_objects_list(self):
        return self._run_async_in_thread(self._async_printer_objects_list())
    def printer_objects_query(self, objects: dict):
        return self._run_async_in_thread(self._async_printer_objects_query(objects))
    def printer_objects_subscribe(self, objects: dict):
        return self._run_async_in_thread(self._async_printer_objects_subscribe(objects))
    def printer_query_endstops_status(self):
        return self._run_async_in_thread(self._async_printer_query_endstops_status())
    def printer_gcode_script(self, script: str):
        return self._run_async_in_thread(self._async_printer_gcode_script(script))
    def printer_gcode_help(self):
        return self._run_async_in_thread(self._async_printer_gcode_help())
    def printer_print_start(self, filename: str):
        return self._run_async_in_thread(self._async_printer_print_start(filename))
    def printer_print_pause(self):
        return self._run_async_in_thread(self._async_printer_print_pause())
    def printer_print_resume(self):
        return self._run_async_in_thread(self._async_printer_print_resume())
    def printer_print_cancel(self):
        return self._run_async_in_thread(self._async_printer_print_cancel())
    def machine_system_info(self):
        return self._run_async_in_thread(self._async_machine_system_info())
    def machine_shutdown(self):
        return self._run_async_in_thread(self._async_machine_shutdown())
    def machine_reboot(self):
        return self._run_async_in_thread(self._async_machine_reboot())
    def machine_services_restart(self, service: str):
        return self._run_async_in_thread(self._async_machine_services_restart(service))
    def machine_services_stop(self, service: str):
        return self._run_async_in_thread(self._async_machine_services_stop(service))
    def machine_services_start(self, service: str):
        return self._run_async_in_thread(self._async_machine_services_start(service))
    def machine_proc_stats(self):
        return self._run_async_in_thread(self._async_machine_proc_stats())
    def machine_sudo_info(self, check_access=False):
        return self._run_async_in_thread(self._async_machine_sudo_info(check_access))
    def machine_sudo_password(self, password: str):
        return self._run_async_in_thread(self._async_machine_sudo_password(password))
    def machine_peripherals_usb(self):
        return self._run_async_in_thread(self._async_machine_peripherals_usb())
    def machine_peripherals_serial(self):
        return self._run_async_in_thread(self._async_machine_peripherals_serial())
    def machine_peripherals_video(self):
        return self._run_async_in_thread(self._async_machine_peripherals_video())
    def machine_peripherals_canbus(self, interface='can0'):
        return self._run_async_in_thread(self._async_machine_peripherals_canbus(interface))
    def server_files_list(self, root='gcodes'):
        return self._run_async_in_thread(self._async_server_files_list(root))
    def server_files_roots(self):
        return self._run_async_in_thread(self._async_server_files_roots())
    def server_files_metadata(self, filename: str):
        return self._run_async_in_thread(self._async_server_files_metadata(filename))
    def server_files_metadata_post(self, filename: str):
        return self._run_async_in_thread(self._async_server_files_metadata_post(filename))
    def server_files_thumbnails(self, filename: str):
        return self._run_async_in_thread(self._async_server_files_thumbnails(filename))
    def server_files_directory(self, path = 'gcodes', extended = False):
        return self._run_async_in_thread(self._async_server_files_directory(path , extended ))
    def server_files_directory_post(self, path: str):
        return self._run_async_in_thread(self._async_server_files_directory_post(path))
    def server_files_directory_delete(self, path: str, force = False):
        return self._run_async_in_thread(self._async_server_files_directory_delete(path, force ))
    def server_files_move(self, source: str, dest: str):
        return self._run_async_in_thread(self._async_server_files_move(source, dest))
    def server_files_copy(self, source: str, dest: str):
        return self._run_async_in_thread(self._async_server_files_copy(source, dest))
    def server_files_zip(self, items: list[str], dest: str, store_only = False):
        return self._run_async_in_thread(self._async_server_files_zip(items[str], dest, store_only ))
    def server_files_delete(self, root: str, filename: str):
        return self._run_async_in_thread(self._async_server_files_delete(root, filename))
    def server_files_klippy_log(self):
        return self._run_async_in_thread(self._async_server_files_klippy_log())
    def server_files_moonraker_log(self):
        return self._run_async_in_thread(self._async_server_files_moonraker_log())
    def access_login(self, username: str, password: str, source = 'moonraker'):
        return self._run_async_in_thread(self._async_access_login(username, password, source ))
    def access_logout(self):
        return self._run_async_in_thread(self._async_access_logout())
    def access_user(self):
        return self._run_async_in_thread(self._async_access_user())
    def access_user_post(self, username: str, password: str):
        return self._run_async_in_thread(self._async_access_user_post(username, password))
    def access_user_delete(self, username: str):
        return self._run_async_in_thread(self._async_access_user_delete(username))
    def access_users_list(self):
        return self._run_async_in_thread(self._async_access_users_list())
    def access_user_password(self, password: str, new_password: str):
        return self._run_async_in_thread(self._async_access_user_password(password, new_password))
    def access_refresh_jwt(self, refresh_token: str):
        return self._run_async_in_thread(self._async_access_refresh_jwt(refresh_token))
    def  access_oneshot_token(self):
        return self._run_async_in_thread(self._async_access_oneshot_token())
    def  access_api_key(self):
        return self._run_async_in_thread(self._async_access_api_key())
    def  access_api_key_post(self):
        return self._run_async_in_thread(self._async_access_api_key_post())
    def server_database_list(self):
        return self._run_async_in_thread(self._async_server_database_list())
    def server_database_item(self, namespace: str, key: str = None):
        return self._run_async_in_thread(self._async_server_database_item(namespace, key ))
    def server_database_item_post(self, namespace: str, key: str, value: any):
        return self._run_async_in_thread(self._async_server_database_item_post(namespace, key, value))
    def server_database_item_delete(self, namespace: str, key: str):
        return self._run_async_in_thread(self._async_server_database_item_delete(namespace, key))
    def server_database_compact(self):
        return self._run_async_in_thread(self._async_server_database_compact())
    def server_database_backup_post(self, filename: str):
        return self._run_async_in_thread(self._async_server_database_backup_post(filename))
    def server_database_backup_delete(self, filename: str):
        return self._run_async_in_thread(self._async_server_database_backup_delete(filename))
    def server_database_restore(self, filename: str):
        return self._run_async_in_thread(self._async_server_database_restore(filename))
    def debug_database_list(self):
        return self._run_async_in_thread(self._async_debug_database_list())
    def debug_database_item(self, namespace: str, key: str = None):
        return self._run_async_in_thread(self._async_debug_database_item(namespace, key ))
    def debug_database_item_post(self, namespace: str, key: str, value: any):
        return self._run_async_in_thread(self._async_debug_database_item_post(namespace, key, value))
    def debug_database_item_delete(self, namespace: str, key: str):
        return self._run_async_in_thread(self._async_debug_database_item_delete(namespace, key))
    def debug_database_table(self, table: str):
        return self._run_async_in_thread(self._async_debug_database_table(table))
    def server_job_queue_status(self):
        return self._run_async_in_thread(self._async_server_job_queue_status())
    def server_job_queue_job_post(self, filenames: list[str], reset: bool = False):
        return self._run_async_in_thread(self._async_server_job_queue_job_post(filenames[str], reset ))
    def server_job_queue_job_delete(self, job_ids: list[str], all: bool = False):
        return self._run_async_in_thread(self._async_server_job_queue_job_delete(job_ids[str], all ))
    def server_job_queue_pause(self):
        return self._run_async_in_thread(self._async_server_job_queue_pause())
    def server_job_queue_start(self):
        return self._run_async_in_thread(self._async_server_job_queue_start())
    def server_job_queue_jump(self, job_id: str):
        return self._run_async_in_thread(self._async_server_job_queue_jump(job_id))
    def server_history_list(self, limit: int = 50, start: int = 0, before: float = None, since: float = None, order: str = "desc"):
        return self._run_async_in_thread(self._async_server_history_list(limit , start , before , since , order ))
    def server_history_totals(self):
        return self._run_async_in_thread(self._async_server_history_totals())
    def server_history_reset_totals(self):
        return self._run_async_in_thread(self._async_server_history_reset_totals())
    def server_history_job(self, uid: str):
        return self._run_async_in_thread(self._async_server_history_job(uid))
    def server_history_job_delete(self, uid: str, all: bool = False):
        return self._run_async_in_thread(self._async_server_history_job_delete(uid, all ))
    def server_announcements_list(self, include_dismissed: bool = False):
        return self._run_async_in_thread(self._async_server_announcements_list(include_dismissed ))
    def server_announcements_update(self):
        return self._run_async_in_thread(self._async_server_announcements_update())
    def server_announcements_dismiss(self, entry_id: str, wake_time: float = None):
        return self._run_async_in_thread(self._async_server_announcements_dismiss(entry_id, wake_time ))
    def server_announcements_feeds(self):
        return self._run_async_in_thread(self._async_server_announcements_feeds())
    def server_announcements_feed_post(self, name: str):
        return self._run_async_in_thread(self._async_server_announcements_feed_post(name))
    def server_announcements_feed_delete(self, name: str):
        return self._run_async_in_thread(self._async_server_announcements_feed_delete(name))
    def server_webcams_list(self):
        return self._run_async_in_thread(self._async_server_webcams_list())
    def server_webcams_item(self, uid: str):
        return self._run_async_in_thread(self._async_server_webcams_item(uid))
    def server_webcams_item_post(self, params: dict):
        return self._run_async_in_thread(self._async_server_webcams_item_post(params))
    def server_webcams_item_delete(self, uid: str):
        return self._run_async_in_thread(self._async_server_webcams_item_delete(uid))
    def server_webcams_test(self, uid: str):
        return self._run_async_in_thread(self._async_server_webcams_test(uid))
    def machine_update_status(self):
        return self._run_async_in_thread(self._async_machine_update_status())
    def machine_update_refresh(self, name: str):
        return self._run_async_in_thread(self._async_machine_update_refresh(name))
    def machine_update_upgrade(self, name: str):
        return self._run_async_in_thread(self._async_machine_update_upgrade(name))
    def machine_update_recover(self, name: str, hard: bool = False):
        return self._run_async_in_thread(self._async_machine_update_recover(name, hard ))
    def machine_update_rollback(self, name: str):
        return self._run_async_in_thread(self._async_machine_update_rollback(name))
    def machine_update_full(self):
        return self._run_async_in_thread(self._async_machine_update_full())
    def machine_update_moonraker(self):
        return self._run_async_in_thread(self._async_machine_update_moonraker())
    def machine_update_klipper(self):
        return self._run_async_in_thread(self._async_machine_update_klipper())
    def machine_update_client(self, name: str):
        return self._run_async_in_thread(self._async_machine_update_client(name))
    def machine_update_system(self):
        return self._run_async_in_thread(self._async_machine_update_system())
    def machine_device_power_devices(self):
        return self._run_async_in_thread(self._async_machine_device_power_devices())
    def machine_device_power_device(self, device: str):
        return self._run_async_in_thread(self._async_machine_device_power_device(device))
    def machine_device_power_device_post(self, device: str, action: str):
        return self._run_async_in_thread(self._async_machine_device_power_device_post(device, action))
    def machine_device_power_status(self, devices: list[str]):
        return self._run_async_in_thread(self._async_machine_device_power_status(devices[str]))
    def machine_device_power_on(self, devices: list[str]):
        return self._run_async_in_thread(self._async_machine_device_power_on(devices[str]))
    def machine_device_power_off(self, devices: list[str]):
        return self._run_async_in_thread(self._async_machine_device_power_off(devices[str]))
    def machine_wled_strips(self):
        return self._run_async_in_thread(self._async_machine_wled_strips())
    def machine_wled_status(self, strips: list[str]):
        return self._run_async_in_thread(self._async_machine_wled_status(strips[str]))
    def machine_wled_on(self, strips: list[str]):
        return self._run_async_in_thread(self._async_machine_wled_on(strips[str]))
    def machine_wled_off(self, strips: list[str]):
        return self._run_async_in_thread(self._async_machine_wled_off(strips[str]))
    def machine_wled_toggle(self, strips: list[str]):
        return self._run_async_in_thread(self._async_machine_wled_toggle(strips[str]))
    def machine_wled_strip(self, strip: str):
        return self._run_async_in_thread(self._async_machine_wled_strip(strip))
    def machine_wled_strip_post(self, params: dict):
        return self._run_async_in_thread(self._async_machine_wled_strip_post(params))
    def server_sensors_list(self, extended: bool = False):
        return self._run_async_in_thread(self._async_server_sensors_list(extended ))
    def server_sensors_info(self, sensor: str, extended: bool = False):
        return self._run_async_in_thread(self._async_server_sensors_info(sensor, extended ))
    def server_sensors_measurements(self, sensor: str = None):
        return self._run_async_in_thread(self._async_server_sensors_measurements(sensor ))
    def server_mqtt_publish(self, topic: str, payload: any = None, qos: int = None, retain: bool = False, timeout: float = None):
        return self._run_async_in_thread(self._async_server_mqtt_publish(topic, payload , qos , retain , timeout ))
    def server_mqtt_subscribe(self, topic: str, qos: int = None, timeout: float = None):
        return self._run_async_in_thread(self._async_server_mqtt_subscribe(topic, qos , timeout ))
    def server_notifiers_list(self):
        return self._run_async_in_thread(self._async_server_notifiers_list())
    def debug_notifiers_test(self, name: str):
        return self._run_async_in_thread(self._async_debug_notifiers_test(name))
    def server_spoolman_status(self):
        return self._run_async_in_thread(self._async_server_spoolman_status())
    def server_spoolman_spool_id_post(self, spool_id: int = None):
        return self._run_async_in_thread(self._async_server_spoolman_spool_id_post(spool_id ))
    def server_spoolman_spool_id(self):
        return self._run_async_in_thread(self._async_server_spoolman_spool_id())
    def server_spoolman_proxy(self, request_method: str, path: str, query: str = None, body: dict = None, use_v2_response: bool = False):
        return self._run_async_in_thread(self._async_server_spoolman_proxy(request_method, path, query , body , use_v2_response ))
    def server_analysis_status(self):
        return self._run_async_in_thread(self._async_server_analysis_status())
    def server_analysis_estimate(self, filename: str, estimator_config: str = "", update_metadata: bool = False):
        return self._run_async_in_thread(self._async_server_analysis_estimate(filename, estimator_config , update_metadata ))
    def server_analysis_dump_config(self, dest_config: str = None):
        return self._run_async_in_thread(self._async_server_analysis_dump_config(dest_config ))
    def api_version(self):
        return self._run_async_in_thread(self._async_api_version())
    def api_server(self):
        return self._run_async_in_thread(self._async_api_server())
    def api_login(self):
        return self._run_async_in_thread(self._async_api_login())
    def api_settings(self):
        return self._run_async_in_thread(self._async_api_settings())
    def api_files_local(self, filename: str, file: bytes, root: str = 'gcodes', path: str = None, checksum: str = None, print: bool = False):
        return self._run_async_in_thread(self._async_api_files_local(filename, file, root , path , checksum , print ))
    def api_job(self):
        return self._run_async_in_thread(self._async_api_job())
    def api_printer(self):
        return self._run_async_in_thread(self._async_api_printer())
    def api_printer_command(self, commands: list[str]):
        return self._run_async_in_thread(self._async_api_printer_command(commands[str]))
    def api_printerprofiles(self):
        return self._run_async_in_thread(self._async_api_printerprofiles())
    def server_extensions_list(self):
        return self._run_async_in_thread(self._async_server_extensions_list())
    def server_extensions_request(self, agent: str, method: str, arguments: dict = None):
        return self._run_async_in_thread(self._async_server_extensions_request(agent, method, arguments ))



    async def _async_server_info(self):
        return await self.__ws_call('/server/info')
    
    async def _async_server_config(self):
        return await self.__ws_call('/server/config')
    
    async def _async_server_temperature_store(self, include_monitors=False):
        return await self.__ws_call('/server/temperature_store', params={'include_monitors':include_monitors})
    
    async def _async_server_gcode_store(self, count=100):
        return await self.__ws_call('/server/gcode_store', params={'count':count})
    
    async def _async_server_logs_rollover(self, application='moonraker'):
        return await self.__ws_call('/server/logs/rollover', params={'application':application})
    
    async def _async_server_restart(self):
        return await self.__ws_call('/server/restart')
    
    async def _async_printer_info(self):
        return await self.__ws_call('/printer/info')
    
    async def _async_printer_emergency_stop(self):
        return await self.__ws_call('/printer/emergency_stop')
    
    async def _async_printer_restart(self):
        return await self.__ws_call('/printer/restart')
    
    async def _async_printer_firmware_restart(self):
        return await self.__ws_call('/printer/firmware_restart')
    
    async def _async_printer_objects_list(self):
        return await self.__ws_call('/printer/objects/list')
    
    async def _async_printer_objects_query(self, objects: dict):
        return await self.__ws_call('/printer/objects/query', params={'objects':objects})
    
    async def _async_printer_objects_subscribe(self, objects: dict):
        return await self.__ws_call('/printer/objects/subscribe', params={'objects':objects})
    
    async def _async_printer_query_endstops_status(self):
        return await self.__ws_call('/printer/query_endstops/status')
    
    async def _async_printer_gcode_script(self, script: str):
        return await self.__ws_call('/printer/gcode/script', params={'script':script})
    
    async def _async_printer_gcode_help(self):
        return await self.__ws_call('/printer/gcode/help')
    
    async def _async_printer_print_start(self, filename: str):
        return await self.__ws_call('/printer/print/start', params={'filename':filename})
    
    async def _async_printer_print_pause(self):
        return await self.__ws_call('/printer/print/pause')
    
    async def _async_printer_print_resume(self):
        return await self.__ws_call('/printer/print/resume')
    
    async def _async_printer_print_cancel(self):
        return await self.__ws_call('/printer/print/cancel')
    
    async def _async_machine_system_info(self):
        return await self.__ws_call('/machine/system_info')
    
    async def _async_machine_shutdown(self):
        return await self.__ws_call('/machine/shutdown')
    
    async def _async_machine_reboot(self):
        return await self.__ws_call('/machine/reboot')
    
    async def _async_machine_services_restart(self, service: str):
        return await self.__ws_call('/machine/services/restart', params={'service':service})
    
    async def _async_machine_services_stop(self, service: str):
        return await self.__ws_call('/machine/services/stop', params={'service':service})
    
    async def _async_machine_services_start(self, service: str):
        return await self.__ws_call('/machine/services/start', params={'service':service})
    
    async def _async_machine_proc_stats(self):
        return await self.__ws_call('/machine/proc_stats')
    
    async def _async_machine_sudo_info(self, check_access=False):
        return await self.__ws_call('/machine/sudo/info', params={'check_access':check_access})
    
    async def _async_machine_sudo_password(self, password: str):
        return await self.__ws_call('/machine/sudo/password', params={'password':password})
    
    async def _async_machine_peripherals_usb(self):
        return await self.__ws_call('/machine/peripherals/usb')
    
    async def _async_machine_peripherals_serial(self):
        return await self.__ws_call('/machine/peripherals/serial')
    
    async def _async_machine_peripherals_video(self):
        return await self.__ws_call('/machine/peripherals/video')
    
    async def _async_machine_peripherals_canbus(self, interface='can0'):
        return await self.__ws_call('/machine/peripherals/canbus', params={'interface':interface})
    
    async def _async_server_files_list(self, root='gcodes'):
        return await self.__ws_call('/server/files/list', params={'root':root})
    
    async def _async_server_files_roots(self):
        return await self.__ws_call('/server/files/roots')
    
    async def _async_server_files_metadata(self, filename: str):
        return await self.__ws_call('/server/files/metadata', params={'filename':filename})
    
    async def _async_server_files_metadata_post(self, filename: str):
        return await self.__ws_call('/server/files/metadata', params={'filename':filename})
    
    async def _async_server_files_thumbnails(self, filename: str):
        return await self.__ws_call('/server/files/thumbnails', params={'filename':filename})
    
    async def _async_server_files_directory(self, path = 'gcodes', extended = False):
        return await self.__ws_call('/server/files/directory', params={'path':path, 'extended':extended})
    
    async def _async_server_files_directory_post(self, path: str):
        return await self.__ws_call('/server/files/directory', params={'path':path})
    
    async def _async_server_files_directory_delete(self, path: str, force = False):
        return await self.__ws_call('/server/files/directory', params={'path':path, 'force':force})
    
    async def _async_server_files_move(self, source: str, dest: str):
        return await self.__ws_call('/server/files/move', params={'source':source, 'dest':dest})
    
    async def _async_server_files_copy(self, source: str, dest: str):
        return await self.__ws_call('/server/files/copy', params={'source':source, 'dest':dest})
    
    async def _async_server_files_zip(self, items: list[str], dest: str, store_only = False):
        return await self.__ws_call('/server/files/zip', params={'items':items, 'dest':dest, 'store_only':store_only})
    
    async def _async_server_files_delete(self, root: str, filename: str):
        return await self.__ws_call(f'/server/files/{root}/{filename}')
    
    async def _async_server_files_klippy_log(self):
        return await self.__ws_call(f'/server/files/klippy.log', output_format=bytes)
    
    async def _async_server_files_moonraker_log(self):
        return await self.__ws_call(f'/server/files/moonraker.log', output_format=bytes)
    
    async def _async_access_login(self, username: str, password: str, source = 'moonraker'):
        return await self.__ws_call(f'/access/login', params={'username':username, 'password':password, 'source':source})
    
    async def _async_access_logout(self):
        return await self.__ws_call(f'/access/logout')
    
    async def _async_access_user(self):
        return await self.__ws_call(f'/access/user')
    
    async def _async_access_user_post(self, username: str, password: str):
        return await self.__ws_call(f'/access/user', params={'username':username, 'password':password})
    
    async def _async_access_user_delete(self, username: str):
        return await self.__ws_call(f'/access/user', params={'username':username})
    
    async def _async_access_users_list(self):
        return await self.__ws_call(f'/access/users/list')
    
    async def _async_access_user_password(self, password: str, new_password: str):
        return await self.__ws_call(f'/access/user/password', params={'password':password, 'new_password':new_password})
    
    async def _async_access_refresh_jwt(self, refresh_token: str):
        return await self.__ws_call(f'/access/refresh_jwt', params={'refresh_token':refresh_token})
    
    async def _async_access_oneshot_token(self):
        return await self.__ws_call(f'/access/oneshot_token', output_format=str)
    
    async def _async_access_api_key(self):
        return await self.__ws_call(f'/access/api_key', output_format=str)
    
    async def _async_access_api_key_post(self):
        return await self.__ws_call(f'/access/api_key', output_format=str)
    
    async def _async_server_database_list(self):
        return await self.__ws_call('/server/database/list')
    
    async def _async_server_database_item(self, namespace: str, key: str = None):
        return await self.__ws_call('/server/database/item', params={'namespace':namespace, 'key':key})
    
    async def _async_server_database_item_post(self, namespace: str, key: str, value: any):
        return await self.__ws_call('/server/database/item', params={'namespace':namespace, 'key':key, 'value':value})
    
    async def _async_server_database_item_delete(self, namespace: str, key: str):
        return await self.__ws_call('/server/database/item', params={'namespace':namespace, 'key':key})
    
    async def _async_server_database_compact(self):
        return await self.__ws_call('/server/database/compact')
    
    async def _async_server_database_backup_post(self, filename: str):
        return await self.__ws_call('/server/database/backup', params={'filename':filename})
    
    async def _async_server_database_backup_delete(self, filename: str):
        return await self.__ws_call('/server/database/backup', params={'filename':filename})
    
    async def _async_server_database_restore(self, filename: str):
        return await self.__ws_call('/server/database/restore', params={'filename':filename})
    
    async def _async_debug_database_list(self):
        return await self.__ws_call('/debug/database/list')
    
    async def _async_debug_database_item(self, namespace: str, key: str = None):
        return await self.__ws_call('/debug/database/item', params={'namespace':namespace, 'key':key})
    
    async def _async_debug_database_item_post(self, namespace: str, key: str, value: any):
        return await self.__ws_call('/debug/database/item', params={'namespace':namespace, 'key':key, 'value':value})
    
    async def _async_debug_database_item_delete(self, namespace: str, key: str):
        return await self.__ws_call('/debug/database/item', params={'namespace':namespace, 'key':key})
    
    async def _async_debug_database_table(self, table: str):
        return await self.__ws_call('/debug/database/table', params={'table':table})
    
    async def _async_server_job_queue_status(self):
        return await self.__ws_call('/server/job_queue/status')
    
    async def _async_server_job_queue_job_post(self, filenames: list[str], reset: bool = False):
        return await self.__ws_call('/server/job_queue/job', params={'filenames':filenames, 'reset':reset})
    
    async def _async_server_job_queue_job_delete(self, job_ids: list[str], all: bool = False):
        return await self.__ws_call('/server/job_queue/job', params={'job_ids':job_ids, 'all':all})
    
    async def _async_server_job_queue_pause(self):
        return await self.__ws_call('/server/job_queue/pause')
    
    async def _async_server_job_queue_start(self):
        return await self.__ws_call('/server/job_queue/start')
    
    async def _async_server_job_queue_jump(self, job_id: str):
        return await self.__ws_call('/server/job_queue/jump', params={'job_id':job_id})
    
    async def _async_server_history_list(self, limit: int = 50, start: int = 0, before: float = None, since: float = None, order: str = "desc"):
        return await self.__ws_call('/server/history/list', params={'limit':limit, 'start':start, 'before':before, 'since':since, 'order':order})
    
    async def _async_server_history_totals(self):
        return await self.__ws_call('/server/history/totals')
    
    async def _async_server_history_reset_totals(self):
        return await self.__ws_call('/server/history/reset_totals')
    
    async def _async_server_history_job(self, uid: str):
        return await self.__ws_call('/server/history/job', params={'uid':uid})
    
    async def _async_server_history_job_delete(self, uid: str, all: bool = False):
        return await self.__ws_call('/server/history/job', params={'uid':uid, 'all':all})
    
    async def _async_server_announcements_list(self, include_dismissed: bool = False):
        return await self.__ws_call('/server/announcements/list', params={'include_dismissed':include_dismissed})
    
    async def _async_server_announcements_update(self):
        return await self.__ws_call('/server/announcements/update')
    
    async def _async_server_announcements_dismiss(self, entry_id: str, wake_time: float = None):
        return await self.__ws_call('/server/announcements/dismiss', params={'entry_id':entry_id, 'wake_time':wake_time})
    
    async def _async_server_announcements_feeds(self):
        return await self.__ws_call('/server/announcements/feeds')
    
    async def _async_server_announcements_feed_post(self, name: str):
        return await self.__ws_call('/server/announcements/feed', params={'name':name})
    
    async def _async_server_announcements_feed_delete(self, name: str):
        return await self.__ws_call('/server/announcements/feed', params={'name':name})
    
    async def _async_server_webcams_list(self):
        return await self.__ws_call('/server/webcams/list')
    
    async def _async_server_webcams_item(self, uid: str):
        return await self.__ws_call('/server/webcams/item', params={'uid':uid})
    
    async def _async_server_webcams_item_post(self, params: dict):
        return await self.__ws_call('/server/webcams/item', params=params)
    
    async def _async_server_webcams_item_delete(self, uid: str):
        return await self.__ws_call('/server/webcams/item', params={'uid':uid})
    
    async def _async_server_webcams_test(self, uid: str):
        return await self.__ws_call('/server/webcams/test', params={'uid':uid})
    
    async def _async_machine_update_status(self):
        return await self.__ws_call('/machine/update/status')
    
    async def _async_machine_update_refresh(self, name: str):
        return await self.__ws_call('/machine/update/refresh', params={'name':name})
    
    async def _async_machine_update_upgrade(self, name: str):
        return await self.__ws_call('/machine/update/upgrade', params={'name':name})
    
    async def _async_machine_update_recover(self, name: str, hard: bool = False):
        return await self.__ws_call('/machine/update/recover', params={'name':name, 'hard':hard})
    
    async def _async_machine_update_rollback(self, name: str):
        return await self.__ws_call('/machine/update/rollback', params={'name':name})
    
    async def _async_machine_update_full(self):
        return await self.__ws_call('/machine/update/full')
    
    async def _async_machine_update_moonraker(self):
        return await self.__ws_call('/machine/update/moonraker')
    
    async def _async_machine_update_klipper(self):
        return await self.__ws_call('/machine/update/klipper')
    
    async def _async_machine_update_client(self, name: str):
        return await self.__ws_call('/machine/update/client', params={'name':name})
    
    async def _async_machine_update_system(self):
        return await self.__ws_call('/machine/update/system')
    
    async def _async_machine_device_power_devices(self):
        return await self.__ws_call('/machine/device_power/devices')
    
    async def _async_machine_device_power_device(self, device: str):
        return await self.__ws_call('/machine/device_power/device', params={'device':device})
    
    async def _async_machine_device_power_device_post(self, device: str, action: str):
        return await self.__ws_call('/machine/device_power/device', params={'device':device, 'action':action})
    
    async def _async_machine_device_power_status(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return await self.__ws_call('/machine/device_power/status', params=params)
    
    async def _async_machine_device_power_on(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return await self.__ws_call('/machine/device_power/on', params=params)
    
    async def _async_machine_device_power_off(self, devices: list[str]):
        params = {}
        for device in devices:
            params[device] = None
        return await self.__ws_call('/machine/device_power/off', params=params)
    
    async def _async_machine_wled_strips(self):
        return await self.__ws_call('/machine/wled/strips')
    
    async def _async_machine_wled_status(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/status', params=params)
    
    async def _async_machine_wled_on(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/on', params=params)
    
    async def _async_machine_wled_off(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/off', params=params)
    
    async def _async_machine_wled_toggle(self, strips: list[str]):
        params = {}
        for strip in strips:
            params[strip] = None
        return await self.__ws_call('/machine/wled/toggle', params=params)
    
    async def _async_machine_wled_strip(self, strip: str):
        return await self.__ws_call('/machine/wled/strip', params={'strip':strip})
    
    async def _async_machine_wled_strip_post(self, params: dict):
        return await self.__ws_call('/machine/wled/strip', params=params)
    
    async def _async_server_sensors_list(self, extended: bool = False):
        return await self.__ws_call('/server/sensors/list', params={'extended':extended})
    
    async def _async_server_sensors_info(self, sensor: str, extended: bool = False):
        return await self.__ws_call('/server/sensors/info', params={'sensor':sensor, 'extended':extended})
    
    async def _async_server_sensors_measurements(self, sensor: str = None):
        return await self.__ws_call('/server/sensors/measurements', params={'sensor': sensor})
    
    async def _async_server_mqtt_publish(self, topic: str, payload: any = None, qos: int = None, retain: bool = False, timeout: float = None):
        params = {'topic': topic, 'payload': payload, 'qos': qos, 'retain': retain, 'timeout': timeout}
        return await self.__ws_call('/server/mqtt/publish', params=params)
    
    async def _async_server_mqtt_subscribe(self, topic: str, qos: int = None, timeout: float = None):
        return await self.__ws_call('/server/mqtt/subscribe', params={'topic': topic, 'qos': qos, 'timeout': timeout})
    
    async def _async_server_notifiers_list(self):
        return await self.__ws_call('/server/notifiers/list')
    
    async def _async_debug_notifiers_test(self, name: str):
        return await self.__ws_call('/debug/notifiers/test', params={'name': name})
    
    async def _async_server_spoolman_status(self):
        return await self.__ws_call('/server/spoolman/status')
    
    async def _async_server_spoolman_spool_id_post(self, spool_id: int = None):
        return await self.__ws_call('/server/spoolman/spool_id', params={'spool_id': spool_id})
    
    async def _async_server_spoolman_spool_id(self):
        return await self.__ws_call('/server/spoolman/spool_id')
    
    async def _async_server_spoolman_proxy(self, request_method: str, path: str, query: str = None, body: dict = None, use_v2_response: bool = False):
        return await self.__ws_call('/server/spoolman/proxy', params={'request_method': request_method, 'path': path, 'query': query, 'body': body, 'use_v2_response': use_v2_response})
    
    async def _async_server_analysis_status(self):
        return await self.__ws_call('/server/analysis/status')
    
    async def _async_server_analysis_estimate(self, filename: str, estimator_config: str = "", update_metadata: bool = False):
        return await self.__ws_call('/server/analysis/estimate', params={'filename': filename, 'estimator_config': estimator_config, 'update_metadata': update_metadata})
    
    async def _async_server_analysis_dump_config(self, dest_config: str = None):
        return await self.__ws_call('/server/analysis/dump_config', params={'dest_config': dest_config})
    
    async def _async_api_version(self):
        return await self.__ws_call('/api/version')
    
    async def _async_api_server(self):
        return await self.__ws_call('/api/server')
    
    async def _async_api_login(self):
        return await self.__ws_call('/api/login')
    
    async def _async_api_settings(self):
        return await self.__ws_call
    
    async def _async_api_files_local(self, filename: str, file: bytes, root: str = 'gcodes', path: str = None, checksum: str = None, print: bool = False):
        files = {'file': (filename, file, 'application/octet-stream')}
        data = {'root': root, 'path': path, 'checksum': checksum, 'print': str(print).lower()}
        return await self.__ws_call('/api/files/upload', params={'files':files, 'data':data}, as_file_upload=True)('/api/settings')
    
    async def _async_api_job(self):
        return await self.__ws_call('/api/job')
    
    async def _async_api_printer(self):
        return await self.__ws_call('/api/printer')
    
    async def _async_api_printer_command(self, commands: list[str]):
        return await self.__ws_call('/api/printer/command', params={'commands': commands})
    
    async def _async_api_printerprofiles(self):
        return await self.__ws_call('/api/printerprofiles')
    
    async def _async_server_extensions_list(self):
        return await self.__ws_call('/server/extensions/list')
    
    async def _async_server_extensions_request(self, agent: str, method: str, arguments: dict = None):
        return await self.__ws_call('/server/extensions/request', params={'agent': agent, 'method': method, 'arguments': arguments})
