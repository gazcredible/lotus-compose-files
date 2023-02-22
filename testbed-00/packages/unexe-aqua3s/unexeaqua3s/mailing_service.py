import inspect
import unexeaqua3s.json

import unexeaqua3s.service_alert
import unexeaqua3s.deviceinfo
import unexeaqua3s.service
import os
import unexefiware.base_logger
from unexeaqua3s import support
import unexefiware.workertask
import unexefiware.fiwarewrapper

import unexeaqua3s.service_chart
import unexeaqua3s.service_anomaly
import datetime
import urllib

import smtplib, ssl
from email.message import EmailMessage

# reads the json file that contains a JSON array with the emails of the recipients
# you can have one or more email addresses


recipients = ['gareth_lewis@yahoo.com', 'moumtzid@iti.gr']
msg = 'Subject:email\n\n\nThanks Natasa. \nCan you make sure the gmail account is set to English as it\'s really hard to work out where the settings are in Greek ;)\n\n\nBest\nAqua3s Info'

def send_email(recipients, msg):

    if isinstance(recipients,str):
        recipients = [recipients]

    # Create a secure SSL context
    context = ssl.create_default_context()


    smtp_server = "smtp.gmail.com"
    port = 587  # For starttls
    sender_email = "aqua3s.alerts@gmail.com"
    password = "aqua3s.alerts!69"
    password = 'jkzpsnutpjzhfnja'

    #sender_email = "aqua3s.info@gmail.com"
    #password = "thn!ASD23"


    try:
        server = smtplib.SMTP(smtp_server,port)
        server.ehlo() # Can be omitted
        server.starttls(context=context) # Secure the connection
        server.ehlo() # Can be omitted
        server.login(sender_email, password)
        # TODO: Send email here
        server.sendmail(sender_email, recipients, msg.encode('utf-8'))
    except Exception as e:
        # Print any error messages to stdout
        print(e)
    finally:
        if server.sock and server.sock._closed == False:
            server.quit()


def print_text(deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2) -> str:
    text = 'Current Alert Status'
    text += '\n'

    alert_count = 0
    for device_id in deviceInfo.deviceModelList:
        device = deviceInfo.deviceModelList[device_id]

        if device.alert_isTriggered():
            alert_count +=1
            text += device.name()
            text += ' '
            text += device.get_id()
            text += '\n'
            text += device.alert_observedAt()
            text += ' '
            text += device.alertstatus_reason_prettyprint().ljust(30, ' ')

            text = text.replace('<br>', ' ')
            text += '\n'
            text += '\n'

    if alert_count == 0:
        text = 'Current Alert Status'
        text += '\n'
        text += 'All sensors are good!'
    else:
        text += '\n'
        text += 'End of Alert List'

    return text

