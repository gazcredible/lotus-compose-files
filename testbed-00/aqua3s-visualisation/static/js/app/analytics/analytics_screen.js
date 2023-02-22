class AnalyticsScreen extends charting_base
{
    constructor(access_token)
    {
        super();

        window.access_token = access_token;

        this.mode_select_label = 'analytics_screen_mode_select';
        this.mode_select_options = ['Charting'];
        this.mode_content_label = 'analytics_screen_mode_content';

        this.mode_lookup = {};
        this.mode_lookup['Charting'] = {'mode': new ChartingPage()};
    }

    onInit(root)
    {
        this.my_root = document.createElement('div');
        this.my_root.id = 'analytics_screen';
        this.my_root.style.overflowY = 'hidden';
        this.my_root.style.overflowX = 'hidden';
        this.my_root.style.overflow = 'hidden';
        this.my_root.style.width = '100%';
        this.my_root.className = 'container-fluid';
        document.body.appendChild(this.my_root);


        //do an arbitrary GET to see if the user is still valid/logged in etc
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

            let nav = document.createElement('nav');
            nav.className="nav nav-pills nav-justified";
            nav.id= this.mode_select_label;
            this.my_root.appendChild(nav);

            $(nav).hover(function ()
            {
                $(this).css('cursor', 'pointer');
            });

             let labels = Object.keys(this.mode_lookup);

            for (let i = 0; i < labels.length; i++)

            {
                let a = document.createElement('nav');
                a.className="nav-item nav-link active";
                a.id = labels[i];
                a.href="#";
                a.innerHTML = a.id;
                a.onclick= function()
                {
                    window.analytics.mode_select(a.id);
                };

                nav.appendChild(a);
            }

            //gareth -  add a shim to make some space between the rows of navs
            {
                let div = document.createElement('div');
                div.className = 'row';
                div.style = 'height:20px;';
                this.my_root.appendChild(div);
            }

            {
                let labels = Object.keys(this.mode_lookup);
                this.mode_select(labels[0]);
            }

        }).catch(function (error)
        {
            if (error.response)
            {
                let text = 'GET Error:' + error.response.data;
                   alert_message(   arguments,text);
                return;
            }
        });
    }

    mode_select(option_label)
    {
        let elements = document.getElementById(this.mode_select_label).childNodes;

        for(let i=0;i< elements.length;i++)
        {
            elements[i].className = "nav-item nav-link";

            if(elements[i].id === option_label)
            {
                elements[i].className += " active";
            }
        }


        let screen_user_content_root = 'screen_user_content_root';
        //do something this active thing
        {
            let container = document.getElementById(screen_user_content_root);

            if(container !== null)
            {
                container.remove();
            }
        }

        let container = document.createElement('div');
        container.id = screen_user_content_root;
        //gareth document.body.appendChild(container);
        this.my_root.appendChild(container);

        this.mode_lookup[option_label]['mode'].onInit(container);
    }
}

class AnalyticsChartBase extends ScrollingGraphContentWidget
{
    /*
        +-------+------+
        |  PBS  |  SBP |
        +-------+------+
        | fixed buttons|
        +--------------+
        | scrolling    |
        | content      |
        +--------------+

    */
    constructor()
    {
        super();
    }

    onInit(root)
    {
        if (root !== undefined)
        {
            this.my_root = root;
        }

        this.build_ui();
    }

    build_ui()
    {
        this.root_content_id = 'analytics-root-content';

        let container = document.getElementById(this.root_content_id);

        if(container !== null)
        {
            container.remove();
        }

        let row = document.createElement('div');
        row.className = 'row-12';
        row.id = this.root_content_id;
        this.my_root.appendChild(row);

        let r = document.createElement('div');
        r.className = 'row';
        row.appendChild(r);

        let col = document.createElement('div');
        col.className = 'col-3';
        col.id = 'analytics-time';
        r.appendChild(col);

        col = document.createElement('div');
        col.className = 'col-9';
        col.id = 'analytics-props';
        r.appendChild(col);

        let srcoll_content = document.createElement('div');
        srcoll_content.className = 'row-12';
        srcoll_content.id = 'analytics-scroll-content';
        srcoll_content.style.height = '100vh';
        srcoll_content.style.overflowY = 'scroll';

        row.appendChild(srcoll_content);
    }

