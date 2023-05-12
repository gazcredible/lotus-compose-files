
class waternetwork_baselayer extends map_layer
{
    constructor(layer_name)
    {
        super(layer_name);
    }

    load_data_into_layer()
    {
        if (window.mapview.map.getSource(this.layer_name)!== undefined)
        {
            return;
        }

        window.mapview.map.addSource(this.layer_name, {'type': 'geojson', 'data': this.data});

        let isline = false;

        if((this.layer_name === 'pipe_geojson') ||(this.layer_name === 'valve_geojson'))
        {
            isline = true;
        }

        if(isline === true)
        {
            window.mapview.map.addLayer(
                {
                    'id': this.layer_name,
                    'type': 'line',
                    'source': this.layer_name,
                    'paint':
                        {
                            'line-color': ['get', 'line-color'],
                            'line-width': ['get', 'line-width'],
                        },
                    'layout':
                        {
                            'visibility': 'visible',
                            'line-join': 'round',
                            'line-cap': 'round'
                        }
                });
        }
        else
        {
            window.mapview.map.addLayer(
            {
                'id': this.layer_name,
                'type': 'circle',
                'source': this.layer_name,
                'paint':
                    {
                        'circle-color': ['get', 'line-color'],
                        'circle-radius': ['get', 'circle-radius'],
                        'circle-stroke-width': 1,
                        'circle-stroke-color': '#000000'
                    },
                'layout':
                    {
                        'visibility': 'visible'
                    }
            });
        }

        window.mapview.map.setLayoutProperty(this.layer_name, 'visibility', 'none');
    }
}

class waternetwork_leaklocalisation extends map_layer
{
    constructor(layer_name)
    {
        super(layer_name);

        this.data = {
            'type': 'FeatureCollection'
            , 'features': [
                {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [
                        [
                            [13.776110855163298, 45.66123319472972],
                            [13.77602944301599, 45.66185367577934],
                            [13.77578767931012, 45.66245531092066],
                            [13.775392907149293, 45.6630198266533],
                            [13.774857116972127, 45.66353007690689],
                            [13.774196582365954, 45.66397056381974],
                            [13.773431365788158, 45.66432790845632],
                            [13.772584709207951, 45.66459125716646],
                            [13.77168232817665, 45.664752611243905],
                            [13.77075163076768, 45.66480706987155],
                            [13.76982088510951, 45.66475297897422],
                            [13.768918360796086, 45.66459198145799],
                            [13.768071470252744, 45.66432896731013],
                            [13.76730593613698, 45.66397192507519],
                            [13.766645010062607, 45.66353169921848],
                            [13.766108766377098, 45.663021660746466],
                            [13.765713492442215, 45.662457301088395],
                            [13.765471193936996, 45.66185576157414],
                            [13.765389230208536, 45.66123531279962],
                            [13.765470090746096, 45.66061479969283],
                            [13.765711319567698, 45.66001306913576],
                            [13.766105589815814, 45.659448397526845],
                            [13.766640926296443, 45.6589379356709],
                            [13.767301069202412, 45.65849718785661],
                            [13.768065967973468, 45.6581395409439],
                            [13.768912390293162, 45.657875857764],
                            [13.769814627725385, 45.657714147182006],
                            [13.770745276558257, 45.657659320843166],
                            [13.771676070138714, 45.65771304399119],
                            [13.772578737417264, 45.657873684889644],
                            [13.77342586162628, 45.658136364382855],
                            [13.774191713011128, 45.658493104090745],
                            [13.774853030321557, 45.65893306873669],
                            [13.775389727327063, 45.65944289524797],
                            [13.775785502897165, 45.660007098633265],
                            [13.776028336116628, 45.66060854230916],
                        ]]
                    },
                    'properties': {
                        'line-width': 2.5,
                        'line-color': '#ff0000',
                        'index': 0
                    },
                },
            ]
        };
    }

    set_visible(visible)
    {
        super.set_visible(visible && window.mapview.waternetwork.leak_visualisation_is_visible);
    }

    load_data_into_layer()
    {
        if (window.mapview.map.getSource(this.layer_name) !== undefined)
        {
            return;
        }

        window.mapview.map.addSource(this.layer_name, {'type': 'geojson', 'data': this.data});

        window.mapview.map.addLayer(
            {
                'id': this.layer_name,
                'type': 'fill',
                'source': this.layer_name,
                'paint':
                    {
                        'fill-color': ['get', 'line-color'],
                        'fill-opacity': 0.4,
                    },
                'layout':
                    {
                        'visibility': 'visible'
                    },
                'filter': ['==', '$type', 'Polygon']
            });

        window.mapview.map.setLayoutProperty(this.layer_name, 'visibility', 'none');
    }
}

