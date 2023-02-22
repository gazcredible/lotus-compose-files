class AlertsScreen extends charting_base
{
    constructor(access_token)
    {
        super();

        window.access_token = access_token;

        this.mode_select_label = 'analytics_screen_mode_select';
        this.mode_content_label = 'analytics_screen_mode_content';

        this.mode_lookup = {};
    }

    onInit(root)
    {
        this.my_root = document.createElement('div');
        this.my_root.id = 'AlertsScreen';
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

            this.mode_lookup = {};
            this.mode_lookup['Alerts'] = {'mode': new AlertsPage()};
            this.mode_lookup['Anomalies'] = {'mode': new AnomaliesPage()};

            if(('has_epanet_anomalies' in  response.data) && (response.data['has_epanet_anomalies']===true))
            {
                this.mode_lookup['EPANET Anomalies'] ={'mode': new EPANETAnomaliesPage()};
            }


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
                    window.alertscreen.mode_select(a.id);
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

//---------------------------------------------------------------------------------------
class SetAlerts extends ScrollingTableContentWidget
{
    constructor(whatever)
    {
        super();
        this.columns = ['Device ID', 'Property', 'Alert Min', 'Alert Max', 'Active'];
        this.request_command = 'get_alert_data';

    }

    on_get_data(table_root, data)
    {
        if ((data !== undefined) && (data.length>0))
        {
            let body = document.createElement('tbody');
            this.table.appendChild(body);

            for (let index = 0; index < data.length; index++)
            {
                let current_alert = data[index];

                let tr = document.createElement('tr');
                body.appendChild(tr);

                //device id
                let th = document.createElement('th');
                th.scope = 'row';
                th.innerHTML = current_alert['device_name'];
                tr.appendChild(th);

                //property
                let td = document.createElement('td');
                td.innerHTML = current_alert['property_print_name'];
                tr.appendChild(td);

                //min value
                {
                    td = document.createElement('td');
                    let input = document.createElement('input');
                    td.appendChild(input);
                    input.className = "form-control w-50";
                    input.setAttribute('type', 'number');

                    input.setAttribute('min', current_alert['min'].toString());
                    input.setAttribute('max', current_alert['max'].toString());
                    input.setAttribute('step', current_alert['step'].toString());
                    input.value = current_alert['current_min'];

                    tr.appendChild(td);

                    let self = this;

                    input.onchange = function ()
                    {
                        self.alert_on_minvalue_change(current_alert, input.value);
                    };
                }

                //max value
                {
                    td = document.createElement('td');
                    let input = document.createElement('input');
                    td.appendChild(input);
                    input.className = "form-control w-50";
                    input.setAttribute('type', 'number');

                    input.setAttribute('min', current_alert['min'].toString());
                    input.setAttribute('max', current_alert['max'].toString());
                    input.setAttribute('step', current_alert['step'].toString());
                    input.value = current_alert['current_max'];


                    let self = this;

                    input.onchange = function ()
                    {
                        self.alert_on_maxvalue_change(current_alert, input.value);
                    };

                    tr.appendChild(td);
                }

                //active tickbox
                {
                    td = document.createElement('td');
                    let div = document.createElement('div');
                    td.appendChild(div);

                    div.className = 'form-check';
                    //div.className = "custom-control custom-switch";

                    let input = document.createElement('input');
                    div.appendChild(input);
                    input.className = "form-check-input";
                    //input.className = "custom-control-input";
                    input.setAttribute('type', 'checkbox');
                    input.checked = current_alert['active'];

                    let self = this;

                    input.onchange = function ()
                    {
                        self.alert_on_tickboxchange(current_alert, input.checked);
                    };

                    tr.appendChild(td);
                }
            }
        }
        else
        {
            self.add_content_end_msg(table_root,'No Devices are present..');
            return;
        }
    }

    alert_send_post_request(item)
    {
        let cmd = 'set_alert';

        let data = {};
        data['access_token'] = window.access_token;
        data['item'] = item;
        axios.post(cmd, data);
    }

    alert_on_minvalue_change(item, value)
    {
        item['current_min'] = value;

        this.alert_send_post_request(item);
    }

    alert_on_maxvalue_change(item, value)
    {
        item['current_max'] = value;
        this.alert_send_post_request(item);
    }

    alert_on_tickboxchange(item, value)
    {
        item['active'] = value;
        this.alert_send_post_request(item);
    }
}

class ViewAlerts extends ScrollingTableContentWidget
{
    constructor()
    {
        super();
        this.columns = ['Date', 'Device ID', 'Property', 'Reason'];
        this.data_labels = ['time', 'device_name','property_print_name','alert_reason'];
        this.request_command = 'get_alert_data';
    }

    get_active_alert_count(data)
    {
        let active_count = 0;

        if (data !== undefined)
        {
            for (let index = 0; index < data.length; index++)
            {
                if (data[index]['active'])
                {
                    active_count = active_count + 1;
                }
            }
        }

        return active_count;
    }

    get_triggered_alert_count(data)
    {
        let active_count = 0;

        if (data !== undefined)
        {
            for (let index = 0; index < data.length; index++)
            {
                if (data[index]['triggered'])
                {
                    active_count = active_count + 1;
                }
            }
        }

        return active_count;

    }

    on_get_data(table_root, data)
    {
        //add some content for testing ...
        /*
        for (let i=0;i<10;i++)
        {
            data.push({date: i, device_id: 'device_wibble_:'+i, property:'prop'+i, value: i+' l/s'});
        }*/

        if ((this.get_active_alert_count(data) > 0 ) && (this.get_triggered_alert_count(data) > 0) )
        {
            let body = document.createElement('tbody');
            this.table.appendChild(body);

            for (let index = 0; index < data.length; index++)
            {
                if (data[index]['triggered'])
                {
                    let tr = document.createElement('tr');
                    body.appendChild(tr);

                    for (let column_index = 0; column_index < this.columns.length; column_index++)
                    {
                        let th = document.createElement('th');
                        th.scope = 'row';
                        th.innerHTML = data[index][this.data_labels[column_index]];
                        tr.appendChild(th);
                    }
                }
            }
        }
        else
        {
            if (this.get_active_alert_count(data) === 0)
            {
                this.add_content_end_msg(table_root, 'No alerts have been set');
                return;
            }

            if (this.get_triggered_alert_count(data) === 0)
            {
                this.add_content_end_msg(table_root, 'No alerts have been triggered');
                return;
            }
        }
    }
}

class AlertPage extends BasePageWidget
{
    constructor()
    {
        super();

        this.mode_select_options = {};
        this.mode_select_options['Set Alerts']  = new SetAlerts(this);
        this.mode_select_options['Current Alerts']  = new ViewAlerts(this);
        //this.mode_select_options['Historic Alerts']  = new HistoricAlerts(this);

        this.current_mode = Object.keys(this.mode_select_options)[0];

        this.mode_select_label = this.constructor.name + '_select';
        this.mode_content_label = this.constructor.name + '_content';
    }
}

class AnomalySettings extends ScrollingGraphContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.anomaly_object = anomaly_object;
        this.cmd = 'get_anomaly_settings';
    }

    onInit(root)
    {
        this.cmd = 'get_anomaly_settings';
        super.onInit(root);
    }
}

