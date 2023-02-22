/*
This is a grid of property graphs, each graph contains all the sensors that track that property
 */

class charting_prop_by_sensor extends charting_base
{
    constructor()
    {
        super();
        this.root = undefined;
    }


    onInit(root)
    {
        super.onInit(root);

        this.root = root;

        this.current_time_option = 3;

        this.on_radio_button(this.time_options_label, this.current_time_option);
    }

    populate_graphs(chart_data)
    {
        if (chart_data['props'].length > 0)
        {
            let chart_defintion = this.get_chart_definition();

            for (let chart_index = 0; chart_index < chart_data['props'].length; chart_index++)
            {
                let current_chart = chart_data['props'][chart_index];

                chart_defintion.series = [];

                for (let series_index = 0; series_index < current_chart['devices'].length; series_index++)
                {
                    let series = {};
                    series['name'] = current_chart['devices'][series_index]['name'];
                    series['data'] = current_chart['devices'][series_index]['values'];
                    series['type'] = 'line';
                    series['marker'] = false;

                    chart_defintion.series.push(series);
                }

                chart_defintion.xAxis.categories = chart_data['labels'];
                chart_defintion.xAxis.tickInterval = chart_data['tick_interval'];

                chart_defintion.chart.type = 'line';
                chart_defintion.title.text = current_chart['main_text'];// + ' ' + chart_index.toString();
                chart_defintion.subtitle.text = current_chart['sub_text'];
                chart_defintion.yAxis.title.text = current_chart['unit_text'];


                try
                {
                    Highcharts.chart('graph-' + chart_index.toString(), chart_defintion);
                }
                catch (error)
                {
                    console.log('Charting failed: ' + error);
                }
            }
        }
    }

    on_radio_button(radio_group, id)
    {
        let option = this.id_to_index(radio_group, this.time_options, id);

        if (option != -1)
        {
            this.current_time_option = option;
        }


        let payload = {};
        payload['access_token'] = window.access_token;
        payload['time_mode'] = this.time_options[this.current_time_option].toLowerCase();
        let cmd = 'get_chart_prop_by_sensor';

        axios.get(cmd, {params: payload}).then(response =>
        {
            if (response.status !== 200)
            {
                alert_message(arguments,'Can\'t load data from server');
                return;
            }

            let pilot_data = response.data;

            let element = document.getElementById('charting_prop_by_sensor-container');

            if(element !== null)
            {
                element.parentNode.removeChild(element);
            }


            // have 3 charts per row, 1 for each property
            let container = document.createElement('div');
            container.className = 'container-fluid';
            container.id = 'charting_prop_by_sensor-container';
            this.root.appendChild(container);

            if (pilot_data['props'].length > 0)
            {
                {
                    let div = document.createElement('div');
                    div.className = "row pt-1";
                    container.appendChild(div);

                    {
                        this.add_radio(div, 'time_mode', this.time_options, this.current_time_option);
                    }
                }

                this.add_graphs(container, pilot_data['props'].length);
                this.populate_graphs(pilot_data);

                this.add_gutter(container);
            }
            else
            {
                this.add_default_mesaage('charting_mode_content','No graphs are present');
            }

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
}