class IMMScreen extends charting_base
{
    constructor(access_token)
    {
        super();

        window.access_token = access_token;

        this.mode_select_label = 'analytics_screen_mode_select';
        this.mode_select_options = ['Charting'];
        this.mode_content_label = 'analytics_screen_mode_content';

        this.mode_lookup = {};
        this.mode_lookup['IMM'] = {'mode': new IMMPage()};
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


function imm_initialise(access_token)
{
    window.imm = new IMMScreen(access_token);
    window.imm.onInit();
}