class AnomalyRanges extends ScrollingTableContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.columns = ['Device', 'Property', 'Lower', 'Upper'];
        this.data_labels = ['print_name', 'property','lower_limit','upper_limit'];

        this.request_command = 'get_anomaly_ranges';
    }
}

class CurrentAnomalies extends ScrollingTableContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.columns = ['Time', 'Device', 'Property', 'Reason'];
        this.data_labels = ['time', 'print_name', 'property','reason'];

        this.request_command = 'get_current_anomalies';
    }
}

class HistoricAnomalies extends ScrollingTableContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.columns = ['Time', 'Device', 'Property', 'Reason'];
        this.data_labels = ['time', 'print_name', 'property','reason'];

        this.request_command = '';
    }
}

class AnomalyPage extends BasePageWidget
{
    constructor()
    {
        super();

        this.mode_select_options = {};
        this.mode_select_options['Anomaly Ranges']      = new AnomalyRanges(this);
        this.mode_select_options['Current Anomalies']   = new CurrentAnomalies(this);
        this.mode_select_options['Historic Anomalies']  = new HistoricAnomalies(this);
        this.mode_select_options['Anomaly Settings']    = new AnomalySettings(this);

        this.current_mode = Object.keys(this.mode_select_options)[0];

        this.mode_select_label = this.constructor.name + '_select';
        this.mode_content_label = this.constructor.name + '_content';
    }
}

