/*jshint -W069*/
/*jshint -W080*/
/*jshint -W104*/
/*jshint -W117*/
/* jshint strict: false */
/*jshint esversion: 6*/

let container = undefined;

class mapviewui
{
    constructor()
    {
        this.uishared_hover_popup = undefined;
        this.uishared_enable_hover_popup = false;

        this.container = undefined;
        this.defaultStyle = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
    }

    init()
    {
        this.container = document.createElement('div');
        this.container.id = 'root';
        this.container.style = "position: absolute; top: 0; bottom: 0; width: 100%";
        document.body.appendChild(this.container);

        let map_container = document.createElement('div');
        map_container.id = 'map';
        map_container.style = "position: absolute; top: 0; bottom: 0; width: 100%";

        this.container.appendChild(map_container);

        this.isOpen=false;
    }



    toggleNav()
    {
        if (this.isOpen === false)
        {
            document.getElementById("mySidenav").style.width = "33%";
            document.getElementById("toggleButton").style.marginLeft = "33%";

            this.isOpen = true;
        }
        else
        {
            document.getElementById("mySidenav").style.width = "0";
            document.getElementById("toggleButton").style.marginLeft= "0";
            this.isOpen = false;
        }
    }


    build()
    {
        this.uishared_hover_popup = new maplibregl.Popup({
            offset: 25,
            maxWidth: 400,
            closeButton: false,
            closeOnClick: false
        });

        this.uishared_hover_popup.addTo(window.mapview.map);

        let toggleButton = document.createElement('div');
        toggleButton.id = 'toggleButton';
        toggleButton.style = 'position: absolute;  top: 0; left: 0; padding: 10px; transition: 0.5s;';

        let hamburger = document.createElement('span');
        toggleButton.appendChild(hamburger);

        let self = this;
        hamburger.onclick = function(){self.toggleNav();};

        hamburger.textContent = '☰';
        hamburger.style="font-size:30px;cursor:pointer;";

        document.body.appendChild(toggleButton);


        let menu = document.createElement('div');
        menu.className="sidenav top";
        menu.id = "mySidenav";

        //menu.style="position: absolute; width: 33%; top: 0; left: 0; padding: 10px; font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";

        menu.style= "height: 100%; width: 0; position: fixed; z-index: 1; top: 0; left: 0; background-color: #ffffff; overflow-x: hidden; transition: 0.5s;padding-top: 0px;";

        this.container.appendChild(menu);

        let menu_inner = document.createElement('div');
        menu_inner.className="map-overlay-inner";
        menu_inner.style=" background-color: #fff; box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2); border-radius: 3px; padding: 10px";
        menu.appendChild(menu_inner);

        {
            let label = document.createElement('label');
            label.style="font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
            label.innerHTML = 'Control';
            menu_inner.appendChild(label);
        }


        this.menu_slidy_content = document.createElement('div');

        this.menu_slidy_content.className="container-fluid";
        this.menu_slidy_content.style="height: 85vh; overflow-y: scroll;";
        this.menu_slidy_content.id = 'menu_slidy_content';
        menu_inner.appendChild(this.menu_slidy_content);

        //add mapstyle
        try
        {
            {
                let label = document.createElement('label');
                label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                label.innerHTML = 'Map Mode';
                this.menu_slidy_content.appendChild(label);
            }

            let div = document.createElement('div');
            div.className="d-flex justify-content-center";
            this.menu_slidy_content.appendChild(div);

            let button_data = [{id: 'Street View', print_text: 'Street View'},
                               {id: 'Satellite', print_text: 'Satellite'}];

            let id = 'mapmode_group';
            let div2 = this.add_button_group(this, id, button_data);
            div.appendChild(div2);

            this.on_button_press(id,button_data[0]['id'],"btn btn-primary");
        }
        catch (err)
        {
            alert_message(arguments,err);
        }

        //add device properties
        try
        {
            {
                let label = document.createElement('label');
                label.style="font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                label.innerHTML = '<br>Device / Property Views';
                this.menu_slidy_content.appendChild(label);
            }

            let div = document.createElement('div');
            div.className="d-flex justify-content-center";
            this.menu_slidy_content.appendChild(div);

            if(('controlled_properties' in window.mapview.pilot_data) && (window.mapview.pilot_data['controlled_properties'].length > 0))
            {
                let button_data = [];

                for (let i = 0; i < window.mapview.pilot_data['controlled_properties'].length; i++)
                {
                    let record = {};
                    record['id'] = window.mapview.pilot_data['controlled_properties'][i]['label'];
                    record['print_text'] = window.mapview.pilot_data['controlled_properties'][i]['print_label'];

                    button_data.push(record);
                }

                let id = 'controlled_properties_button_group';
                let div2 = this.add_vertical_button_group(this, id, button_data);
                div.appendChild(div2);

                this.on_button_press(id,button_data[0]['id'],"btn btn-primary");

            }
            else
            {
                let div = document.createElement('div');
                div.className = "d-flex justify-content-center";
                this.menu_slidy_content.appendChild(div);

                let label = document.createElement('label');
                label.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
                label.innerHTML = 'No Device Data avaliable';div.appendChild(label);

            }
        }
        catch(err)
        {
            alert_message(arguments,err);
        }
    }

    add_button_group(parent, div_id, button_names, buttonClassName ="btn btn-primary")
    {
        let div2 = document.createElement('div');
        div2.className = "btn-group";
        div2.id = div_id;
        for (let i = 0; i < button_names.length; i++)
        {
            let button = document.createElement('button');
            button.type = "button";
            button.className = buttonClassName;

            button.style = this.defaultStyle;
            button.innerHTML = button_names[i]['print_text'];
            button.id = button_names[i]['id'];
            button.onclick = function ()
            {
                parent.on_button_press(div_id, button.id, buttonClassName);
            };
            div2.appendChild(button);
        }

        return div2;
    }

    add_vertical_button_group(parent, div_id, button_names, buttonClassName ="btn btn-primary")
    {
        let div2 = document.createElement('div');
        div2.className = "btn-group-vertical";
        div2.id = div_id;
        for (let i = 0; i < button_names.length; i++)
        {
            let button = document.createElement('button');
            button.type = "button";
            button.className = buttonClassName;
            button.style = this.defaultStyle;
            button.innerHTML = button_names[i]['print_text'];
            button.id = button_names[i]['id'];
            button.onclick = function ()
            {
                parent.on_button_press(div_id, button.id, buttonClassName);
            };
            div2.appendChild(button);
        }

        return div2;
    }

    on_button_press(div_id, selected_id, classname)
    {
        if(div_id === 'controlled_properties_button_group')
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

            //do something here with the property
            window.mapview.update_devices_by_property(selected_id);
            return;
        }

        if(div_id === 'mapmode_group')
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

            window.mapview.set_mapstyle(selected_id);
            return;
        }
    }
}

function set_marker_colour(marker, color)
{
    let $elem = jQuery(marker.getElement());
    $elem.find('svg g[fill="' + marker._color + '"]').attr('fill', color);
    marker._color = color;
}
