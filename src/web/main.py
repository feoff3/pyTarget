import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from comm.stdlib import *


# help path
#HELP_PAGE_PATH = os.path.dirname(__file__) + os.sep + 'help.htm'
#HELP_PAGE_PATH = 'help.htm'

# command line html code
CMD_LINE = '''
<fieldset name="Group1">
    <legend>Command </legend>
    <form method="post">
        <input name="Command" type="text" style="width: 85%" /> <input name="Submit1" type="submit" value="Submit" /><input name="Reset1" type="reset" value="Claer" /><input type="hidden" name="SessionID" value="PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-V9DX9-V9DX9-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-V9DX9-V9DX9-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-V9DX9-V9DX9-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-V9DX9-V9DX9-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-PYHYP-WXB3B-B2CCM-V9DX9-VDY8T-V9DX9-V9DX9" />
    </form>
    command 'help' for help information
</fieldset> <br>'''

def TB(isBegin = False):
    if isBegin:
        return '''<table style="border-style: solid; border-width: 1px;" cellspacing="1">'''
    else:
        return '''</table>'''

def TR(arg):
    return '<tr>' + arg + '</tr>'

def TD(arg = '&nbsp;', isTitle = False):
    if isTitle:
        txt = '''<td style="border: 1px; text-align: center; color: #FFFFFF;background-color: #666666;">'''        
    else:
        txt = '''<td style="border: 1px solid #000000;">'''
    txt += arg + '</td>' 
    return txt

def RequestPage(server):
        server.Send_HttpHeader()
        server.Send_Data(CMD_LINE)

def ResponsePage(server):
    cmds = server.cmds

    try:
        if cmds[0] == 'version':
            import comm.version as version
            buf = 'Version =%s Data=%s' % (version.MY_VERSION, version.MY_DATE)
            server.Send_HttpHeader()
            server.Send_Data(buf)

        elif cmds[0] == 'help' or cmds[0] == 'HELP' or cmds[0] == '?':
            path = 'help.htm'
            try:
                if not os.path.exists(path):
                    path = 'web' + os.sep + path
                fd = open(path)
                buf = fd.read()
                fd.close()           
            except IOError:
                buf = 'missing file ' + path           
                server.Send_ErrData(buf)
                return
            server.Send_HttpHeader()
            server.Send_Data(CMD_LINE + buf)
            return

        elif cmds[0] == 'target':
            from web.target import Target_Page
            Target_Page(server)
        elif cmds[0] == 'host':
            from web.host import Host_Page
            Host_Page(server)
        elif cmds[0] == 'lun':
            from web.lun import Lun_Page
            Lun_Page(server)
        elif cmds[0] == 'session':
            from web.session import Session_Page
            Session_Page(server)
        elif cmds[0] == 'connect':
            from web.connect import Connect_Page
            Connect_Page(server)
        elif cmds[0] == 'simulator':
            from web.simulator import Simulator_Page
            Simulator_Page(server)
        elif cmds[0] == 'debug':
            import comm.debug as debug
            if cmds[1] == 'level':
                debug.CURRENT_DEBUG_LEVEL = atoi(cmds[2])
                buf = 'Modify debug level to %s' % cmds[2]
                server.Send_SuccData(buf, '/')
            elif cmds[1] == 'ls':
                buf = CMD_LINE
                buf += 'Current debug level = %d' % debug.CURRENT_DEBUG_LEVEL
                server.Send_HttpHeader()
                server.Send_Data(buf)
                return
        else:
            server.Send_ErrData('unknown commands or parameters', '/')
    except:
        server.Send_ErrData('unknown commands or parameters', '/')


class WebServer(BaseHTTPRequestHandler):

    def Send_HttpHeader(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def Send_Data(self, data):
        self.wfile.write(data)

    def Send_ErrData(self, detail, link):
        self.Send_HttpHeader()
        self.Send_Data('''<font color="#FF0000">Operation failed: %s. </font>&nbsp; <a href = "%s"> back </a>''' % (detail, link))

    def Send_SuccData(self, detail, link):
        self.Send_HttpHeader()
        self.Send_Data('''<font color="#008000">Operation success: %s. </font>&nbsp; <a href = "%s"> back </a>''' % (detail, link))
        
    def do_GET(self):           
        RequestPage(self)

    def do_POST(self):
        self.__decode()
        ResponsePage(self)

    def __decode(self):
        # decode keys
        self.keys = {}
        txt = str(self.rfile.read(500))
        while len(txt): 
            sub = txt[:txt.find('&')]
            key = sub[:sub.find('=')]
            val = sub[len(key) + 1:]
            txt = txt[len(sub) + 1:]
            self.keys[key] = val

        # decode command
        self.cmds = []
        buf = ''    
        for i in self.keys['Command']:
            if i == '+':
                if buf:
                    self.cmds.append(buf)
                    buf = ''
            elif i:
                buf += i
        if buf:
            self.cmds.append(buf)

def WebService(isStop = None):
    try:
        server = HTTPServer(('', 80), WebServer)
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()

if __name__ == '__main__':
    WebService()