class mapview_waternetwork
{
    constructor()
    {
        this.layers = {};

        this.model = undefined;
        this.network_simulation = [];
        this.water_network = undefined;

        this.access_token = undefined;
        this.current_frame = 0;

        this.debug_itcount = 0;

        this.node_modes = [{id:'NodeResultLabels.Supply', label:'Supply'},//0
               {id:'NodeResultLabels.Head', label:'Head'},              //1
               {id:'NodeResultLabels.Pressure', label:'Pressure'},          //2
               {id:'NodeResultLabels.Quality', label:'Quality'}];          //3

        this.link_modes = [{id:'LinkResultLabels.Flow', label:'Flow'}, //0
                {id:'LinkResultLabels.Velocity', label:'Velocity'},        //1
                {id:'LinkResultLabels.Headloss', label:'HeadLoss'},        //2
                {id:'LinkResultLabels.Quality', label:'Quality'},         //3
                {id:'LinkResultLabels.Status', label:'Status'},          //4
                {id:'LinkResultLabels.Setting', label:'Setting'},         //5
                {id:'LinkResultLabels.ReactionRate', label:'Reaction Rate'},    //6
                {id:'LinkResultLabels.FrictionFactor', label:'Friction'}]; //7

        this.current_node_label = this.node_modes[2];
        this.current_link_label = this.link_modes[1];

        this.inJunction = false;
        this.hover_popup = undefined;
        this.leak_visualisation_is_visible = false;
        this.visible = true;
    }

    set_leak_visualisation(visible)
    {
        this.leak_visualisation_is_visible = visible;

        name = 'leak_localisation';
        if (name in this.layers === true)
        {
            this.layers[name].set_visible(this.visible);
        }
    }

    init()
    {
        if (window.mapview.has_epanet_access() === false)
        {
            return;
        }

        let payload = {};
        payload['access_token'] = window.access_token;

        let cmd = 'get_simulation_global_data';

        axios.get(cmd, {params: payload}).then(response =>
        {
            if (response.status !== 200)
            {
                alert_message( arguments,'Can\'t load data from server');
                return;
            }
            else
            {
                this.water_network = response.data;

                this.network_simulation = [];
                for (let i = 0; i < this.reporting_periods(); i++)
                {
                    this.network_simulation.push(undefined);
                }

                this.initialise_sim_gfx();
                this.buildui();
            }
        });

        this.hover_popup = new maplibregl.Popup({
        offset: 25,
        maxWidth:800,
        closeButton: false,
        closeOnClick: false
        });

    }

    set_node_mode_from_ui(value)
    {
        this.current_node_label = value;
        this.set_current_frame(this.current_frame);
    }

    set_link_mode_from_ui(value)
    {
        this.current_link_label = value;
        this.set_current_frame(this.current_frame);
    }

    has_model()
    {
        return this.reporting_periods() > 0;
    }

    reporting_periods()
    {
        try
        {
            if (this.water_network !== undefined)
            {
                return this.water_network['frame count'];
            }
        }catch (e)
        {
            alert_message(arguments,'EpanetModel.reporting_periods()');
        }

        return 0;
    }

    node_name(index)
    {
        try
        {
            return this.water_network['epanet_sim']['global_data']['node_names'][index];
        }catch (e)
        {
            alert_message( arguments,'EpanetModel.node_name()');
        }
    }

    link_name(index)
    {
        try
        {
            return this.water_network['epanet_sim']['global_data']['link_names'][index];
        }catch (e)
        {
            alert_message(arguments,arguments,'EpanetModel.link_name():'+e);
        }
    }

