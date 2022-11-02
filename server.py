#!/usr/bin/python3
# coding=UTF-8

import http.server
from urllib.parse import parse_qs
from manager import *


def run_server() -> None:
    """ Runs the HTTP server. """
    server_class = HeatServer
    httpd = server_class(("", 8888), HeatHandler)
    print(get_time_string(), "HeatServer starts - %s:%s" % ("", 8888))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(get_time_string(), "HeatServer stops")


class HeatServer(http.server.HTTPServer):

    def __init__(self, server_address_port, request_handler) -> None:
        super().__init__(server_address_port, request_handler)


class HeatHandler(http.server.BaseHTTPRequestHandler):

    usage = """
    do=start                            - starts the manager
    do=stop                             - stops the manager
    do= info                            - short information about the heaters
    do=status                           - full status information about the heaters und solar system
    do=verbose                          - turn on extensive logging on the server
    do=silent                           - turn off extensive logging on the server
    do=help                             - this help text
    do=enable&heater=name               - enable a heater
    do=disable&heater=name              - disable a heater
    do=switch&heater=name&heater=name   - exchanges two heaters in the HeatSteps definition
    do=clear                            - deletes the exchange of heaters
    """

    def do_GET(self):
        start = self.requestline.find("?")
        kvp = {}
        if start > 0:
            end = self.requestline.find(" ", start)
            kvp = parse_qs(self.requestline[start + 1: end])
        response = "this is a system error"
        if 'do' in kvp:
            arg = kvp['do'][0]
            if arg == 'help':
                response = self.usage
            elif arg == 'info':
                response = heat("info")
            elif arg == 'status':
                response = status()
            elif arg == "silent":
                response = verbose_manager(False)
            elif arg == 'start':
                response = start_manager()
            elif arg == 'stop':
                response = stop_manager()
            elif arg == "verbose":
                response = verbose_manager(True)
            elif arg == "enable":
                if 'heater' in kvp:
                    for heater_name in kvp['heater']:
                        try:
                            heat(heater_name, "enable")
                            response = "Heater %r is enabled." % kvp['heater']
                        except ValueError as inst:
                            response = ' '.join(inst.args)
                else:
                    response = "Parameter &heater=... is missing."
            elif arg == "disable":
                if 'heater' in kvp:
                    for heater_name in kvp['heater']:
                        try:
                            heat(heater_name, "disable")
                            response = "Heater %r is disabled." % kvp['heater']
                        except ValueError as inst:
                            response = ' '.join(inst.args)
                else:
                    response = "Parameter &heater=... is missing."
            elif arg == "switch":
                if 'heater' in kvp:
                    if len(kvp['heater']) != 2:
                        response = "There have to be two parameters &heater=..."
                    else:
                        try:
                            heater_name1 = kvp['heater'][0]
                            heater_name2 = kvp['heater'][1]
                            response = heatSteps.switch(heater_name1, heater_name2)
                            manager.inform_about_new_step_definition()
                        except ValueError as inst:
                            response = ' '.join(inst.args)
                else:
                    response = "Parameter &heater=... is missing."
            elif arg == "clear":
                heatSteps.clear_switch()
                manager.inform_about_new_step_definition()
                response = "Switching of heaters is withdrawn."
            else:
                response = "You get help with '?do=help'"
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(response.encode("utf8"))


if __name__ == '__main__':
    """ Starts the HeatManager and runs the HTTP server """
    start_manager(verbose=True)  # set False by default
    run_server()