class Mailservice:
    def __init__(self):

        self.fiware_service = ''
        self.payload = {}
        self.logger = unexefiware.base_logger.BaseLogger()

    def init(self,fiware_service:str):
        self.fiware_service = fiware_service
        #self.delete()

        #gareth - don't do this
        #if self.get() == False:
        #    self.post()

        if self.do_mailing() == False:
            return

        self.get()

    def do_mailing(self):
        if 'ALERT_MAIL' not in os.environ or os.environ['ALERT_MAIL'].lower() == 'false':
            return False

        return True

    def get(self):
        if self.do_mailing() == False:
            return False

        fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])

        result = fiware_wrapper.get_entity(self.smartmodel_id(), self.fiware_service)

        if len(result) > 0:
            try:
                raw_data = result[self.smartmodel_payload_label()]['value']
                self.payload = unexeaqua3s.json.loads(raw_data)
                return True
            except Exception as e:
                self.logger.exception(inspect.currentframe(),e)

        self.payload = {}

        return False

    def delete(self):
        if self.do_mailing() == False:
            return

        fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
        fiware_wrapper.delete_instance(self.smartmodel_id(), self.fiware_service)

        self.payload = {}

    def post(self):
        if self.do_mailing() == False:
            return

        fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
        result = fiware_wrapper.get_entity(self.smartmodel_id(), self.fiware_service)

        if len(result) != 0:
            self.delete()

        #fill-in initial (default) payload
        payload = {}
        payload['status'] = {}
        payload['mail_list'] = ['g.lewis2@exeter.ac.uk']
        payload['actually_send_mail'] = True
        payload['force_sending'] = False
        payload['process_mail'] = True

        smart_model = {
            "@context": "https://smartdatamodels.org/context.jsonld",
            "id": self.smartmodel_id(),
            "type": "AlertEmail",

            self.smartmodel_payload_label() : {
                "type": "Property",
                "value": unexeaqua3s.json.dumps(payload)
            },
        }

        fiware_wrapper.create_instance(smart_model, self.fiware_service)

    def patch(self):

        if self.do_mailing() == False:
            return

        fiware_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
        result = fiware_wrapper.get_entity(self.smartmodel_id(), self.fiware_service)

        if len(result) > 0:
            new_data = unexeaqua3s.json.loads(result[self.smartmodel_payload_label()]['value'])
            if self.payload['status'] != new_data:

                patch_data = {self.smartmodel_payload_label():
                {
                        "type": "Property",
                        "value": unexeaqua3s.json.dumps(self.payload)
                        }
                }

                fiware_wrapper.patch_entity(self.smartmodel_id(), patch_data, service=self.fiware_service)

    def get_new_status(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2) -> dict:
        status = {}

        for device_id in deviceInfo.deviceModelList:
            device = deviceInfo.deviceModelList[device_id]

            status[device_id] = device.alert_isTriggered()

        return status

    def compare_status_equal(self, status_a:dict, status_b:dict) -> bool:

        for key in status_a:
            if key not in status_b:
                return False

            if status_a[key] != status_b[key]:
                return False

        for key in status_b:
            if key not in status_a:
                return False

        return True

    def smartmodel_id(self):
        return "urn:ngsi-ld:AlertEmail:AlertEmail00"

    def smartmodel_payload_label(self):
        return 'email_data'

    def update(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2, force_email:bool=False):

        if self.do_mailing() == False:
            return

        try:
            self.get()

            if self.payload != {} and 'process_mail' in self.payload and self.payload['process_mail'] == True:
                if self.payload['status'] == {}:
                    self.payload['status'] = self.get_new_status(deviceInfo)

                    if self.payload['status'] != {}:
                        self.do_email(deviceInfo)
                else:
                    new_status = self.get_new_status(deviceInfo)

                    if self.compare_status_equal(self.payload['status'], new_status) == False or self.payload['force_sending'] == True or force_email == True:
                        self.payload['status'] = self.get_new_status(deviceInfo)
                        self.do_email(deviceInfo)
                    else:
                        self.logger.log(inspect.currentframe(),'Nothing to email')

                self.patch()

        except Exception as e:
            self.logger.exception(inspect.currentframe(),e)

    def do_email(self, deviceInfo:unexeaqua3s.deviceinfo.DeviceInfo2):
        print('Sending email')

        text = self.create_email_message(deviceInfo)

        self.send_email(self.payload['mail_list'], subject=self.fiware_service +' Alert Status', msg=text)

    def create_email_message(self, deviceInfo: unexeaqua3s.deviceinfo.DeviceInfo2) -> str:
        text = 'Current Alert Status'
        text += '\n'

        alert_count = 0
        for device_id in deviceInfo.deviceModelList:
            device = deviceInfo.deviceModelList[device_id]

            if device.alert_isTriggered():
                alert_count += 1
                text += device.name()
                text += ' '
                text += device.get_id()
                text += '\n'
                text += device.alert_observedAt()
                text += ' '
                text += device.alertstatus_reason_prettyprint().ljust(30, ' ')

                text = text.replace('<br>', ' ')
                text += '\n'
                text += '\n'

        if alert_count == 0:
            text = 'Current Alert Status'
            text += '\n'
            text += 'All sensors are good!'
        else:
            text += '\n'
            text += 'End of Alert List'

        return text

    def send_email(self, recipients, subject:str, msg:str):

        if self.payload['actually_send_mail'] == False:
            print(str(recipients))
            print(msg)
            print()

            return

        if isinstance(recipients, str):
            recipients = [recipients]

        try:
            # Create a secure SSL context
            context = ssl.create_default_context()

            smtp_server = "smtp.gmail.com"
            port = 587  # For starttls
            sender_email = "aqua3s.alerts@gmail.com"
            password = "aqua3s.alerts!69"
            password = 'jkzpsnutpjzhfnja'

            # sender_email = "aqua3s.info@gmail.com"
            # password = "thn!ASD23"

            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()  # Can be omitted
            server.starttls(context=context)  # Secure the connection
            server.ehlo()  # Can be omitted
            server.login(sender_email, password)
            # TODO: Send email here
            payload = EmailMessage()
            payload['Subject'] = subject
            payload['From'] = sender_email
            payload['To'] = recipients

            # Create a plain text message (no formatting)
            payload.set_content(msg)


            msg_to_send = msg.encode('utf8')
            #server.sendmail(sender_email, recipients, msg_to_send)
            server.send_message(payload)
            server.quit()

        except Exception as e:
            # Print any error messages to stdout
            print(e)

