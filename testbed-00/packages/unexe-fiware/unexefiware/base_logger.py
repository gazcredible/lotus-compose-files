import unexefiware.debug
import traceback
import os

class BaseLogger:
    def __init__(self):
        pass

    def exception_to_string(self,exception):
        try:
            text = str(exception)
            text += '\n'
            stack = traceback.format_tb(tb=exception.__traceback__)
            stack.reverse()
            for entry in stack:
                terms = entry.split(',')
                head, filename = os.path.split(terms[0])
                text += filename.replace('"', '') + terms[1].replace('line ', ':').replace(' ', '')
                text += terms[2].replace('\n', '')
                text += '\n'

            return text

        except Exception as e:
            return 'Failed to process exception!'


    def exception(self, cf, exception):
        try:
            text = self.exception_to_string(exception)
            self.fail(cf,text)
        except Exception as e:
            self.fail(cf, 'Failed to process exception!')

    def fail(self, cf, text):
        self.log(cf, 'FAIL:'+str(text))

    def log(self, cf, text):
        print(self.formatmsg(cf, text))

    def formatmsg(self, cf, text):
        return unexefiware.debug.formatmsg(cf, str(text))

