import local_environment_settings
import unexeaqua3s.kibanablelog

servicelog = unexeaqua3s.kibanablelog.KibanableLog('3D_Visualisation')

payload_sequence_number = 0
def dump_payload_to_disk(command, payload):
    global payload_sequence_number

    #blueprints.debug.servicelog.log(inspect.currentframe(), command+'-payload:' + str(len(payload)))
    return #no payload info
    f = open('tests/payloads/'+str(payload_sequence_number)+'_'+command, 'w')
    f.write(payload)
    f.close()

    payload_sequence_number = payload_sequence_number + 1

class DebugControl:
    def __init__(self):
        self.disableKeyrock = False
        self.use_simulated_context_brokers = True
        self.allowUNEXEPilots = True
        self.print_log_to_console = False

    def launch(self):
        pass

    def is_sim(self, fiware_service):
        if self.use_simulated_context_brokers == True:
            return True

        if fiware_service == 'GT':
            return True

        if fiware_service == 'WIS':
            return True

        return False

debugControl = None

def init():
    global  debugControl
    debugControl = DebugControl()
    debugControl.launch()