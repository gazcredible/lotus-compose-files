class component_base
{
    constructor()
    {
        this.my_root = undefined;
    }

    onInit(root)
    {
        this.my_root = root;
    }

    add_gutter(table)
    {
        for (let i = 0; i < 15; i++)
        {
            let p = document.createElement('p');
            p.innerHTML = '<br>';
            table.appendChild(p);
        }
    }

    add_content_end_msg(table_root, msg)
    {
        let text = document.createElement('div');
        text.className = 'container';
        let h1 = document.createElement('p');
        h1.className = 'text-center';
        text.appendChild(h1);
        h1.innerText = msg;

        document.getElementById("table_root").appendChild(text);
    }
}

class page_base extends component_base
{
    constructor()
    {
        super();
    }
}

class alermolies_view extends component_base
{
    constructor()
    {
        super();
        this.columns = [];
        this.request_command = '';
    }

    on_get_data(table_root, data)
    {

    }

    onInit(root) {
        super.onInit(root);

        let table_root = document.createElement('div');
        table_root.id = 'table_root';
        this.my_root.appendChild(table_root);

        let table = document.createElement('table');
        table.className = 'table';

        table_root.appendChild(table);

        let head = document.createElement('thead');
        table.appendChild(head);

        let tr = document.createElement('tr');
        head.appendChild(tr);

        for (let i = 0; i < this.columns.length; i++)
        {
            let th = document.createElement('th');
            th.scope = 'col';
            th.innerText = this.columns[i];
            tr.appendChild(th);
        }

        let payload = {};
        payload['access_token'] = window.access_token;

        axios.get(this.request_command, {params: payload}).then(response =>
        {
            if (response.status === 200)
            {
                let body = document.createElement('tbody');
                table.appendChild(body);

                if (response.data.length > 0)
                {
                    this.on_get_data(table, response.data);

                    this.add_content_end_msg(table_root, 'End of list');
                }
                else
                {
                   this.add_content_end_msg(table_root, 'No Devices are present 1');
                }

                this.add_gutter(table_root);
            }
            else
            {
                this.add_content_end_msg(table_root,'failed to read data');
            }
        }).catch(function (error)
        {
            this.add_content_end_msg(table_root,  'failed to read data: ' + error);
        });
    }
}

class charting_base extends component_base
{
    constructor()
    {
        super();

        this.time_options_label = 'time_mode';
        this.time_options = ['Daily', 'Weekly', 'Monthly', 'Quarterly', 'Half-Year', 'Year'];
        this.current_time_option = 0;
        this.my_root = undefined;
    }


    id_to_index(radio_group, options, id)
    {
        for(let i=0;i< options.length;i++)
        {
            if(id === options[i])
            {
                return i;
            }
        }

        return -1;
    }


    add_radio(root, group_name, options, current_index)
    {
        //add col for mode
        let col = document.createElement('div');
        col.className = "col-sm";
        root.appendChild(col);

        let btn_group = document.createElement('div');
        btn_group.className="btn-group btn-group-toggle flex-wrap";
        btn_group.setAttribute("data-toggle", "buttons");
        btn_group.id=group_name;
        col.appendChild(btn_group);

        let inst = this;

        for (let i = 0; i < options.length; i++)
        {
            let label = document.createElement('label');
            btn_group.appendChild(label);

            let input = document.createElement('input');

            input.type = "radio";
            input.name = "options";
            label.id = options[i];
            label.textContent = options[i];
            input.setAttribute('autocomplete', "off");

            input.onchange = function ()
            {
                inst.on_radio_button(btn_group.id, options[i]);
            };

            label.appendChild(input);

            if(i === current_index)
            {
                label.className = "btn btn-secondary active";
                input.setAttribute('checked','true');
            }
            else
            {
                label.className = "btn btn-secondary";
            }
        }
    }

    on_radio_button(radio_group, id)
    {
        if(radio_group === this.time_options_label)
        {

        }
    }

