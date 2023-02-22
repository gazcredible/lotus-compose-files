import datetime
import unexefiware.base_logger

import unexe_epanet.epanet_fiware
import unexeaqua3s.workhorse_backend

import unexeaqua3s.deviceinfo
import unexeaqua3s.service_chart
import unexefiware.time

class Aqua3S_Fiware(unexe_epanet.epanet_fiware.epanet_fiware):
    def __init__(self, logger:unexefiware.base_logger.BaseLogger=None):
        super().__init__()

        self.workhorse = unexeaqua3s.workhorse_backend.WorkhorseBackend()
        self.workhorse.init(logger=logger, debug=True)

    def on_patch_entity(self, fiware_service:str, entity_id:str):
        pass

    def reset(self,sensor_list:list=None, start_datetime:datetime.datetime=None):
        super().reset(sensor_list,start_datetime)
        self.workhorse.add_command(self.fiware_service, unexeaqua3s.workhorse_backend.command_pilot_update)

        deviceInfo = unexeaqua3s.deviceinfo.DeviceInfo2(self.fiware_service)
        deviceInfo.run()

        chartingService = unexeaqua3s.service_chart.ChartService()
        chartingService.build_from_deviceInfo(deviceInfo, self.elapsed_datetime())

    def simulate(self, steps:int):
        for i in range(0, steps):

            self.step()
            print(str(self.elapsed_datetime()))
            self.workhorse.add_command(self.fiware_service, unexeaqua3s.workhorse_backend.command_pilot_update)

        #pass in time as current time
        self.workhorse.add_command(self.fiware_service, unexeaqua3s.workhorse_backend.command_rebuild_charts,{'datetime': unexefiware.time.datetime_to_fiware(self.elapsed_datetime())})
