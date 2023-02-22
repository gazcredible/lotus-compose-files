from flask import request
from flask_cors import CORS, cross_origin
from flask import Blueprint, render_template, abort, send_file

import inspect
import unexeaqua3s.json
import io

import blueprints.debug
import blueprints.orion_device
import blueprints.keyrock_blueprint
import blueprints.resourcemanager
import blueprints.analytics_blueprint

import epanet_fiware.epanet_outfile_handler
import unexefiware.units
import unexeaqua3s.service_chart

blueprint = Blueprint('mapview_blueprint', __name__, template_folder='templates')

import unexeaqua3s.geojson2aqua3s
chart_colourlegends = {}

chart_colourlegends['hdescript'] = [
    ['h>=2','Water depth greater than 200 cm',unexeaqua3s.geojson2aqua3s.rgb_to_hex(0, 77, 182)],
    ['1.5<=h<2','Water depth 150 – 200 cm',unexeaqua3s.geojson2aqua3s.rgb_to_hex(0, 92, 230)],
    ['1<=h<1.5','Water depth 100 – 150 cm',unexeaqua3s.geojson2aqua3s.rgb_to_hex(0, 122, 255)],
    ['0.5<=h<1','Water depth 50 – 100 cm',unexeaqua3s.geojson2aqua3s.rgb_to_hex(115, 178, 255)],
    ['h<0.5','Water depth 0 – 50 cm',unexeaqua3s.geojson2aqua3s.rgb_to_hex(190, 210, 255)],
]