    add_graphs(container, number_of_elements, no_of_cols = 2)
    {
        let row = document.createElement('div');
        row.className = 'row';
        container.appendChild(row);

        let col = document.createElement('div');
            col.className = 'col-sm-12';
            row.appendChild(col);

        let graph_container = document.createElement('div');
        graph_container.className = 'container-fluid';
        col.appendChild(graph_container);
        //col.style.height = '100vh';
        //col.style.overflowY = 'scroll';

        //let row2 = document.createElement('div');
        //row2.className = 'row';
        //graph_container.appendChild(row2);


        let no_of_rows = Math.floor((number_of_elements+(no_of_cols-1)) /no_of_cols);

        let graph_index = 0;

        if(true)
        {
            for(let row_count=0;row_count < no_of_rows; row_count++)
            {
                let r = document.createElement('div');
                r.className = 'row';
                for(let i =0; i<2;i++)
                {
                    let graph = document.createElement('div');
                    graph.className = "col-xl-6 col-lg-12";
                    let figure = document.createElement('figure');
                    graph.appendChild(figure);
                    figure.className = "highcharts-figure";
                    figure.id = 'graph-' + graph_index.toString();
                    figure.style = "height:100%; width:100%;";// position:absolute;";

                    graph_index = graph_index + 1;
                    r.appendChild(graph);
                }

                graph_container.appendChild(r);
            }
        }
        else {
            for (let col_count = 0; col_count < no_of_cols; col_count++) {
                let col = document.createElement('div');
                col.className = 'col-sm-' + (12 / no_of_cols).toString();
                row2.appendChild(col);

                for (let row_index = 0; row_index < no_of_rows; row_index++) {
                    let r = document.createElement('div');
                    r.className = 'row';
                    col.appendChild(r);

                    let figure = document.createElement('figure');
                    r.appendChild(figure);
                    figure.className = "highcharts-figure";
                    figure.id = 'graph-' + graph_index.toString();
                    figure.style = "height:100%; width:100%;";// position:absolute;";

                    graph_index = graph_index + 1;
                }

                {
                    let div = document.createElement('div');
                    div.className = 'row';
                    div.style = 'height:100px;';
                    col.appendChild(div);
                }
            }
        }
    }

    get_chart_definition()
    {
        let chart_defintion =
        {
            chart: {
                type: 'coloredline',
                //type: 'column'
                animation: false,
                height: '50%'
            },
            title: {
                text: ''
            },

            credits: {enabled: false},

            subtitle: {
                text: ''
            },
            xAxis: {
                categories: [],

                 labels: {
                     formatter: function ()
                     {
                         let text = '';

                         if (this.value.length == 1 )
                         {
                             text += this.value[0];
                         }
                         else
                         {
                             text += this.value[1]; // date
                         }

                         //return window.charting.graph_label(text);

                        if(text.includes('<br>'))
                        {
                            return text.split('>').pop();
                        }

                        return text;
                     }
                 }
            },
            yAxis: {
                title: {
                    text: ''
                },
                labels:{
                    formatter: undefined
                }
            },
            plotOptions: {
                line: {
                    dataLabels: {
                        enabled: false
                    },
                    enableMouseTracking: true
                }
            },
            series: [],

            tooltip: {
                pointFormat: '{series.name}: <b>{point.y:.4f}</b><br/>',
                shared: true,

                formatter: function()
                {
                    if (this.points !== undefined)
                    {
                        let text = '';
                        if (this.points[0].key.length ==1 )
                        {
                            text = this.points[0].key[0];
                        }
                        else
                        {
                            text += this.points[0].key[1]; // date
                            text += ' ';
                            text += this.points[0].key[0]; // time
                        }

                        text += '<br>';


                        for(let i=0;i<this.points.length;i++)
                        {
                            text += this.points[i].series.name;
                            text += ': ';
                            text += '<b>';
                            text += this.points[i].y.toFixed(3);
                            text += '</b>';
                            text += '<br>';
                        }

                        return text;
                    }

                    return 'help';

                }
            }
        };

        return chart_defintion;

    }

    add_default_mesaage(parent_id, message)
    {
        let text = document.createElement('div');
            text.className = 'container';

            for(let i=0;i<5;i++)
            {
                let h1 = document.createElement('p');
                h1.className = 'text-center';
                text.appendChild(h1);
                h1.innerHTML = '<br>';
            }

            {
                let h1 = document.createElement('p');
                h1.className = 'text-center';
                text.appendChild(h1);
                h1.innerText = message;
            }

            for(let i=0;i<5;i++)
            {
                let h1 = document.createElement('p');
                h1.className = 'text-center';
                text.appendChild(h1);
                h1.innerHTML = '<br>';
            }

            document.getElementById(parent_id) .appendChild(text);
    }
}

