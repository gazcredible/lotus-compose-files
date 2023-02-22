class LayerPopupInfo
{
    constructor()
    {
        this.index = -1;
        this.content = '';
        this.fetching_content = false;
    }

    remove()
    {
        this.index = -1;
        this.content = '';
        this.fetching_content = false;
    }

    isActive()
    {
        return (this.index !== -1) && (this.fetching_content === false);
    }

    toString()
    {
        if (this.isActive() == true)
        {
            return this.content;
        }

        return 'why?';
    }

    set(layer_name, index)
    {
        if (index !== undefined)
        {
            this.index = index;
            this.fetching_content = true;

            let payload = {};
            payload['access_token'] = window.access_token;
            payload['layer'] = layer_name;
            payload['index'] = index;
            payload['epanet_frame'] = window.mapview.waternetwork.current_frame;

            let cmd = 'get_layer_data';

            axios.get(cmd, {params: payload}).then(response =>
            {
                if (response.status !== 200)
                {
                    alert_message(arguments,'Can\'t load data from server');
                    return;
                }
                window.mapview.on_get_layer_data(response.data['layer'],response.data['data']);
            }).catch(function (error)
            {
                if (error.response)
                {
                    let text = 'GET Error:' + error.response.data;
                    alert_message(arguments,text);
                }
            });
        }
    }

    on_get_layer_data(data)
    {
        this.fetching_content = false;

        if(this.isActive() === true)
        {
            this.content = data;
        }
        else
        {
            this.content = '';
        }
    }
}

class mapview
{
    constructor(access_token)
    {
        this.map = undefined;

        this.pilot_device_data = undefined;
        this.marker_lookup = {};
        this.pilot_data = {};
        this.current_view = {};
        this.current_device_type = undefined;
        this.delete_markers_on_update = false;
        this.mapbox_isready_for_style = false;

        this.epanetmodel = undefined;
        this.userlayers = undefined;

        window.access_token = access_token;
        this.last_device_data_time = 0;
        this.read_server_every_n_seconds = 10;

        this.mapviewui = undefined;
        this.layer_popup = {};
        this.layer_popup_location = undefined;
    }

    has_epanet_access()
    {
        if ('has_water_network' in this.pilot_data)
            return this.pilot_data['has_water_network'];

        return false;
    }

    has_userlayer_access()
    {
        if ('has_user_layers' in this.pilot_data)
            return this.pilot_data['has_user_layers'];

        return false;
    }

    on_get_layer_data(layer_name, data)
    {
        this.layer_popup[layer_name].on_get_layer_data(data);
        this.update_layer_popup();
    }

    add_to_layer_popup(layer_name, index, lnglat)
    {
        if (layer_name in this.layer_popup == false)
        {
            this.layer_popup[layer_name] = new LayerPopupInfo();
        }

        this.layer_popup[layer_name].set(layer_name, index);

        this.layer_popup_location = lnglat;
        this.update_layer_popup();
    }

    update_layer_popup()
    {
        let text = '';
        let active = 0;
        for (const [key, value] of Object.entries(this.layer_popup))
        {
            if (value.isActive() === true)
            {
                active += 1;
            }
        }

        if (active > 0)
        {
            let labels = ['component','simulation'];
            for (let i=0; i< 2;i++)
            {
                text += '<tr style="vertical-align:top; background-color: #ffffff;">';
                for (const [key, value] of Object.entries(this.layer_popup))
                {
                    if (value.isActive() === true)
                    {
                        text += '<td>';
                        text += value['content'][labels[i]];
                        text += '</td>';
                    }
                }
                text += '</tr>';
            }

            this.mapviewui.uishared_hover_popup.addTo(this.map);
            this.mapviewui.uishared_hover_popup.setHTML('<table>'+text+'</table>');
            this.mapviewui.uishared_hover_popup.setLngLat(this.layer_popup_location);
        }
        else
        {
            this.mapviewui.uishared_hover_popup.remove();
        }
    }

