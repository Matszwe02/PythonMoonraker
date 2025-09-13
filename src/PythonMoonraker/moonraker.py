from api import MoonrakerAPI


class Moonraker:
    def __init__(self, url: str, api = None):
        if not api:
            self.api = MoonrakerAPI(url)
        else:
            self.api = api
        self.last_commands_poll = 0
    
    def send_gcode(self, gcode: str) -> bool:
        resp = self.api.printer_gcode_script(gcode)
        return resp.get('result') == 'ok'
    
    def listdir(self, dir = ''):
        if dir == '':
            resp = self.api.server_files_roots()
            dirs = []
            for dir in resp.get('result', {}):
                dirs.append(dir['name'])
            return dirs, []
        
        resp = self.api.server_files_directory(dir)
        dirs = []
        files = []
        for dir in resp.get('result', {}).get('dirs', {}):
            dirs.append(dir['dirname'])
        for file in resp.get('result', {}).get('files', {}):
            files.append(file['filename'])
        return dirs, files
    
    def mv(self, source: str, dest: str):
        resp = self.api.server_files_move(self, source, dest)
        return resp
    
    def endstops(self):
        resp = self.api.printer_query_endstops_status()
        return resp.get('result', {})
    
    def position(self):
        resp = self.api.printer_objects_query({"gcode_move": None, "toolhead": ["position", "status"]})
        # resp = self.api.printer_objects_query({"toolhead": ["position", "status"]})
        return resp 
    
    def paused(self):
        resp = self.api.printer_objects_query({"pause_resume": None})
        return resp.get('result', {}).get('status', {}).get('pause_resume', {}).get('is_paused', False)
    
    def ready_status(self):
        resp = self.api.printer_objects_query({"toolhead": ["status"]})
        return resp.get('result', {}).get('status', {}).get('toolhead', {}).get('status', None)
    
    def poll_commands(self):
        
        resp = self.api.server_gcode_store(50)
        commands = []
        for i in resp.get('result', {}).get('gcode_store', []):
            if i['time'] <= self.last_commands_poll: continue
            commands.append(i['message'])
            self.last_commands_poll = i['time']
                
        
        return commands