class EPANETAnomalyRanges extends ScrollingTableContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.columns = ['Device', 'Property', 'Lower', 'Upper'];
        this.data_labels = ['print_name', 'property','lower_limit','upper_limit'];

        this.request_command = 'get_anomaly_ranges';
    }
}

class CurrentEPANETAnomalies extends ScrollingTableContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.columns = ['Time', 'Device', 'Property', 'Reason'];
        this.data_labels = ['time', 'print_name', 'property','reason'];

        this.request_command = 'get_current_epanetanomalies';
    }
}

class EPAnomaliesurrentReadings extends ScrollingTableContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.columns = ['Date', 'Device', 'Property', 'Value'];
        this.data_labels = ['time', 'device_name','property_print_name','current_print_value'];

        this.request_command = 'get_current_epanomaly_readings';
    }
}

class HistoricEPANETAnomalies extends BaseContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.request_command = 'get_historic_epanetanomalies';
    }
}

class EPANETAnomalySettings extends ScrollingGraphContentWidget
{
    constructor(anomaly_object)
    {
        super();
        this.anomaly_object = anomaly_object;
        this.cmd = 'get_anomaly_settings';
    }

    onInit(root)
    {
        this.cmd = 'get_epanomaly_settings';
        super.onInit(root);
        return;
    }

}

class EPAnomalyPage extends BasePageWidget
{
    constructor()
    {
        super();

        this.mode_select_options = {};
        this.mode_select_options['Current Readings']      = new EPAnomaliesurrentReadings(this);
        this.mode_select_options['Current Anomalies']   = new CurrentEPANETAnomalies(this);
        //this.mode_select_options['Historic Anomalies']  = new HistoricEPANETAnomalies(this);
        this.mode_select_options['Anomaly Settings']    = new EPANETAnomalySettings(this);

        this.current_mode = Object.keys(this.mode_select_options)[0];

        this.mode_select_label = this.constructor.name + '_select';
        this.mode_content_label = this.constructor.name + '_content';
    }
}

class GiotaPage extends ScrollingTableContentWidget
{
    constructor(entity_type, columns)
    {
        super();

        this.columns = ['Date', 'Satellite ID', 'Property', 'Reason'];

        if (columns !== undefined)
            this.columns = columns;

        this.data_labels = ['timestamp', 'source_id','property','reason'];
        this.request_command = 'get_certh_alert_data';

        this.entity_type = entity_type;
    }

    on_get_data(table_root, data)
    {
        let body = document.createElement('tbody');
        this.table.appendChild(body);

        let entity_list = data;
        if (this.entity_type !== '' && this.entity_type in entity_list['alerts'])
        {
            entity_list = data['alerts'][this.entity_type];
        }

        for (let index = 0; index < entity_list.length; index++)
        {
            let tr = document.createElement('tr');
            body.appendChild(tr);

            for (let column_index =0;column_index < this.columns.length;column_index++)
            {
                let th = document.createElement('th');
                th.scope = 'row';
                th.innerHTML = entity_list[index][this.data_labels[column_index]];
                tr.appendChild(th);
            }
        }
    }
}

class DeviceStatusPage extends ScrollingTableContentWidget
{
    constructor()
    {
        super();
        this.columns = ['Date', 'Device ID', 'Property', 'Value'];
        this.data_labels = ['current_prop_reading', 'device_id','property_print_name','current_print_value'];
        this.request_command = 'get_alert_data';
    }
}


