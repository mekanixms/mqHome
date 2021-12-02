import socket
import ujson
import gc
from jssu import responseTemplate, processHeader
from machine import idle


def mem_manage():
    gc.collect()
    gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())


def router(func):
    def wrapper(*args, **kwargs):
        # args sunt argumentele cu care se apeleaza serve
        # args[0] este self catre instanta jss
        # args[1] este path
        # kwargs este empty in acest caz
        # print('router BEFORE:')

        return func(*args, **kwargs)
        # print('AFTER SERV {func}')
    return wrapper


class jss:
    version = 0.10
    version_minor = 1
    sendit = {}
    generatedContent = None
    port = 8080
    addr = None
    s = socket.socket()
    requestHeader = []
    payload = ""
    postMultipart = None
    postMultipartBoundary = None
    postUrlencoded = None
    route = {}
    routeHandler = None
    REQUEST = {}
    RESPONSE = {}
    responseContentType = "text/plain"

    def __init__(self, verbose=False, port=8080):
        self.verbose = verbose
        self.addr = socket.getaddrinfo('0.0.0.0', self.port)[0][-1]
        self.openSocket()

    def openSocket(self):
        self.s = socket.socket()
        self.s.bind(self.addr)
        self.s.listen(100)
        self.s.settimeout(None)
        print('listening on', self.addr)

    def readRequest(self, clsock):
        self.requestHeader = []
        self.payload = ""
        self.postMultipart = None
        self.postMultipartBoundary = None
        self.postUrlencoded = None
        multipartPrefix = b"content-type: multipart/form-data;"
        urlencodedPrefix = b"Content-Type: application/x-www-form-urlencoded".lower()
        contentLength = 0

        while True:
            line = clsock.readline()
            if b"content-length: " in line.lower():
                contentLength = int(line.lower().lstrip(
                    b'content-length: ').decode("utf-16"))

            # Content-Type: multipart/form-data; boundary=...
            if multipartPrefix in line.lower():
                self.postMultipart = True
                bs = line[len(multipartPrefix):].strip()
                self.postMultipartBoundary = bs[len(b'boundary='):]

            # Content-Type: application/x-www-form-urlencoded
            if urlencodedPrefix in line.lower():
                self.postUrlencoded = True

            if not line or line == b'\r\n':
                break
            else:
                self.requestHeader.append(line)

        if contentLength:
            self.payload = clsock.read(contentLength)
        else:
            self.payload = b""

    @router
    def serve(self, path):
        print("jss: " + str(path))
        if self.routeHandler.__class__.__name__ == "function":
            route = self.routeHandler(path)
        else:
            route = path

        if route in self.route:
            pathHandler = self.route[route]
            # print("FOUND\t" + str(route))
        else:
            pathHandler = self.route["/NOTFOUND"]

        return pathHandler(self.REQUEST)

    def fetchContent(self):
        # set valoare default generated content pt self.responseContentType text/plain
        if len(self.sendit) > 0:
            generatedContent = self.sendit if type(
                self.sendit) is str else ujson.dumps(self.sendit)
        else:
            generatedContent = ""

        if self.responseContentType == 'application/javascript':
            if "callback" in self.REQUEST["GET"]:
                generatedContent = self.REQUEST["GET"]["callback"] + \
                    "("+ujson.dumps(self.sendit)+")"
            else:
                self.responseContentType = "application/json"
                generatedContent = "(function(){return " + \
                    ujson.dumps(self.sendit)+"})()"

        if self.responseContentType == 'application/json':
            generatedContent = ujson.dumps(self.sendit)

        return generatedContent

    def resume(self):
        pass

    def pause(self):
        pass

    def stop(self):
        pass

    def parseRequest(self):
        req = b''.join(self.requestHeader)

        http_query_string, http_method, http_query,  POST = {}, {}, {}, {}
        cmd, headers = req.decode("utf-8").split('\r\n', 1)
        parts = cmd.split(' ')
        http_method, path = parts[0], parts[1]
        http_get_string = ''

        r = path.find('?')
        if r > 0:
            req.decode("utf-8").split('\r\n', 1)
            http_get_string = path[r+1:]
            path = path[:r]

        qargs = http_get_string.split('&')
        for arg in qargs:
            t = arg.split('=')
            if len(t) > 1:
                k, v = arg.split('=')
                http_query[k] = v

        if http_method == "POST":
            if self.postUrlencoded:
                qargs = self.payload.decode("utf-8").strip().split('&')
                for arg in qargs:
                    t = arg.split('=')
                    if len(t) > 1:
                        k, v = arg.split('=')
                        POST[k] = v
            else:
                if self.postMultipart:
                    import ure
                    postClean = self.payload.replace(
                        b"--"+self.postMultipartBoundary+b"--", b"")
                    postClean = postClean.lstrip(
                        b"\n--"+self.postMultipartBoundary)

                    for varStr in postClean.split(b"\n--"+self.postMultipartBoundary):
                        vmatch = '^\s*Content-Disposition: form-data; name=\"(.*)\"\s*(.*)$'

                        vgr = ure.match(
                            vmatch, varStr.decode("utf-16").strip())

                        try:
                            keyName = vgr.group(1)
                        except:
                            print("Corrupted POST data")
                        else:
                            if keyName:
                                POST[vgr.group(1)] = vgr.group(
                                    2) if vgr.group(2).strip() else ""

        return {
            "PATH": path,
            "QUERY_STRING": http_query_string,
            "METHOD": http_method,
            "QUERY": http_query,
            "GET": http_query if http_method == "GET" else {},
            "POST": POST,
            "HEADER": processHeader(self.requestHeader)
        }

    def processConnection(self, cl):
        # print('client connected from', self.addr)

        self.readRequest(cl)

        try:
            self.REQUEST = self.parseRequest()
        except ValueError:
            print("ValueError in parseRequest: need more than 1 values to unpack")

        self.response = ""
        if "HEADER" in self.REQUEST:
            METHOD = self.REQUEST["HEADER"]["METHOD"]
            Accept = self.REQUEST["HEADER"]["Accept"] if "Accept" in self.REQUEST["HEADER"].keys(
            ) else ""
            self.response = responseTemplate(METHOD, Accept)

            if self.REQUEST["HEADER"]["METHOD"] == "OPTIONS":
                Allowed = True
                if Allowed:
                    http_status = "204 No Content"
                else:
                    http_status = "403 Forbidden"
            else:
                self.responseContentType, http_status, self.sendit = self.serve(
                    self.REQUEST["PATH"])
                self.generatedContent = self.fetchContent()

            self.response = self.response.replace("{origin}", "*")
            self.response = self.response.replace("{httpStatus}", http_status)

            if self.generatedContent != None:
                self.response = self.response.replace(
                    "{contentLength}", str(len(self.generatedContent)))
                self.response = self.response.replace(
                    "{contentType}", self.responseContentType)
                self.response = self.response.replace(
                    "{CONTENT}", self.generatedContent)
        else:
            print("NO HEADER RECEIVED")

        try:
            cl.send(self.response)
            if self.verbose:
                print("_____SENT RESPONSE____:\n")
                print(self.response)
                print("_____END SENT RESPONSE____")
        except OSError as err:
            print(err)

        cl.close()

    def start(self):
        while True:
            try:
                cl, self.addr = self.s.accept()
            except OSError as err:
                if err.args[0] == 11:
                    print("EAGAIN")
                    print("Reopening Socket")
                    self.openSocket()
                else:
                    print("Error on accept:")
                    print(err)
                    cl.close()
                    break
            except KeyboardInterrupt:
                print("Stopped by keyboard")
                cl.close()
                break

            mem_manage()
            self.processConnection(cl)