    load_frame(frame)
    {
        if(window.mapview.has_epanet_access() === true) {
            if (this.network_simulation[frame] === undefined) {
                let payload = {};
                payload['access_token'] = window.access_token;
                payload['frame'] = frame;

                let cmd = 'get_simulation_frame';

                axios.get(cmd, {params: payload}).then(response => {
                    if (response.status === 200) {
                        this.network_simulation[frame] = response.data;
                        this.set_current_frame(frame);
                    }
                }).catch(function (error) {
                    if (error.response) {
                        alert_message(arguments, 'GET Error:' + error.response.data);   // `error.response.data` here - NOTE difference
                    }
                });
            } else {
                this.set_current_frame(frame);
            }
        }
    }

    on_styleload()
    {
        this.initialise_sim_gfx();
        this.set_current_frame(this.current_frame);
    }

    set_current_frame(frame)
    {
        if((this.network_simulation[frame] !== undefined) && (this.network_simulation.length > 0))
        {
            this.current_frame = frame;

            //GARETH - need to push this into the layers
            for(let water_layer=0;water_layer< this.water_network['layers'].length;water_layer++)
            {
                let layer = this.water_network['layers'][water_layer];
                let name = layer['name'];

                if (window.mapview.map.getSource(name) !== undefined)
                {
                    for (let i = 0; i < layer['geojson']['features'].length; i++)
                    {
                        let colour = '#ff00ff';
                        try
                        {
                            let layer_source = layer['geojson']['features'][i]['properties']['sim_source'];
                            let layer_index  = layer['geojson']['features'][i]['properties']['sim_source_index'];

                            if (layer_source === 'links')
                            {
                                //do link stuff
                                colour = this.network_simulation[frame]['colour_reverse_lookup'][this.get_link_value(layer_index, this.current_link_label, this.current_frame)];
                            }

                            if (layer_source === 'nodes')
                            {
                                //do node stuff
                                colour = this.network_simulation[frame]['colour_reverse_lookup'][this.get_node_value(layer_index, this.current_node_label, this.current_frame)];
                            }

                        }catch (e)
                        {
                            alert_message(arguments,arguments,'Update layer Error '+ e);
                            return;
                        }

                        layer['geojson']['features'][i]['properties']['line-color'] = colour;
                    }

                    window.mapview.map.getSource(name).setData(layer['geojson']);
                }
            }
        }
    }

    initialise_sim_gfx()
    {
        if((this.water_network !== undefined) && ('layers' in this.water_network))
        {
            for(let i=0;i< this.water_network['layers'].length;i++)
            {
                let layer = this.water_network['layers'][i];
                let name = layer['name'];

                if (name in this.layers === false)
                {
                    this.layers[name] = new waternetwork_baselayer(layer['name']);
                    this.layers[name].load_data(layer['geojson']);
                    this.layers[name].isvisible = false;
                }

                this.layers[name].on_styleload();
                this.layers[name].set_visible(this.layers[name].isvisible);
            }

            name = 'leak_localisation';
            if (name in this.layers === false)
            {
                this.layers[name] = new waternetwork_leaklocalisation(name);
                this.layers[name].isvisible = false;
            }
            this.layers[name].on_styleload();
            this.layers[name].set_visible(this.layers[name].isvisible);

            this.load_frame(this.current_frame);
        }
    }

    get_link_value(link_index,property, frame)
    {
        try
        {
            if (this.network_simulation[frame] !== undefined)
            {
                return this.network_simulation[frame]['frame_data'][property][link_index];
            }
        }catch(e)
        {
            alert_message(arguments,'get_link_value()-'+e);
        }

        return 0;
    }

    get_node_value(node_index,property, frame)
    {
        try
        {
            if (this.network_simulation[frame] !== undefined)
            {
                return this.network_simulation[frame]['frame_data'][property][node_index];
            }
        }
        catch (e)
        {
            alert_message(arguments,'get_node_value()-'+e);
        }
        return 0;
    }

    set_visibility(is_visible)
    {
        this.visible = is_visible
        for (const [key, value] of Object.entries(this.layers))
        {
            this.layers[key].isvisible = is_visible;
            this.layers[key].set_visible(this.layers[key].isvisible);
        }
    }