chart_colourlegends['PDESCRIPT'] = [
    ['F', 'Fluvial Area – Area Fluviale',unexeaqua3s.geojson2aqua3s.rgb_to_hex(190, 232, 255)],
    ['P1', 'Moderate hazard – pericolosità idraulica moderata (P1)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(170, 255, 0)],
    ['P2', 'Medium hazard – pericolosità idraulica media (P2)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(255, 255, 0)],
    ['P3A', 'High hazard – pericolosità idraulica elevata (P3A)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(255, 170, 0)],
    ['P3B', 'High hazard – pericolosità idraulica elevata (P3B)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(255, 82, 0)],
    ['AA', 'Attention Area – Area di attenzione idraulica',unexeaqua3s.geojson2aqua3s.rgb_to_hex(130, 130, 130)],
]

chart_colourlegends['RISCHIO'] = [
    ['F', 'Fluvial Area – Area Fluviale',unexeaqua3s.geojson2aqua3s.rgb_to_hex(190, 232, 255)],
    ['R1', 'Moderate risk – rischio idraulico moderata (P1)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(170, 255, 0)],
    ['R2', 'Medium Risk– rischio idraulico medio (P2)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(255, 255, 0)],
    ['R3', 'High risk – Rischio idraulico Elevato (R3)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(255, 170, 0)],
    ['R4', 'Very high risk – Rischio idraulico Molto Elevato (R4)',unexeaqua3s.geojson2aqua3s.rgb_to_hex(255, 82, 0)],
]


def get_waterlookup_table(layer):
    if 'water_depth' in layer.lower():
        return chart_colourlegends['hdescript']

    if 'hazard' in layer.lower():
        return chart_colourlegends['PDESCRIPT']

    if 'Risk_FRMPII_FVG_REGION'.lower() in layer.lower():
        return chart_colourlegends['RISCHIO']

    return None



@blueprint.route('/map')
def map_page():
    access_token = request.args.get('access_token')

    if blueprints.keyrock_blueprint.ok(access_token) and blueprints.keyrock_blueprint.get_is_mapview_available(access_token):

        if blueprints.globals.is_service_available():
            return render_template("mapview.html", access_token=access_token)
        else:
            return render_template("data_processing.html", access_token=access_token)

    return render_template("invalid.html")

#--------------------------------------------------------------------------------------------------------------------------------------------------
@blueprint.route('/get_pilot_data', methods=['GET'])
@cross_origin()
def get_pilot_data():

    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False or blueprints.keyrock_blueprint.get_is_mapview_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid',403

        loc = blueprints.keyrock_blueprint.get_location(access_token)

        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        data = {}
        data['location'] = blueprints.orion_device.get_puc_location(deviceInfo)

        data['water_network'] = {}
        data['has_water_network'] = blueprints.keyrock_blueprint.get_is_epanet_available(access_token)
        data['has_user_layers'] = False
        data['analytics_time_labels'] = unexeaqua3s.service_chart.chart_modes

        data['has_epanet_anomalies'] = False


        if blueprints.globals.fiware_resources.has_userlayers(loc) and blueprints.keyrock_blueprint.get_is_userlayer_available(access_token):
            data['has_user_layers'] = True
            data['user_layers'] = blueprints.globals.fiware_resources.get_userlayer_names(loc)

        data['controlled_properties'] = blueprints.orion_device.get_puc_unique_device_controlled_properties(deviceInfo)

        payload = unexeaqua3s.json.dumps(data);
        blueprints.debug.dump_payload_to_disk('get_pilot_data('+loc+')', payload)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return payload
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500

@blueprint.route('/a3s_get_device_data', methods=['GET'])
@cross_origin()
def get_device_data():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False  or blueprints.keyrock_blueprint.get_is_mapview_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        loc = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        deviceInfo = blueprints.orion_device.get_deviceInfo(loc)

        data = blueprints.orion_device.get_device_extended_data(deviceInfo,request.args.get('device_type'), visualise_alerts = blueprints.keyrock_blueprint.get_is_mapview_alerts_available(access_token))

        payload = unexeaqua3s.json.dumps(data)
        blueprints.debug.dump_payload_to_disk('a3s_get_device_data('+loc+')', payload)

        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return payload
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500

    blueprints.debug.servicelog.log(inspect.currentframe(), 'end')

#--------------------------------------------------------------------------------------------------------------------------------------------------
@blueprint.route("/get_simulation_global_data", methods=['GET'])
def get_simulation_global_data():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))

        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False or blueprints.keyrock_blueprint.get_is_mapview_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        if blueprints.keyrock_blueprint.get_is_epanet_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        fiware_service = blueprints.keyrock_blueprint.get_location(access_token)
        data = {}
        data['frame count'] = 0


        if blueprints.globals.fiware_resources.has_waternetwork(fiware_service) == True:
            data['frame count'] = blueprints.globals.fiware_resources.waternetwork_get_frame_count(fiware_service)
            data['layers'] = blueprints.globals.fiware_resources.get_geojson_for_slipmap(fiware_service)

        payload = unexeaqua3s.json.dumps(data);
        blueprints.debug.dump_payload_to_disk('get_simulation_global_data('+fiware_service+')', payload)
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return payload
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500

@blueprint.route("/get_simulation_frame", methods=['GET'])
def get_simulation_frame():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))

        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.get_is_epanet_available(access_token) == False or blueprints.keyrock_blueprint.get_is_mapview_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        fiware_service = blueprints.keyrock_blueprint.get_location(access_token)

        data = {}

        if blueprints.globals.fiware_resources.has_waternetwork(fiware_service) == True:
            data = get_network_frame_data_as_colourmap(fiware_service, int(request.args.get('frame')))
            payload = unexeaqua3s.json.dumps(data);
            blueprints.debug.dump_payload_to_disk('get_simulation_frame('+fiware_service+')', payload)
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return payload

        return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), 'No network'), 500
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500

# --------------------------------------------------------------------------------------------------------------------------------------------------
@blueprint.route("/userfile/<path:path>")
def get_file(path):
    """Download a file."""
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False  or blueprints.keyrock_blueprint.get_is_mapview_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end-403' + str(access_token))
            return 'Invalid', 403


        fiware_service = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))

        zipdata = blueprints.globals.fiware_resources.get_zip_data(fiware_service, path)

        if len(zipdata) > 0:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            fileobj = io.BytesIO(zipdata)
            return send_file(fileobj, mimetype='application/zip')#, attachment_filename=path)
        else:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end-401 ' + str(access_token))
            return 'invalid', 401
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500

    blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
    return "Record not found", 400