def mailservice_options(mailservice:Mailservice):
    quitApp = False
    while quitApp is False:

        mailservice.get()

        print('Mailservice Options')

        if mailservice.payload != {}:
            print('1..Add mail:' + str(mailservice.payload['mail_list']))
            print('2..Remove mail:' + str(mailservice.payload['mail_list']))

            if 'process_mail' in mailservice.payload:
                print('3..Toggle Process Mail:' + str(mailservice.payload['process_mail']))

            if 'force_sending' in mailservice.payload:
                print('4..Toggle Force sending Mail:' + str(mailservice.payload['force_sending']))

        print('5..Delete FIWARE data')
        print('6..Create FIWARE data')

        print('00..Reset')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == 'x':
            quitApp = True

        if key == '1':
            mail_address = input('enter email >')

            print('Add: ' + mail_address +' y/n' )

            key = input('>')

            if key == 'y':
                mailservice.payload['mail_list'].append(mail_address)
                mailservice.patch()

        if key == '2':
            index  = 1
            for entry in mailservice.payload['mail_list']:
                print(str(index) +' ' + entry)
                index+=1

            key = input('>')

            try:
                key_index = int(key)

                if key_index >= 1 and key_index <= index:
                    mailservice.payload['mail_list'].pop(key_index-1)
                    mailservice.patch()
            except Exception as e:
                pass

            key = ''


        if key == '3':
            if 'process_mail' in mailservice.payload:
                mailservice.payload['process_mail'] = not mailservice.payload['process_mail']

                mailservice.patch()

        if key == '4':
            if 'force_sending' in mailservice.payload:
                mailservice.payload['force_sending'] = not mailservice.payload['force_sending']

                mailservice.patch()

        if key == '5':
            mailservice.delete()

        if key == '6':
            mailservice.post()

        if key == '00':
            mailservice.delete()
            mailservice.post()


def testbed(fiware_service):

    quitApp = False

    mailservice = Mailservice()
    mailservice.init(fiware_service)

    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(fiware_service=fiware_service)
    deviceInfo.logger = unexefiware.base_logger.BaseLogger()
    deviceInfo.run()

    if mailservice.do_mailing() == False:
        while quitApp is False:
            print('\nmailing Testbed')
            print('Mailing service disabled')
            print('X..Back')
            print('\n')

            key = input('>')

            if key == 'x':
                quitApp = True


    else:
        while quitApp is False:

            deviceInfo.run()

            print('\nmailing Testbed')
            for device_id in deviceInfo.deviceModelList:
                device = deviceInfo.deviceModelList[device_id]

                text = '\033[0;30m'

                text += device.get_id().ljust(45, ' ')
                text +=  ' ' + str(device._observedAt_prettyprint())

                text += ' '
                text += 'Alert:'
                if device.alert_isTriggered():
                    text += '\033[0;31m'
                else:
                    text += '\033[0;32m'

                text += device.alertstatus_reason_prettyprint().ljust(55, ' ')

                text += '\033[0;30m'
                text += ' Anomaly:'

                if device.anomaly_isTriggered():
                    text += '\033[0;31m'
                else:
                    text += '\033[0;32m'

                text += device.anomalystatus_reason_prettyprint()
                text += '\033[0;30m'

                print(text)
            print()

            print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])

            print('\n')
            print('1..Run Alert Email to:' + fiware_service)
            print('1a..Force Alert Email to:' + fiware_service)
            print('2..Update deviceInfo')
            print('3..Preview email')
            print('4..Flash email')
            print('5..run mail service')
            print('8..post')
            print('9..patch')
            print('0..configure')

            print('X..Back')
            print('\n')

            key = input('>')

            if key == 'x':
                quitApp = True


            if key == '1':
                mailservice.update(deviceInfo,force_email=False)

            if key == '1a':
                mailservice.update(deviceInfo,force_email=True)


            if key =='2':
                deviceInfo.run()

            if key =='3':
                print(print_text(deviceInfo))

            if key == '4':
                try:
                    for device_id in deviceInfo.deviceModelList:
                        device = deviceInfo.deviceModelList[device_id]

                        print( device.get_id().ljust(45, ' ') + ' ' +str(device.property_observedAt()) + ' ' + str(device.deviceState()).ljust(10, ' ') + ' ' + str(device.alert_isTriggered()).ljust(10, ' ') + str(device.alertstatus_reason_prettyprint()))


                except Exception as e:
                    logger = unexefiware.base_logger.BaseLogger()
                    logger.exception(inspect.currentframe(), e)

            if key == '5':
                mailservice.update(deviceInfo)

            if key == '8':
                mailservice.post()

            if key == '9':
                mailservice.patch()

            if key == '0':
                mailservice_options(mailservice)

if __name__ == '__main__':
    testbed()


