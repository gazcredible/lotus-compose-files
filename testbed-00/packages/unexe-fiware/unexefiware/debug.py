import inspect


def formatmsg(cf, msg):
    try:
        frameinfo = inspect.getframeinfo(cf)
        filename = frameinfo.filename.split('/')[-1]

        return (frameinfo.function + '() ' + filename + '-' + str(frameinfo.lineno) + ': ' + msg)
    except Exception as e:
        print(str(e))