# --------------------------------------------------------------------------------------------------------------------------------------------------

def dump_epanet_static_data(fiware_service, epanet_component_type, index):
    label = ''
    entry = blueprints.globals.fiware_resources.resources[fiware_service]['epanet'].fiware_component[epanet_component_type][index]
    for key in entry:
        if 'type' in entry[key] and entry[key]['type'] == 'Property':
            label += '<b>'
            label += key
            label += '</b>'
            label += ' '

            if isinstance(entry[key]['value'], str):
                label += str(entry[key]['value'])
            else:
                label += str(round(entry[key]['value'], 2))

            if 'unitCode' in entry[key]:
                label += unexefiware.units.get_property_unitcode_printname(entry[key]['unitCode'])

            label += '<br>'

    return label


@blueprint.route('/get_layer_data', methods=['GET'])
@cross_origin()
def get_layer_data():
    try:
        blueprints.debug.servicelog.log(inspect.currentframe(), 'start:' + str(request))
        access_token = request.args.get('access_token')
        if blueprints.keyrock_blueprint.ok(access_token) == False or blueprints.keyrock_blueprint.get_is_mapview_available(access_token) == False:
            blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
            return 'Invalid', 403

        link_status_codes = []
        link_status_codes.append('Closed (pump shutoff head exceeded)')
        link_status_codes.append('Temporarily closed')
        link_status_codes.append('Closed')
        link_status_codes.append('Open')
        link_status_codes.append('Active (partially open)')
        link_status_codes.append('Open (pump max. flow exceeded)')
        link_status_codes.append('Open (FCV can\'t supply flow)')
        link_status_codes.append('Open (PRV/PSV can\'t supply pressure)')

        data = {}
        fiware_service = blueprints.keyrock_blueprint.get_location(request.args.get('access_token'))
        layer = request.args.get('layer')
        index = int(request.args.get('index'))

        epanet_frame = int(request.args.get('epanet_frame'))

        data['layer'] = layer

        layer_info = {}


        if blueprints.globals.fiware_resources.is_waternetwork_layer(fiware_service, layer):
            # do waterlayer stuff
            try:
                src_index = blueprints.globals.fiware_resources.resources[fiware_service]['geojson'][layer]['geojson']['features'][index]['properties']['sim_source_index']
                src_type = blueprints.globals.fiware_resources.resources[fiware_service]['geojson'][layer]['geojson']['features'][index]['properties']['sim_source']

                if 'pipe' in layer:
                    layer_info['component'] = '<b>'
                    layer_info['component'] += 'Pipe'
                    layer_info['component'] += ' '
                    layer_info['component'] += '</b>'
                    layer_info['component'] += blueprints.globals.fiware_resources.resources[fiware_service]['epanet'].epanet_lookups[src_type]['index'][src_index]
                    layer_info['component'] += '<br>'

                    layer_info['component'] += dump_epanet_static_data(fiware_service, 'Pipe', index)

                if 'pump' in layer:
                    layer_info['component'] = '<b>'
                    layer_info['component'] += 'Pump'
                    layer_info['component'] += ' '
                    layer_info['component'] += '</b>'
                    layer_info['component'] += blueprints.globals.fiware_resources.resources[fiware_service]['epanet'].epanet_lookups[src_type]['index'][src_index]
                    layer_info['component'] += '<br>'

                    layer_info['component'] += dump_epanet_static_data(fiware_service, 'Pump', index)

                if 'valve' in layer:
                    layer_info['component'] = '<b>'
                    layer_info['component'] += 'Valve'
                    layer_info['component'] += ' '
                    layer_info['component'] += '</b>'
                    layer_info['component'] += blueprints.globals.fiware_resources.resources[fiware_service]['epanet'].epanet_lookups[src_type]['index'][src_index]
                    layer_info['component'] += '<br>'

                    layer_info['component'] += dump_epanet_static_data(fiware_service, 'Valve', index)

                if 'junction' in layer:
                    layer_info['component'] = '<b>'
                    layer_info['component'] += 'Junction'
                    layer_info['component'] += ' '
                    layer_info['component'] += '</b>'
                    layer_info['component'] += blueprints.globals.fiware_resources.resources[fiware_service]['epanet'].epanet_lookups[src_type]['index'][src_index]
                    layer_info['component'] += '<br>'

                    layer_info['component'] += dump_epanet_static_data(fiware_service, 'Junction', index)

                if 'reservoir' in layer:
                    layer_info['component'] = '<b>'
                    layer_info['component'] += 'Reservoir'
                    layer_info['component'] += ' '
                    layer_info['component'] += '</b>'
                    layer_info['component'] += blueprints.globals.fiware_resources.resources[fiware_service]['epanet'].epanet_lookups[src_type]['index'][src_index]
                    layer_info['component'] += '<br>'

                    layer_info['component'] += dump_epanet_static_data(fiware_service, 'Reservoir', index)

                if 'tank' in layer:
                    layer_info['component'] = '<b>'
                    layer_info['component'] += 'Tank'
                    layer_info['component'] += ' '
                    layer_info['component'] += '</b>'
                    layer_info['component'] += blueprints.globals.fiware_resources.resources[fiware_service]['epanet'].epanet_lookups[src_type]['index'][src_index]
                    layer_info['component'] += '<br>'

                    layer_info['component'] += dump_epanet_static_data(fiware_service, 'Tank', index)

                layer_info['simulation'] = '<b>Simulation Frame:</b> ' +str(epanet_frame)
                layer_info['simulation'] += '<br>'

                if src_type == 'links':
                    bin_file = blueprints.globals.fiware_resources.resources[fiware_service]['sim_data']

                    layer_info['simulation'] += '<b>Flow:</b> ' + str(round(bin_file.link_flow(epanet_frame, src_index), 2)) + unexefiware.units.get_property_unitcode_printname('G51')#LPS
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Velocity:</b> ' + str(round(bin_file.link_velocity(epanet_frame, src_index), 2)) + unexefiware.units.get_property_unitcode_printname('MTS')
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Headloss:</b> ' + str(round(bin_file.link_headloss(epanet_frame, src_index), 2)) +'m/km'
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Quality:</b> ' + str(round(bin_file.link_quality(epanet_frame, src_index), 2))
                    layer_info['simulation'] += '<br>'
                    try:
                        layer_info['simulation'] += '<b>Status:</b> ' + link_status_codes[int(bin_file.link_status(epanet_frame, src_index))]
                    except Exception as e:
                        layer_info['simulation'] += '<b>Status:</b> ' + str(int(bin_file.link_status(epanet_frame, src_index)))

                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Setting:</b> ' + str(round(bin_file.link_setting(epanet_frame, src_index), 2))
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Reaction:</b> ' + str(round(bin_file.link_reaction(epanet_frame, src_index), 2))
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Friction:</b> ' + str(round(bin_file.link_friction(epanet_frame, src_index), 2)) +'DW'
                    layer_info['simulation'] += '<br>'

                if src_type == 'nodes':
                    bin_file = blueprints.globals.fiware_resources.resources[fiware_service]['sim_data']
                    layer_info['simulation'] += '<b>Demand:</b> ' + str(round(bin_file.node_supply(epanet_frame, src_index), 2)) + unexefiware.units.get_property_unitcode_printname('G51')#LPS
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Head:</b> ' + str(round(bin_file.node_head(epanet_frame, src_index), 2)) +'M'
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Pressure:</b> ' + str(round(bin_file.node_pressure(epanet_frame, src_index), 2)) +'M'
                    layer_info['simulation'] += '<br>'
                    layer_info['simulation'] += '<b>Quality:</b> ' + str(round(bin_file.node_quality(epanet_frame, src_index), 2))
                    layer_info['simulation'] += '<br>'

                data['data'] = layer_info
            except Exception as e:
                blueprints.debug.servicelog.exception(inspect.currentframe(), e )
                blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
                return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500
        else:
            try:

                if layer == 'leak_localisation':
                    layer_info['component'] = '<b>'
                    layer_info['component'] += 'Leak Localisation'
                    layer_info['component'] += '</b>'
                    layer_info['component'] += '<br>'


                    layer_info['component'] += 'Covered Leak Probability: 55%'

                    layer_info['simulation'] = ''

                    data['data'] = layer_info
                else:
                    layer_info['component'] = '<b>'
                    layer_info['component'] += layer
                    layer_info['component'] += '</b>'
                    layer_info['component'] += '<br>'

                    layer_info['simulation'] = ''

                    src = blueprints.globals.fiware_resources.resources[fiware_service]['userlayer'][layer]['server'][index]
                    for item in src:
                        layer_info['component'] += item
                        layer_info['component'] += ' : '
                        layer_info['component'] += str(src[item])
                        layer_info['component'] += '<br>'

                    waterlookup_table = get_waterlookup_table(layer)

                    if waterlookup_table != None:
                        text = ''
                        text += '<table>'
                        text += '<tr>'
                        text += '<th> Label </th>'
                        text += '<th> Desc </th>'
                        text += '<th> Colour </th>'
                        text += '</tr>'

                        for i in waterlookup_table:
                            text += '<tr>'
                            text += '<td text-align: center;>'

                            colour = '#000000'

                            text += '<span class="name" style="color:' + colour + '">'

                            text += i[0]

                            text += '</td>'

                            text += '<td>'
                            text += '<span class="name" style="color:' + colour + '">'

                            text += i[1]
                            text += '</td>'

                            text += '<td style="background-color:' + i[2]+'">'
                            text += '<span class="name" style="color:' + colour + '">'
                            text += '</span>'
                            text += '</td>'
                            text += '</tr>'



                        layer_info['simulation'] = text

                    data['data'] = layer_info

            except Exception as e:
                blueprints.debug.servicelog.exception(inspect.currentframe(), e )
                blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
                return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500

        payload = unexeaqua3s.json.dumps(data)
        blueprints.debug.dump_payload_to_disk('get_layer_data(' + fiware_service + ':' + layer + ')', payload)
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return payload
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
        blueprints.debug.servicelog.log(inspect.currentframe(), 'end ' + str(access_token))
        return blueprints.debug.servicelog.formatmsg(inspect.currentframe(), str(e)), 500