    buildui()
    {
        let element = document.getElementById('epanet_ui_root');

        if(element !== null)
        {
            element.parentNode.removeChild(element);
        }

        if(window.mapview.has_epanet_access() === true)
        {
            let epanet_ui_root = document.createElement('div');
            epanet_ui_root.id = 'epanet_ui_root';
            window.mapview.mapviewui.menu_slidy_content.appendChild(epanet_ui_root);

            {
                let label = document.createElement('label');
                label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                label.innerHTML = '<br>EPANET Visualisation';
                epanet_ui_root.appendChild(label);
            }

            if (this.has_model() === true)
            {
                //EPANET visualisation show/hide
                {
                    let div = document.createElement('div');
                    div.className = "d-flex justify-content-center";
                    epanet_ui_root.appendChild(div);

                    let button_data = [{id: 'Show', print_text: 'Show'}
                              ,{id: 'Hide', print_text: 'Hide'}];

                    let id = 'epanet_visibility';
                    let div2 = window.mapview.mapviewui.add_button_group(this, id, button_data);
                    div.appendChild(div2);

                    this.on_button_press(id,button_data[0]['id'],"btn btn-primary");
                }

                //EPANET time scrubber
                {
                    let input = document.createElement('input');

                    input.id = "epanet_sim_time_slider";
                    input.type = "range";
                    input.min = "0";
                    input.max = this.reporting_periods();
                    input.step = "0";
                    input.value = "0";
                    input.style = 'width: 100%;';
                    input.onchange = function ()
                    {
                        window.mapview.waternetwork.sim_time_update(input.id, input.value);
                    };

                    epanet_ui_root.appendChild(input);


                    let buttonClassName = "btn btn-primary";

                    {
                        let button = document.createElement('button');
                        button.type = "button";
                        button.className = buttonClassName;

                        button.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                        button.innerHTML = "<<";
                        button.id = 'epanet_sim_time_slider_back';
                        button.onclick = function ()
                        {
                            window.mapview.waternetwork.sim_time_update(button.id, 0);
                        };
                        epanet_ui_root.appendChild(button);
                    }

                    {
                        let button = document.createElement('button');
                        button.type = "button";
                        button.className = buttonClassName;

                        button.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                        button.innerHTML = ">>";
                        button.id = 'epanet_sim_time_slider_next';
                        button.onclick = function ()
                        {
                            window.mapview.waternetwork.sim_time_update(button.id, 0);
                        };
                        epanet_ui_root.appendChild(button);
                    }

                    {
                        let button = document.createElement('button');
                        button.type = "button";
                        button.className = buttonClassName;

                        button.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                        button.innerHTML = "Reset";
                        button.id = 'epanet_sim_time_slider_reset';
                        button.onclick = function ()
                        {
                            window.mapview.waternetwork.sim_time_update(button.id, 0);
                        };
                        epanet_ui_root.appendChild(button);
                    }

                    {
                        let label = document.createElement('label');
                        label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;display: block;";
                        label.id = 'epanet_sim_time_info';
                        label.innerHTML = '<br>Some Value:<br>';
                        epanet_ui_root.appendChild(label);
                    }
                }

                //EPANET mode buttons
                {
                    {
                        let label = document.createElement('label');
                        label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;display: block;";
                        label.innerHTML = '<br>Simulation Mode:<br>';
                        label.style += "display: block;";
                        epanet_ui_root.appendChild(label);
                    }

                    {
                        //1 row, 2 cols -> LHS: node modes RHS: link modes (radio buttons
                        let div = document.createElement('div');
                        div.class = "container";
                        epanet_ui_root.appendChild(div);
                        let row = document.createElement('div');
                        row.className = "row";
                        div.appendChild(row);

                        let buttonClassName = "btn btn-primary";

                        {
                            //node modes ....
                            let col0 = document.createElement('div');
                            col0.className = "col";

                            row.appendChild(col0);


                            let button_data = [];

                            for (let i = 0; i < this.node_modes.length; i++)
                            {
                                let record = {};
                                record['id'] = this.node_modes[i]['id'];
                                record['print_text'] = this.node_modes[i]['label'];

                                button_data.push(record);
                            }

                            let id = 'epanet_sim_node_mode';
                            let div2 = window.mapview.mapviewui.add_vertical_button_group(this, id, button_data);
                            col0.appendChild(div2);

                            this.on_button_press(id, button_data[0]['id'], "btn btn-primary");
                        }
                        {
                            //link_modes
                            let col1 = document.createElement('div');
                            col1.className = "col";
                            row.appendChild(col1);

                            let button_data = [];

                            for (let i = 0; i < this.link_modes.length; i++)
                            {
                                let record = {};
                                record['id'] = this.link_modes[i]['id'];
                                record['print_text'] = this.link_modes[i]['label'];

                                button_data.push(record);
                            }

                            let id = 'epanet_sim_link_mode';
                            let div2 = window.mapview.mapviewui.add_vertical_button_group(this, id, button_data);
                            col1.appendChild(div2);

                            this.on_button_press(id, button_data[0]['id'], "btn btn-primary");
                        }
                    }
                }

                //EPANET fly to node
                {
                    let button_data = [];

                    for (let key of Object.entries(this.water_network.stuff).sort())
                    {
                        button_data.push({id:key[0], print_text: key[0]})
                    }

                    let id = 'epanet_flyto_node';
                    let div2 = window.mapview.mapviewui.add_vertical_button_group(this, id, button_data,"btn btn-primary mb-2");
                    epanet_ui_root.appendChild(div2);
                }

                this.sim_time_update('', 0);
            }
            else
            {
                let div = document.createElement('div');
                div.className = "d-flex justify-content-center";
                epanet_ui_root.appendChild(div);

                let label = document.createElement('label');
                label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                label.innerHTML = 'No EPANET Data avaliable';
                div.appendChild(label);
            }
        }
    }