class BasePageWidget  extends charting_base
{
    constructor()
    {
        super();

        //gareth -  these need to be unique as they hook into the html
        this.mode_select_label = 'anomalies_mode_select';
        this.mode_content_label = 'anomalies_mode_content';

        this.mode_select_options = {};
        this.my_root = undefined;
        this.current_mode = undefined;
    }

    build_ui()
    {
        //gareth -  update the current view
        this.onChangeMode(this.current_mode);
    }

    get_data_from_server()
    {
        /*
        let payload = {};
        payload['access_token'] = window.access_token;
        let cmd = 'get_alert_data';

        console.log(this.constructor.name);

        axios.get(cmd, {params: payload}).then(response =>
        {
            if (response.status === 200)
            {
                this.alert_table = response.data;
                this.build_ui();
            }
            else
            {
                alert_message(arguments,'failed to read data');
            }
        }).catch(function (error)
        {
            alert_message(arguments,'failed to read data: ' + error);
        });
         */
    }

    onChangeMode(mode_label)
    {
        {
            let container = document.getElementById(this.mode_content_label);

            if (container !== null)
            {
                container.remove();
            }
        }

        let container = document.createElement('div');
        container.id = this.mode_content_label;
        this.my_root.appendChild(container);
        //container.style.height = '100vh';
        //container.style.overflowY = 'scroll';


        //gareth -  ought to put these into a code container [name, object] to make this easier
        //          to work with

        this.current_mode = mode_label;

        this.mode_select_options[mode_label].onInit(container);
    }

    onInit(root)
    {
        super.onInit(root);

        let nav = document.createElement('nav');
        nav.className="nav nav-pills nav-justified mt-2";
        nav.id= this.mode_select_label;
        this.my_root.appendChild(nav);

        $(nav).hover(function ()
        {
            $(this).css('cursor', 'pointer');
        });

        //build nav options
        for (var key in this.mode_select_options)
        {
            let a = document.createElement('nav');
            a.className="nav-item nav-link active";
            a.id = key;
            a.href="#";
            a.innerHTML = a.id;

            if (false) //GARETH - do badges
            {
                let b = document.createElement('span');
                b.className = "badge badge-light ml-1";
                b.innerText = '10';
                b.id = a.id + '_span';
                a.appendChild(b);
            }

            let self = this;

            a.onclick = function()
            {
                self.mode_select(a.id);
            };

            nav.appendChild(a);
        }
        this.mode_select(this.current_mode);

        this.get_data_from_server();
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

        this.onChangeMode(option_label);
    }
}

class BaseContentWidget extends charting_base
{
    constructor()
    {
        super();
    }

    onInit(root)
    {
        this.my_root = root;
    }

    on_get_data(table_root, data)
    {

    }
}

class ScrollingContentWidget extends BaseContentWidget
{
    constructor()
    {
        super();
    }

    onInit(root)
    {
        super.onInit(root);
        this.my_root.style.height = '100vh';
        this.my_root.style.overflowY = 'scroll';
    }

    add_content_end_msg(table_root, msg)
    {
        let text = document.createElement('div');
        text.className = 'container';
        let h1 = document.createElement('p');
        h1.className = 'text-center';
        text.appendChild(h1);
        h1.innerText = msg;

        table_root.appendChild(text);

        return h1;
    }
}

class ScrollingTableContentWidget extends ScrollingContentWidget
{
    constructor()
    {
        super();
        this.columns = ['Date', 'Device ID', 'Property', 'Reason'];
        this.request_command = '';
        this.table = undefined;
    }

    get_table()
    {

    }

    build_headings(head)
    {
        let tr = document.createElement('tr');
        head.appendChild(tr);

        for (let i = 0; i < this.columns.length; i++)
        {
            let th = document.createElement('th');
            th.scope = 'col';
            th.innerText = this.columns[i];
            tr.appendChild(th);
        }
    }