    get_scrolling_content_tag()
    {
        return document.getElementById('analytics-scroll-content');
    }
}


class PBS extends AnalyticsChartBase
{
    constructor()
    {
        super();
        this.my_root = undefined;
        this.current_time_option = 3;
    }


    onInit(root)
    {
        super.onInit(root);
        //this.my_root = root;
        //do this for scrollable content

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

            this.build_ui();


            // have 3 charts per row, 1 for each property
            let container = document.createElement('div');
            container.className = 'container-fluid';
            container.id = 'charting_prop_by_sensor-container';
            this.get_scrolling_content_tag().appendChild(container);

            if (  ('props' in pilot_data )
                &&(pilot_data['props'].length > 0)
            )
            {
                this.add_radio(document.getElementById('analytics-time'), 'time_mode', this.time_options, this.current_time_option);

                this.add_graphs(container, pilot_data['props'].length);
                this.populate_graphs(pilot_data);

                this.add_gutter(container);
            }
            else
            {
                this.add_content_end_msg(container,'No graphs are present');
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


class SBP extends AnalyticsChartBase
{
    constructor()
    {
        super();
        this.current_time_option = 3;
        this.my_root = undefined;

        this.property_options_label = 'properties';
        this.property_labels = [];
        this.property_values = [];
        this.current_property = -1;
    }

    onInit(root)
    {
        super.onInit(root);
        
        //do this for scrollable content
        

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
        this.build_ui();


        // have 3 charts per row, 1 for each property
        let container = document.createElement('div');
        container.className = 'container-fluid';
        container.id = 'charting_prop_by_sensor-container';
        this.get_scrolling_content_tag().appendChild(container);

        {
            if ((('device_data' in pilot_data) && (pilot_data['device_data'].length > 0))
            && (('prop_data' in pilot_data) && (pilot_data['prop_data'].length > 0))
            )
            {
                this.add_radio(document.getElementById('analytics-time'), 'time_mode', this.time_options, this.current_time_option);
                this.add_radio(document.getElementById('analytics-props'), this.property_options_label, this.property_labels, this.current_property);

                this.add_graphs(container, pilot_data['device_data'].length);

                this.populate_graphs(pilot_data);
                this.add_gutter(container);
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

            if ('y_plotlines' in current_chart)
                {
                    chart_defintion.yAxis.plotLines = current_chart['y_plotlines'];
                }

            if ('graph_range' in current_chart)
                chart_defintion.yAxis.min = current_chart['graph_range']['min'];
                chart_defintion.yAxis.max = current_chart['graph_range']['max'];


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

                this.onInit(this.my_root);
            }

            return;
        }

        if (radio_group === this.property_options_label)
        {
            let option = this.id_to_index(radio_group, this.property_labels, id);

            if (option != -1)
            {
                this.current_property = option;
                this.onInit(this.my_root);
            }

            return;
        }
    }
}

class AnalyticsScreen2 extends BasePageWidget
{
    constructor()
    {
        super();


        this.mode_select_options = {};
        this.mode_select_options['Properties By Sensor']  = new PBS();
        this.mode_select_options['Sensors By Property']  = new SBP();

        this.my_root = undefined;
        this.current_mode = Object.keys(this.mode_select_options)[0];

        //gareth -  these need to be unique as they hook into the html
        this.mode_select_label = this.constructor.name + '_select';
        this.mode_content_label = this.constructor.name + '_content';
    }
}


function analytics_initialise(access_token)
{
    window.analytics = new AnalyticsScreen(access_token);
    window.analytics = new AnalyticsScreen2(access_token);
    window.analytics.onInit(document.body);
}