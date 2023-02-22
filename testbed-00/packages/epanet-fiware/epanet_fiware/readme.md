# Notes on usage of `EPAnetModel`

## 1. Arguments

* `network_name` (required): Name for the network being loaded (if retrieving a network using FIWARE, this must match the name used when the network was stored)
* `filename` (optional): EPANET .inp file. If this is provided, then this will be used for any network analysis and simulations instead of FIWARE.
* `output_path` (optional): Location for any EPANET output files to be saved. Default `'.'`.
* `inp_coordinate_system` (optional): Coordinate system used for node coordinates and vertices in the .inp file, of type `ngsi_ld_writer.CoordinateSystem`. Used to convert coordinates to WGS84 when storing network using FIWARE (other coordinate referencing systems will cause an error). WGS84 system is assumed if none specified.
* `gateway_server` (optional): Used to retrieve network using FIWARE if no .inp file is provided.
* `client_id`, `client_secret` and `auth_url` (optional): Provide if required for authentication when posting/retrieving the network model.

## 2. Converting an EPANET .inp file to JSON-LD (according to Water Network Management data model) and storing using context broker

To generate JSON-LD (in accordance with the Water Network Management data model) from an EPANET .inp file and store using the context broker, run the following with `network_name`, `filename`, `gateway_server`, `inp_coordinate_system` (optional), `client_id` (optional), `client_secret` (optional) and `auth_url` (optional) updated appropriately.
```
model = EPAnetModel(network_name='network_name',
                    filename='epanet_inp_file',
                    inp_coordinate_system=CoordinateSystem.osgb)
model.post_network_model(gateway_server='http://xx.xx.xx.xx:xxxx')
```

## 3. Retrieving a network from the context broker and using to generate an EPANET project

To retrieve data for all components of network `network_name` from the the context broker and generate an EPANET project that can be used to run simulations:
```
model = EPAnetModel(network_name='network_name',
                    gateway_server='http://xx.xx.xx.xx:xxxx')
```

Network properties can then be retrieved from the generated project (see 4), modifications can be applied to the network (see 5), and simulations can be run (see 6).

## 4. Retrieving network properties

`get_*` functions are available to retrieve network properties. These can be used to retrieve both static properties (as given in an .inp file) and dynamic data for links and nodes (simulation outputs).

* `get_node_ids(self, node_type: enu.NodeTypes)`: Returns a list of the IDs of all nodes of a specified type.
* `get_link_ids(self, link_type: enu.LinkTypes)`: Returns a list of the IDs of all links of a specified type.
* `get_link_property(self, link_id: str, prop: Union[enu.PipeProperties, enu.PumpProperties, enu.ValveProperties])`: Returns the value of a specified property of a specified link.
* `get_node_property(self, node_id: str, prop: Union[enu.JunctionProperties, enu.ReservoirProperties, enu.TankProperties])`: Returns the value of a specified property of a specified link.

Time parameters used in the simulation can also be retrieved:

* `get_time_param(self, prop: enu.TimeParams)`: Returns the value of a specified time parameter


## 5. Setting network properties

`set_*` functions that can be used to manipulate node and link properties are to be added. Time parameters for the simulation can also be set using `set_time_param(...)`

## 6. Running a simulation

Load an EPANET model, either from an .inp file (as in 2, above) or the context broker (as in 3, above). A full simulation (all time steps at once) is then run with:
```
model.simulate_full()
```

A step-by-step simulation is run with:
```
model.simulate_init()
while model.simulation_status in [
        SimStatus.initialised, SimStatus.started]:
    model.simulate_step()
```

This automatically closes/ends the hydraulic and quality simultaion when the last time step is reached. To reset the simulation and start again from time zero before reaching the end, do:
```
model.simulate_close()
model.simulate_init()
```

## 6. Extracting simulation results from the binary output file

Following completion of a full simulation with `model.simulate_full()`, a binary output file is created that contains hydraulic and quality simulation results.


An `EpanetOutFile` is automatically created from the binary output file and stored as `model.out_file_data`; the `EpanetOutFile` functions from `epanet_outfile_handler.py` for reading the binary file can be accessed from here.

Alternatively (and more simply), the supply, head, pressure or quality of a node at any reporting period can be obtained using:
```
model.get_node_result(period, prop, node_id, node_index)
```
Where:
* `period` is the reporting period (range from 0 to the total number of periods)
* `prop` is the required property (of type `NodeResultLabels`)
* Only the `node_id` OR the `node_index` needs to be specified


Similarly the flow, headloss, quality, status, setting, reaction rate or friction factor of a link at any reporting period can be obtained using:
```
model.get_link_result(period, prop, link_id, link_index)
```
Where:
* `period` is the reporting period (range from 0 to the total number of periods)
* `prop` is the required property (of type `LinkResultLabels`)
* Only the `link_id` OR the `linkindex` needs to be specified



