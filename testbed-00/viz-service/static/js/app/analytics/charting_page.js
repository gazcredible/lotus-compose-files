class ChartingPage extends charting_base
{
    constructor()
    {
        super();

        this.mode_select_label = 'charting_mode_select';
        this.mode_select_options = ['Properties by Sensor','Sensors by Property'];
        this.mode_content_label = 'charting_mode_content';

        this.prop_by_sensor = new charting_prop_by_sensor();
        this.sensor_by_prop = new charting_sensor_by_prop();
        this.my_root = undefined;

    }

    onInit(root)
    {
        this.my_root = root;

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
            super.onInit(root);

            let nav = document.createElement('nav');
            nav.className="nav nav-pills nav-justified";
            nav.id= this.mode_select_label;
            root.appendChild(nav);

             $(nav).hover(function ()
            {
                $(this).css('cursor', 'pointer');
            });

             this.prop_by_sensor.time_options = response.data['analytics_time_labels'];
             this.sensor_by_prop.time_options = response.data['analytics_time_labels'];


            for (let i = 0; i < this.mode_select_options.length; i++)
            {
                let a = document.createElement('nav');
                a.className="nav-item nav-link active";
                a.id = this.mode_select_options[i];
                a.href="#";
                a.innerHTML = a.id;

                let self = this;

                a.onclick= function()
                {
                    self.mode_select(a.id);
                };

                nav.appendChild(a);
            }

            this.mode_select(this.mode_select_options[0]);
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

        //do something this active thing
        {
            let container = document.getElementById(this.mode_content_label);

            if(container !== null)
            {
                container.remove();
            }
        }

        let container = document.createElement('div');
        container.id = this.mode_content_label;
        this.my_root.appendChild(container);

        if(option_label == this.mode_select_options[0])
        {
            this.prop_by_sensor.onInit(container);
        }

        if(option_label == this.mode_select_options[1])
        {
            this.sensor_by_prop.onInit(container);
        }
    }

    graph_label(label)
    {
        if(label.includes('<br>'))
        {
            return label.split('>').pop();
        }

        return label;
    }
}