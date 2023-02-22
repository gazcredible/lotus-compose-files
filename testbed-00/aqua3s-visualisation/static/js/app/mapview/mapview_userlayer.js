/*jshint -W069*/
/*jshint -W080*/
/*jshint -W104*/
/*jshint -W117*/
/* jshint strict: false */
/*jshint esversion: 6*/

//gareth - look at this for re-colouring layers
//https://docs.mapbox.com/mapbox-gl-js/example/color-switcher/

class userlayer extends map_layer
{
    constructor(layer_name)
    {
        super(layer_name);
        this.visualisation_colour = '#ffffff';
    }

    load_data_into_layer()
    {
        if ((this.map !== undefined) && (this.layer_name != undefined) && (this.data !== undefined))
        {
            if ('header' in this.data)
            {
                //new data format
                this.map.addSource(this.layer_name,
                    {
                        'type': 'geojson',
                        'data': this.data['geojson']
                    });

                this.data['header']['id'] = this.layer_name;
                if ('fill-opacity' in this.data['header']['paint'])
                {
                    this.data['header']['paint']['fill-opacity'] = 0.75;
                }
                try
                {
                    this.map.addLayer(this.data['header']);
                }
                catch (e)
                {
                    alert_message(arguments,e);
                }

                if ('info' in this.data)
                {
                    if (this.data['info']['has_colour_lookups'] === false)
                    {
                        try
                        {
                            this.map.setPaintProperty(this.layer_name, this.data['info']['colour_label'], this.visualisation_colour );
                        }
                        catch (e)
                        {

                        }
                    }
                }
            }
        }
    }
}

class mapview_userlayers
{
    constructor()
    {
        this.layer_info = {};

        //move into content server
        this.layer_debug_index = 0;
        this.colours = ['#C00000',
            '#9BBB59',
            '#8064A2',
            '#4BACC6',
            '#F79646',
            '#FFFF00',
            //'#92D050',
            //'#00B050',
            '#00B0F0',
            '#0070C0',
            '#002060',
            '#7030A0',
            //'#FFFFFF',
            '#000000',
            //'#EEECE1',
            '#1F497D',
            '#4F81BD',
            '#C0504D',
            '#FF0000',
            '#FFC000',

            //'#F2F2F2','#808080','#DDD9C4','#C5D9F1',
            //'#DCE6F1','#F2DCDB','#EBF1DE','#E4DFEC',
            //'#DAEEF3','#FDE9D9','#D9D9D9','#595959',
            //'#C4BD97','#8DB4E2','#B8CCE4','#E6B8B7',
            //'#D8E4BC','#CCC0DA','#B7DEE8','#FCD5B4',
            //'#BFBFBF','#404040','#948A54','#538DD5',
            //'#95B3D7','#DA9694','#C4D79B','#B1A0C7',
            //'#92CDDC','#FABF8F','#A6A6A6','#262626',
            //'#494529','#16365C','#366092','#963634',
            //'#76933C','#60497A','#31869B','#E26B0A',
            //'#808080','#0D0D0D','#1D1B10','#0F243E',
            //'#244062','#632523','#4F6228','#403151',
            //'#215967','#974706'
            ];
    }

    getDebugColour()
    {
        let c = this.colours[this.layer_debug_index];

        this.layer_debug_index = this.layer_debug_index+1;
        this.layer_debug_index = this.layer_debug_index % (this.colours.length-1);

        if(c === undefined)
        {
            alert_message(arguments,'Bad colour');
        }

        return c;
    }