def get_network_frame_data(pilot_name, period):
    frame_data = {}

    try:
        if True:
            sim_data = blueprints.globals.fiware_resources.resources[pilot_name]['sim_data']

            if sim_data and period < sim_data.reporting_periods():
                node_labels = [epanet_fiware.epanet_outfile_handler.NodeResultLabels.Supply,
                               epanet_fiware.epanet_outfile_handler.NodeResultLabels.Head,
                               epanet_fiware.epanet_outfile_handler.NodeResultLabels.Pressure,
                               epanet_fiware.epanet_outfile_handler.NodeResultLabels.Quality]

                link_labels = [epanet_fiware.epanet_outfile_handler.LinkResultLabels.Flow,
                               epanet_fiware.epanet_outfile_handler.LinkResultLabels.Velocity,
                               epanet_fiware.epanet_outfile_handler.LinkResultLabels.Headloss,
                               epanet_fiware.epanet_outfile_handler.LinkResultLabels.Quality,
                               epanet_fiware.epanet_outfile_handler.LinkResultLabels.Status,
                               epanet_fiware.epanet_outfile_handler.LinkResultLabels.Setting,
                               epanet_fiware.epanet_outfile_handler.LinkResultLabels.ReactionRate,
                               epanet_fiware.epanet_outfile_handler.LinkResultLabels.FrictionFactor]

                for label in node_labels:
                    try:
                        frame_data[str(label)] = sim_data.node_sim_frame(period, label)
                    except Exception as e:
                        frame_data[str(label)] = []
                        print('get_network_frame_data()-' + str(e))

                for label in link_labels:
                    try:
                        frame_data[str(label)] = sim_data.link_sim_frame(period, label)
                    except Exception as e:
                        frame_data[str(label)] = []
                        blueprints.debug.servicelog.exception(inspect.currentframe(), e )

            else:
                blueprints.debug.servicelog.log(inspect.currentframe(), 'epanet_broker:get_network_frame_data()-' +'period out of range:' + str(period) )
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )
    return frame_data