    remove_from_layer_popup(layer_name)
    {
        this.layer_popup[layer_name].remove();
        this.update_layer_popup();
    }

    launch()
    {
        let payload = {};
        payload['access_token'] = window.access_token;
        let cmd = 'get_pilot_data';

        axios.get(cmd, {params: payload}).then(response =>
        {
            if (response.status !== 200)
            {
                alert_message(arguments,'Can\'t load data from server');
                return;
            }

            this.pilot_data = response.data;

            this.mapviewui = new mapviewui();
            this.mapviewui.init();

            //this.map = new maplibregl.Map(
            this.map = new maplibregl.Map({
                container: 'map',
                style: 'https://api.maptiler.com/maps/streets/style.json?key=190h5zFBwRUUrVLfgxYK',
                //style: 'https://demotiles.maplibre.org/style.json',
                center: [this.pilot_data['location'][0], this.pilot_data['location'][1]],
                zoom: this.pilot_data['location'][2]
            });

            this.map.on('idle', function (e)
            {
                if(window.mapview.waternetwork !== undefined)
                {
                    window.mapview.waternetwork.on_styleload();
                }
            });

            this.map.on('zoom', function (e)
            {
                window.mapview.current_view['zoom'] = window.mapview.map.getZoom();
                window.mapview.update_info();
            });

            this.map.on('mousemove', function (e)
            {
                window.mapview.current_view['screen_pos'] = e.point;
                window.mapview.current_view['world_pos'] = e.lngLat.wrap();
                window.mapview.current_view['zoom'] = window.mapview.map.getZoom();

                window.mapview.update_info();
            });

            this.map.on('load', function ()
            {
                window.mapview.waternetwork = new mapview_waternetwork();
                window.mapview.waternetwork.init();

                window.mapview.userlayers = new mapview_userlayers();
                window.mapview.userlayers.init();
                window.mapview.set_mapstyle('streets');

                window.mapview.mapviewui.build();
                window.mapview.userlayers.buildui();
                window.mapview.waternetwork.buildui();

                window.mapview.map.addControl(new maplibregl.NavigationControl());
                window.mapview.map.addControl(new maplibregl.ScaleControl({position: 'bottom-right'}));


                let text = document.createElement('div');
                text.className = 'container';
                text.style = 'position: relative';
                let h1 = document.createElement('p');
                h1.id = 'map_debug_text';
                h1.className = 'font-weight-bold text-center ml-1 mr-1';
                text.appendChild(h1);
                h1.innerHTML = '';

                document.body.appendChild(text);

                window.mapview.current_device_type = 'device';


                window.setInterval(function ()
                {
                    window.mapview.periodic_update();
                }, 16); //ms

                window.mapview.periodic_update();
            });

            this.map.on('style.load', function ()
            {
                if(window.mapview.userlayers !== undefined)
                {
                    window.mapview.userlayers.on_styleload();
                }

                if(window.mapview.waternetwork !== undefined)
                {
                    window.mapview.waternetwork.on_styleload();
                }
            });
        }).catch(function (error)
        {
            if (error.response)
            {
                let text = 'GET Error:' + error.response.data;
                alert_message(arguments,text);
            }
        });
    }

    periodic_update()
    {
        let current_seconds = new Date().getTime() / 1000;

        if (current_seconds - this.last_device_data_time > (this.read_server_every_n_seconds * 1))
        {
            this.last_device_data_time = new Date().getTime() / 1000;
            this.get_device_data();
        }
    }

    get_device_data()
    {
        let payload = {};
        payload['access_token'] = window.access_token;
        payload['device_type'] = this.current_device_type;
        let cmd = 'a3s_get_device_data';


        axios.get(cmd, {params: payload}).then(response =>
        {
            if (response.status === 200)
            {
                if (JSON.stringify(this.pilot_device_data) !== JSON.stringify(response.data))
                {
                    this.pilot_device_data = response.data;

                    this.update_devices();

                    this.waternetwork.set_leak_visualisation(this.pilot_device_data['leak_localisation'] === true)
                }
            }
            else
            {
                //alert_message(arguments,'failed to read device data');
            }
        }).catch(function (error)
        {
            //alert_message(arguments, 'failed to read device data: ' + error);
        });
    }