    createRandomColour()
    {
        var letters = '0123456789ABCDEF';
        var color = '#';
        for (var i = 0; i < 6; i++)
        {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    }

    init()
    {
        this.layer_debug_index = 0;

        if(('has_user_layers' in window.mapview.pilot_data) && (window.mapview.pilot_data['has_user_layers'] === true))
        {
            for (let i = 0; i < window.mapview.pilot_data['user_layers'].length; i++)
            {
                this.add_layer(window.mapview.pilot_data['user_layers'][i]);
            }
        }
    }

    layer_count()
    {
        return this.layer_names().length;
    }

    layer_names()
    {
        return Array.from(Object.keys(this.layer_info));
    }

    layer_print_name(label)
    {
        return label.replace('.geojson','');
    }

    layer_id(label)
    {
        return label;
    }


    add_layer(info)
    {
        //this was info.name, but name is the only attributes
        this.layer_info[info] = new userlayer(info);
        this.layer_info[info].visualisation_colour = this.getDebugColour();


        this.load_layer(info);
    }

    load_layer(label)
    {
        this.layer_info[label]['loaded'] = true;

        JSZipUtils.getBinaryContent('userfile/' + label+'?access_token='+window.access_token, function (err, data)
        {
            if (err)
            {
                log_message(arguments, 'Cant load:' + label);
            }
            else
            {
                JSZip.loadAsync(data).then(function (zip)
                {
                    zip.file(label).async("string").then(function (data)
                    {
                        let obj = window.mapview.userlayers.layer_info[label];

                        obj.load_data(JSON.parse(data));
                        obj.on_styleload();
                        obj.set_visible(obj.isvisible);
                        window.mapview.userlayers.set_button_status();
                    }).catch(function (error)
                    {
                        if (error)
                        {
                            let text = 'Zip unpack:' + error;

                            alert_message(arguments,text);
                        }
                    });
                }).catch(function (error)
                {
                    if (error)
                    {
                        let text = 'Zip load async:' + error.response.data;

                        alert_message(arguments,text);
                    }
                });
            }
        });
    }

    toggle_layer(label)
    {
        if (this.layer_info[label].isvisible === false)
        {
            if (this.layer_info[label].data === undefined)
            {
                this.load_layer(label);
            }
            else
            {
                this.layer_info[label].set_visible(true);
            }
        }
        else
        {
            this.layer_info[label].set_visible(false);
        }
    }

    get_layer_visibility(label)
    {
        return this.layer_info[label].isvisible;
    }

    on_styleload()
    {
        //for all userlayers that are visibile and loaded, add the user layer

        for (const [key, value] of Object.entries(this.layer_info))
        {
            this.layer_info[key].on_styleload();
            this.layer_info[key].set_visible(this.layer_info[key].isvisible);
        }
    }

    set_button_status()
    {
        if (window.mapview.has_userlayer_access() === true) {
            for (const [key, value] of Object.entries(this.layer_info)) {
                document.getElementById(key).disabled = (this.layer_info[key].data === undefined);
            }
        }
    }

    buildui()
    {
        if (window.mapview.has_userlayer_access() === true) {
            try {
                {
                    let label = document.createElement('label');
                    label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                    label.innerHTML = '<br>User Layers';
                    window.mapview.mapviewui.menu_slidy_content.appendChild(label);
                }

                let div = document.createElement('div');
                div.className = "d-flex justify-content-center";
                window.mapview.mapviewui.menu_slidy_content.appendChild(div);

                //if(('has_user_layers' in pilot_data) && (pilot_data['has_user_layers'] === true))
                if (this.layer_count() > 0) {
                    let button_data = [];

                    for (let i = 0; i < this.layer_names().length; i++) {
                        let record = {};
                        record['id'] = this.layer_names()[i];
                        record['print_text'] = this.layer_print_name(this.layer_names()[i]);

                        button_data.push(record);
                    }

                    let div2 = window.mapview.mapviewui.add_vertical_button_group(this, 'layer_names', button_data, "btn btn-primary");
                    div.appendChild(div2);

                    this.set_button_status();
                } else {
                    let div = document.createElement('div');
                    div.className = "d-flex justify-content-center";
                    menu_slidy_content.appendChild(div);

                    let label = document.createElement('label');
                    label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                    label.innerHTML = 'No Layer Data avaliable';
                    div.appendChild(label);
                }
            } catch (err) {
                alert_message(arguments, err);
            }
        }
    }

    on_button_press(div_id, selected_id, classname)
    {
        if(div_id === 'layer_names')
        {
            let element = document.getElementById(selected_id);

            this.toggle_layer(selected_id);

            if (this.get_layer_visibility(selected_id) === true)
            {
                element.className = classname + " active";
            }
            else
            {
                element.className = classname;
            }
        }
    }
}