class DevicesPage extends BasePageWidget
{
    constructor(pilot_data)
    {
        super();

        this.request_command = '';

        this.mode_select_options = {};
        this.mode_select_options['Current Readings']  = new DeviceStatusPage(this);
        //this.mode_select_options['Alerts']  = new AlertPage(this);
        //this.mode_select_options['Anomalies']  = new AnomalyPage(this);

        if (('epanomalies' in pilot_data) && (pilot_data['epanomalies'] === 'true'))
        {
            this.mode_select_options['EPAnomalies'] = new EPAnomalyPage(this);
        }

        this.current_mode = Object.keys(this.mode_select_options)[0];
        this.mode_select_label = this.constructor.name + '_select';
        this.mode_content_label = this.constructor.name + '_content';
    }
}

class ALertPacketPage extends ScrollingContentWidget
{
    constructor()
    {
        super();
        this.request_command = 'get_giota_data';
    }

    onInit(root)
    {
        super.onInit(root);

        let payload = {};
        payload['access_token'] = window.access_token;

        if (this.request_command !== '')
        {
            axios.get(this.request_command, {params: payload}).then(response =>
            {
                if (response.status === 200)
                {
                    //GARETH - force this ...
                    if ((response.data.length > 0) || (true))
                    {
                        //do stuff here!
                        let text = "<div class='row'><div class='col-1'></div><div class='col-10'><pre>" + JSON.stringify(response.data, null,2) +"</pre></div><div class='col-1'></div></div>";


                        this.my_root.innerHTML = text;

                    }
                    else
                    {
                        this.add_content_end_msg(this.my_root, 'No Devices are present 3');
                    }

                    this.add_gutter(this.my_root);
                }
                else
                {
                    this.add_content_end_msg(this.my_root, 'failed to read data');
                }
            }).catch(function (error)
            {
                this.add_content_end_msg(this.my_root, 'failed to read data: ' + error);
            });
        }
        else
        {
            this.add_content_end_msg(this.my_root, 'No command to process');
        }
    }
}


class AlertPage2 extends BasePageWidget
{
    constructor(access_token,pilot_data)
    {
        super();

        window.access_token = access_token;



        this.mode_select_options = {};
        this.mode_select_options['Devices']  = new DevicesPage(pilot_data);

        if (('satellite' in pilot_data) && (pilot_data['satellite'] === 'true'))
        {
            this.mode_select_options['Satellites'] = new GiotaPage('satellite', ['Date', 'Satellite ID', 'Property', 'Reason']);
        }
        if (('social_media' in pilot_data) && (pilot_data['social_media'] === 'true'))
        {
            this.mode_select_options['Social Media'] = new GiotaPage('social_media', ['Date', 'SM ID', 'Property', 'Reason']);
        }

        if (('cctv' in pilot_data) && (pilot_data['cctv'] === 'true'))
        {
            //this.mode_select_options['CCTV'] = new GiotaPage('cctv', ['Date', 'CCTV ID', 'Property', 'Reason']);
            this.mode_select_options['CCTV'] = new GiotaPage('cctv', ['Date', 'CCTV ID', 'Property']);
        }

        if (('drones' in pilot_data) && (pilot_data['drones'] === 'true'))
        {
            //this.mode_select_options['Drone'] = new GiotaPage('drone', ['Date', 'Drone ID', 'Property', 'Reason']);
            this.mode_select_options['Drone'] = new GiotaPage('drone', ['Date', 'Drone ID', 'Property']);
        }

        if (false)
        {
            this.mode_select_options['Giota'] = new ALertPacketPage(this);
        }

        this.my_root = undefined;
        this.current_mode = Object.keys(this.mode_select_options)[0];

        //gareth -  these need to be unique as they hook into the html
        this.mode_select_label = this.constructor.name + '_select';
        this.mode_content_label = this.constructor.name + '_content';
    }
}


function alerts_initialise(access_token, pilot_data)
{
    //window.alertscreen = new AlertsScreen(access_token);

    window.alertscreen = new AlertPage2(access_token,pilot_data);

    window.alertscreen.onInit(document.body);
}