def sim_value_to_colour(label, value):

    if label == 'LinkResultLabels.Flow':
        return colour_0_to_100(value)

    if label == 'LinkResultLabels.Velocity':
        if value < 0.01:
            return '#0000ff'


        if value < 0.1:
            return '#00ffff'

        if value < 1.0:
            return '#00ff00'
        if value < 2.0:
            return '#ffff00'

        return '#ff0000'

    if label == 'LinkResultLabels.Headloss':
        return '#000000'

    if label == 'LinkResultLabels.Quality':
        if value < 0.2:
            return '#0000ff'

        if value < 0.4:
            return '#00ffff'

        if value < 0.6:
            return '#00ff00'

        if value < 0.8:
            return '#ffff00'

        return '#ff0000'


    if label == 'LinkResultLabels.Status':
        return '#000000'

    if label == 'LinkResultLabels.Setting':
        return '#000000'

    if label == 'LinkResultLabels.ReactionRate':
        if value < 0.1:
            return '#0000ff'

        if value < 0.5:
            return '#00ffff'

        if value < 1.0:
            return '#00ff00'

        if value < 5.0:
            return '#ffff00'

        return '#ff0000'

    if label == 'LinkResultLabels.FrictionFactor':
        if value < 0.001:
            return '#0000ff'

        if value < 0.010:
            return '#00ffff'

        if value < 0.10:
            return '#00ff00'

        if value < 1.0:
            return '#ffff00'

        return '#ff0000'

    if label == 'NodeResultLabels.Supply':
        return colour_0_to_100(value)

    if label == 'NodeResultLabels.Head':
        return colour_0_to_100(value)

    if label == 'NodeResultLabels.Pressure':
        return colour_0_to_100(value)

    if label == 'NodeResultLabels.Quality':
        if value < 0.2:
            return '#0000ff'

        if value < 0.4:
            return '#00ffff'

        if value < 0.6:
            return '#00ff00'

        if value < 0.8:
            return '#ffff00'

        return '#ff0000'

    return '#000000'

def colour_0_to_100(value):

    if value < 25:
        return '#0000ff'

    if value < 50:
        return '#00ffff'

    if value < 75:
        return '#00ff00'

    if value < 100:
        return '#ffff00'

    return '#ff0000'

def get_network_frame_data_as_colourmap(pilot_name, period):
    try:
        frame_data = get_network_frame_data(pilot_name,period)

        data = {}
        data['frame_data'] = {}
        data['colour_lookup'] = {}
        data['colour_reverse_lookup'] = []


        for key in frame_data:
            new_data = []
            for i in range(0, len(frame_data[key])):
                colour = sim_value_to_colour(key, frame_data[key][i])

                if colour not in data['colour_lookup']:
                    data['colour_lookup'][colour] = len(data['colour_lookup'])
                    data['colour_reverse_lookup'].append(colour)

                new_data.append(data['colour_lookup'][colour])

            data['frame_data'][key] = new_data
    except Exception as e:
        blueprints.debug.servicelog.exception(inspect.currentframe(), e )

    return data