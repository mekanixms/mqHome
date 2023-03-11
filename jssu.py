http_return_headers = {
    "CORS": """HTTP/1.1 {httpStatus}
Access-Control-Max-Age: 86400
Access-Control-Allow-Origin: {origin}
Access-Control-Allow-Methods: *
Access-Control-Allow-Headers: *
Access-Control-Allow-Credentials: true
Cache-Control: no-store, no-cache, must-revalidate
Pragma: no-cache
Connection: Keep-Alive
Content-Length: {contentLength}
Content-Type: {contentType}

{CONTENT}
""",

    "DEFAULT": """HTTP/1.1 {httpStatus}
Connection: Keep-Alive
Content-Length: {contentLength}
Content-Type: {contentType}

{CONTENT}
""",

    "OPTIONS": """HTTP/1.1 {httpStatus}
Server: mpqh
Connection: Keep-Alive
Access-Control-Allow-Origin: {origin}
Access-Control-Allow-Methods: POST, GET, OPTIONS
Access-Control-Allow-Headers: X-Requested-With, Origin, Content-Type
"""
}


def responseTemplate(method, contentType):

    if method == "OPTIONS":
        return http_return_headers["OPTIONS"]
    else:
        if contentType in ["application/json", "application/javascript"]:
            return http_return_headers["CORS"]
        else:
            return http_return_headers["DEFAULT"]


def processHeader(rcvd):
    ret = {}
    if len(rcvd) > 0:
        for i in range(len(rcvd)):
            l = rcvd[i]
            if l != b'\r\n':
                stl = l.decode("utf-8").strip("\r\n")
                if i == 0:
                    stlsp = stl.split(" ")
                    if len(stlsp) > 0:
                        ret["METHOD"] = stlsp[0]
                        ret["FULL_PATH"] = stlsp[1]
                        ret["HTTP_VERSION"] = stlsp[2]
                else:
                    stlspbc = stl.split(":", 1)
                    ret[stlspbc[0]] = stlspbc[1].strip()

    return ret

# Credits to https://github.com/SpotlightKid/mrequests/blob/master/urlunquote.py
def unquote(string):
    """unquote('abc%20def') -> b'abc def'.

    Note: if the input is a str instance it is encoded as UTF-8.
    This is only an issue if it contains unescaped non-ASCII characters,
    which URIs should not.
    """
    if not string:
        return b''

    if isinstance(string, str):
        string = string.encode('utf-8')

    bits = string.split(b'%')
    if len(bits) == 1:
        return string

    res = bytearray(bits[0])
    append = res.append
    extend = res.extend

    for item in bits[1:]:
        try:
            append(int(item[:2], 16))
            extend(item[2:])
        except KeyError:
            append(b'%')
            extend(item)

    return bytes(res).decode("utf-8")
