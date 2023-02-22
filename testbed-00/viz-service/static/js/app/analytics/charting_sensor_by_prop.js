class charting_sensor_by_prop extends charting_base
{
    constructor()
    {
        super();
        this.current_time_option = 3;
        this.root = undefined;

        this.property_options_label = 'properties';
        this.property_labels = [];
        this.property_values = [];
        this.current_property = -1;
    }

    onInit(root)
    {
        //if(this.root === undefined)
        {
            super.onInit(root);
            this.root = root;
        }

        let payload = {};
        payload['access_token'] = window.access_token;
        payload['time_mode'] = this.time_options[this.current_time_option].toLowerCase();

        if(this.current_property != -1)
        {
            payload['property'] = this.property_values[this.current_property].toLowerCase();
        }

        let cmd = 'get_chart_sensor_by_prop';

        axios.get(cmd, {params: payload}).then(response =>
        {
            //get the properties for the pilot
            if (response.status !== 200)
            {
                alert_message(arguments,'Can\'t load data from server');
                return;
            }

            let pilot_data = response.data;

            if ('prop_data' in pilot_data)
            {
                if (this.property_labels.length === 0)
                {
                    for (let i = 0; i < pilot_data['prop_data'].length; i++)
                    {
                        this.property_labels.push(pilot_data['prop_data'][i]['print_text']);
                        this.property_values.push(pilot_data['prop_data'][i]['prop_name']);
                        this.current_property = 0;
                    }
                }
            }

            // layout the UI
            this.layout_ui(response.data);
            // fill the charts

        }).catch(function (error)
        {
            if (error.response)
            {
                let text = 'GET Error:' + error.response.data;
                alert_message(arguments,text);
                return;
            }
        });
    }

    layout_ui(pilot_data)
    {
        let element = document.getElementById('charting_prop_by_sensor-container');

        if (element !== null)
        {
            element.parentNode.removeChild(element);
        }


        // have 3 charts per row, 1 for each property
        let container = document.createElement('div');
        container.className = 'container-fluid';
        container.id = 'charting_prop_by_sensor-container';
        this.root.appendChild(container);

        {
            let div = document.createElement('div');
            div.className = "row pt-1";
            container.appendChild(div);

            if ((('prop_data' in pilot_data) && (pilot_data['prop_data'].length > 0))
                && (('device_data' in pilot_data) && (pilot_data['device_data'].length > 0))
            )
            {
                this.add_radio(div, this.time_options_label, this.time_options, this.current_time_option);
                this.add_radio(div, this.property_options_label, this.property_labels, this.current_property);

                this.add_graphs(container, pilot_data['device_data'].length);

                this.populate_graphs(pilot_data);
            }
            else
            {
                this.add_content_end_msg(container,'No graphs are present');
            }
        }
    }

    populate_graphs(chart_data)
    {
        let chart_defintion = this.get_chart_definition();

        for(let chart_index=0;chart_index< chart_data['device_data'].length;chart_index++)
        {
            let current_chart = chart_data['device_data'][chart_index];

            chart_defintion.series = [];

            //for(let series_index =0;series_index < current_chart['devices'].length; series_index++)
            {
                let series = {};
                series['name'] = current_chart['name'];
                series['data'] = current_chart['values'];
                series['type'] = 'line';
                series['marker'] = false;

                chart_defintion.series.push(series);
            }

            chart_defintion.xAxis.categories = current_chart['labels'];
            chart_defintion.xAxis.tickInterval = current_chart['tick_interval'];

            chart_defintion.chart.type = 'line';
            chart_defintion.title.text = current_chart['main_text'];// + ' ' + chart_index.toString();
            chart_defintion.subtitle.text = current_chart['sub_text'];
            chart_defintion.yAxis.title.text = current_chart['unit_text'];

            if (chart_defintion.yAxis.title.text === undefined)
            {
                chart_defintion.yAxis.title.text = 'Add text here!';
            }

            try
            {
                Highcharts.chart('graph-' + chart_index.toString(), chart_defintion);
            }
            catch(error)
            {
                console.log('Charting failed: '+error);
            }
        }
    }

    on_radio_button(radio_group, id)
    {
        if (radio_group === this.time_options_label)
        {
            let option = this.id_to_index(radio_group, this.time_options, id);

            if (option != -1)
            {
                this.current_time_option = option;

                this.onInit(this.root);
            }

            return;
        }

        if (radio_group === this.property_options_label)
        {
            let option = this.id_to_index(radio_group, this.property_labels, id);

            if (option != -1)
            {
                this.current_property = option;
                this.onInit(this.root);
            }

            return;
        }
    }
}