    sim_time_update(root_id, value)
    {
        if(root_id === 'epanet_sim_time_slider')
        {
            //do something with the slider
        }
        else
        {
            value = this.current_frame;
    
            if (root_id === 'epanet_sim_time_slider_back')
            {
                //move back 1 frame
                if (value > 0)
                {
                    value = value - 1;
                }
            }
    
            if (root_id === 'epanet_sim_time_slider_next')
            {
                //move forward 1 frame
                if ((value + 1) < this.reporting_periods())
                {
                    value = value + 1;
                }
            }
    
            if (root_id === 'epanet_sim_time_slider_reset')
            {
                //reset to 0
                value = 0;
            }
    
            document.getElementById("epanet_sim_time_slider").value = value;
        }
    
        //set the 'epanet_sim_time_info' to be the current time value
        document.getElementById('epanet_sim_time_info').innerHTML = '<br>' + value.toString() +' of ' + this.reporting_periods().toString();
        this.load_frame(value);
    }

    on_button_press(div_id, selected_id, classname)
    {
        if(div_id === 'epanet_flyto_node')
        {
            let val = window.mapview.waternetwork.water_network.stuff[selected_id];
            window.mapview.map.jumpTo({center: [val[1],val[0]], zoom:18});
        }

        if(div_id === 'epanet_sim_node_mode')
        {
            let elements = document.getElementById(div_id);

            if (elements !== null)
            {
                elements = elements.childNodes;

                for (let i = 0; i < elements.length; i++)
                {
                    elements[i].className = classname;

                    if (elements[i].id === selected_id)
                    {
                        elements[i].className += " active";
                    }
                }
            }

            this.set_node_mode_from_ui(selected_id);
            return;
        }

        if(div_id === 'epanet_sim_link_mode')
        {
            let elements = document.getElementById(div_id);

            if (elements !== null)
            {
                elements = elements.childNodes;

                for (let i = 0; i < elements.length; i++)
                {
                    elements[i].className = classname;

                    if (elements[i].id === selected_id)
                    {
                        elements[i].className += " active";
                    }
                }
            }

            this.set_link_mode_from_ui(selected_id);
            return;
        }

        if(div_id === 'epanet_visibility')
        {
            let elements = document.getElementById(div_id);

            if (elements !== null)
            {
                elements = elements.childNodes;

                for (let i = 0; i < elements.length; i++)
                {
                    elements[i].className = classname;

                    if (elements[i].id === selected_id)
                    {
                        elements[i].className += " active";
                    }
                }
            }

            this.set_visibility( selected_id === 'Show');
            return;
        }
    }
}