    onInit(root)
    {
        super.onInit(root);

        let table_root = document.createElement('div');
        table_root.id = 'table_root';
        this.my_root.appendChild(table_root);

        this.table = document.createElement('table');
        this.table.className = 'table';

        table_root.appendChild(this.table);

        let head = document.createElement('thead');
        this.table.appendChild(head);

        let payload = {};
        payload['access_token'] = window.access_token;

        if (this.request_command !== '')
        {
            axios.get(this.request_command, {params: payload}).then(response =>
            {
                if (response.status === 200)
                {
                    let body = document.createElement('tbody');
                    this.table.appendChild(body);

                    //GARETH - force this ...
                    if ((response.data.length > 0) || (true))
                    {
                        this.build_headings(head);
                        this.on_get_data(table_root, response.data);

                        this.add_content_end_msg(table_root, 'End of list');
                    }
                    else
                    {
                        this.build_headings(head);
                        this.add_content_end_msg(table_root, 'No Devices are present 3');
                    }

                    this.add_gutter(table_root);
                }
                else
                {
                    this.build_headings(head);
                    this.add_content_end_msg(table_root, 'failed to read data');
                }
            }).catch(function (error)
            {
                this.add_content_end_msg(table_root, 'failed to read data: ' + error);
            });
        }
        else
        {
            //GARETH - force this ...
            let body = document.createElement('tbody');
            this.table.appendChild(body);
            this.build_headings(head);
            this.on_get_data(table_root, []);
            this.add_content_end_msg(table_root, 'End of list');
            this.add_gutter(table_root);
        }
    }

    on_get_data(table_root, data)
    {
        let body = document.createElement('tbody');
        this.table.appendChild(body);

        for (let index = 0; index < data.length; index++)
        {
            let tr = document.createElement('tr');
            body.appendChild(tr);

            for (let column_index =0;column_index < this.columns.length;column_index++)
            {
                let th = document.createElement('th');
                th.scope = 'row';
                th.innerHTML = data[index][this.data_labels[column_index]];
                tr.appendChild(th);
            }
        }
    }
}

class ScrollingGraphContentWidget extends ScrollingContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.cmd = 'get_anomaly_settings';
    }

    onInit(root)
    {
        this.my_root = root;
        //do this for scrollable content
        this.my_root.style.height = '100vh';
        this.my_root.style.overflowY = 'scroll';

        let payload = {};
        payload['access_token'] = window.access_token;

        axios.get(this.cmd, {params: payload}).then(response =>
        {
            if (response.status === 200)
            {
                if (response.data.length > 0)
                {
                    this.add_graphs(this.my_root, response.data.length, 2);
                }
                this.populate_graphs(response.data);

                this.add_gutter(this.my_root);
            }
            else
            {
                alert_message(arguments,'Can\'t load data from server');
                return;
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

    populate_graphs(chart_data)
    {
        if (chart_data.length > 0)
        {
            let chart_defintion = this.get_chart_definition();

            for (let chart_index = 0; chart_index < chart_data.length; chart_index++)
            {
                let current_chart = chart_data[chart_index];

                chart_defintion.series = current_chart['series'];
                chart_defintion.xAxis.categories = current_chart['xaxis-labels'];

                if ('tick_interval' in current_chart)
                {
                    chart_defintion.xAxis.tickInterval = current_chart['tick_interval'];
                }
                else
                {
                    chart_defintion.xAxis.tickInterval = 1;
                }

                chart_defintion.chart.type = 'line';
                chart_defintion.title.text = current_chart['graph_title'];// + ' ' + chart_index.toString();
                chart_defintion.subtitle.text = current_chart['graph_subtitle'];
                chart_defintion.yAxis.title.text = current_chart['prop_units'];

                if ('y_plotlines' in current_chart)
                {
                    chart_defintion.yAxis.plotLines = current_chart['y_plotlines'];
                }

                if ('graph_range' in current_chart)
                    chart_defintion.yAxis.min = current_chart['graph_range']['min'];
                    chart_defintion.yAxis.max = current_chart['graph_range']['max'];

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
        else
        {
            let text = document.createElement('div');
            text.className = 'container';

            for(let i=0;i<5;i++)
            {
                let h1 = document.createElement('p');
                h1.className = 'text-center';
                text.appendChild(h1);
                h1.innerHTML = '<br>';
            }

            {
                let h1 = document.createElement('p');
                h1.className = 'text-center';
                text.appendChild(h1);
                h1.innerText = 'No Devices are present 5';
            }

            for(let i=0;i<5;i++)
            {
                let h1 = document.createElement('p');
                h1.className = 'text-center';
                text.appendChild(h1);
                h1.innerHTML = '<br>';
            }

            document.getElementById('anomalies_mode_content') .appendChild(text);
        }
    }
}