    update_devices()
    {
        if (typeof this.pilot_device_data === 'string')
        {
            alert_message(arguments, 'Device data invalid');
            return;
        }

        if (this.pilot_device_data['marker'].length == 0)
        {
            //alert_message(arguments, 'No devices present, Context Broker may be down');
            return;
        }

        if ((this.delete_markers_on_update === true) && (Object.keys(this.marker_lookup).length > 0))
        {
            for (const [key, value] of Object.entries(this.marker_lookup))
            {
                this.marker_lookup[key].remove();
            }

            this.marker_lookup = {};
            this.delete_markers_on_update = false;
        }

        if ((Object.keys(this.marker_lookup).length === 0) && (Object.keys(this.pilot_device_data).length > 0))
        {
            //add markers
            for (let index = 0; index < this.pilot_device_data['marker'].length; index++)
            {
                let key = this.pilot_device_data['marker'][index]['id'];
                let pos = this.pilot_device_data['marker'][index]['loc'];

                if ('detail' in this.pilot_device_data['marker'][index])
                {
                    this.marker_lookup[key] = new maplibregl.Marker()
                        .setLngLat([pos[0], pos[1]])
                        .setPopup(new maplibregl.Popup({offset: 25, maxWidth: 450}) // add popups
                            .setHTML(this.pilot_device_data['marker'][index]['detail']))
                        .addTo(this.map);
                }
                else
                {
                    this.marker_lookup[key] = new maplibregl.Marker()
                        .setLngLat([pos[1], pos[0]])
                        .setPopup(new maplibregl.Popup({offset: 25, maxWidth: 450}) // add popups
                            .setHTML('No detail!'))
                        .addTo(this.map);
                }
            }
        }

        if (Object.keys(this.marker_lookup).length > 0)
        {
            for (let index = 0; index < this.pilot_device_data['marker'].length; index++)
            {
                let key = this.pilot_device_data['marker'][index]['id'];
                let marker = this.marker_lookup[key];

                let color = this.pilot_device_data['marker'][index]['color'];
                set_marker_colour(marker, color);

                marker.getPopup().setHTML(this.pilot_device_data['marker'][index]['detail']);
            }
        }
    }

    update_info()
    {
        try
        {
            let str = 'screen pos: ' + this.current_view['screen_pos']['x'].toString() + ':' + this.current_view['screen_pos']['y'].toString();

            str += '\n';
            str += 'world pos: ' + this.current_view['world_pos']['lng'].toFixed(3).toString() + ':' + this.current_view['world_pos']['lat'].toFixed(3).toString();
            str += '\n';
            str += 'zoom:' + this.current_view['zoom'].toFixed(2).toString();

            let node = document.getElementById('map_debug_text');

            if (node !== null)
            {
                node.innerHtml = str;
                node.innerHtml = '';
            }
        }
        catch (err)
        {
            alert_message(arguments,arguments, err);
        }
    }

    update_devices_by_property(property)
    {
        if (this.current_device_type !== property)
        {
            this.delete_markers_on_update = true;
        }

        this.current_device_type = property;
        this.get_device_data();
    }

    set_mapstyle(label)
    {
        try
        {
            if (label.toLowerCase().includes('satellite') === true)
            {
                this.map.setStyle(`https://api.maptiler.com/maps/hybrid/style.json?key=190h5zFBwRUUrVLfgxYK`);
            }
            else
            {
                this.map.setStyle('https://api.maptiler.com/maps/streets/style.json?key=190h5zFBwRUUrVLfgxYK');
            }
        }
        catch (err)
        {
            alert_message(arguments,arguments, err);
        }
    }
}

function mapview_initialise(access_token)
{
    window.mapview = new mapview(access_token);
    window.mapview.launch();
}