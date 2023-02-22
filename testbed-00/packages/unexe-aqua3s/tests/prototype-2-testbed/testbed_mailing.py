import unexeaqua3s.service_alert
import unexeaqua3s.deviceinfo
import unexeaqua3s.service
import os
import unexefiware.base_logger
from unexeaqua3s import support
import unexefiware.workertask

import unexeaqua3s.service_chart
import unexeaqua3s.service_anomaly


import smtplib, ssl

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

    sender_email = "aqua3s.info@gmail.com"
    password = "thn!ASD23"


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
        server.quit()




def testbed(fiware_service):
    quitApp = False

    device_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['DEVICE_BROKER'], historic_url=os.environ['DEVICE_HISTORIC_BROKER'])
    alert_wrapper = unexefiware.fiwarewrapper.fiwareWrapper(url=os.environ['ALERT_BROKER'], historic_url=os.environ['ALERT_HISTORIC_BROKER'])
    deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo(fiware_service, device_wrapper=device_wrapper, other_wrapper=alert_wrapper)
    deviceInfo.run()

    while quitApp is False:

        deviceInfo.run()

        print('\nmailing Testbed')
        support.print_devices(deviceInfo)
        print()

        print('DEVICE_BROKER: ' + os.environ['DEVICE_BROKER'])
        print('ALERT_BROKER:  ' + os.environ['ALERT_BROKER'])

        print('\n')
        print('1..Send Alert Email to:' + fiware_service)
        print('2..Update deviceInfo')

        print('X..Back')
        print('\n')

        key = input('>')

        if key == '1':
            key_list = list(deviceInfo.deviceInfoList.keys())
            key_list = sorted(key_list)

            text = 'Current Alert Status'
            text += '\n'

            alert_count = 0
            for device_id in key_list:
                if deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.alertStatus_label, 'triggered') == 'True':
                    alert_count +=1

            if alert_count > 0:
                for device_id in key_list:
                    if deviceInfo._get_value_entry(device_id, unexeaqua3s.deviceinfo.alertStatus_label, 'triggered') == 'True':
                        text += deviceInfo.device_name(device_id)
                        text += '\n'
                        text += deviceInfo.alertstatus_observedAt(device_id)
                        text += ' '
                        text += str(deviceInfo.alertstatus_reason_prettyprint(device_id)).ljust(30, ' ')

                        text = text.replace('<br>', ' ')
                        text += '\n'
                        text += '\n'
                text += '\n'
                text += 'End of Alert List'
            else:
                text += 'All sensors are good!'

            print(text)

            if fiware_service == 'WBL':
                send_email(['solomos@wbl.com.cy','g.lewis2@exeter.ac.uk'], msg= 'Subject:WBL Alert Status\n' + text)

            if fiware_service == 'SOF':
                send_email(['maleksova@sofiyskavoda.bg', 'g.lewis2@exeter.ac.uk'], msg='Subject:SOF Alert Status\n' + text)

        if key =='2':
            deviceInfo.run()

        if key == 'x':
            quitApp = True

if __name__ == '__main__':
    testbed()


