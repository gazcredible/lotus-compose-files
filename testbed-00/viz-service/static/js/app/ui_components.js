/*jshint -W069*/
/*jshint -W080*/
/*jshint -W104*/
/*jshint -W117*/
/* jshint strict: false */
/*jshint esversion: 6*/

function get_by_id(root, required_id)
{
    if (root !== null)
    {
        if(root.id === required_id)
        {
            return root;
        }

        let elements = root.childNodes;

        //console.log('id:'+ root.id + ' n:' + root.name + ' c:'+elements.length);

        for (let i = 0; i < elements.length; i++)
        {
            let result = get_by_id(elements[i], required_id);

            if (result !== null)
            {
                return result;
            }
        }
    }

    return null;
}

//--------------------------------------------------------------------------------------------------------------
function add_button(id, text, buttonClassName, onclick_event)
{
    let button = document.createElement('button');
    button.type = "button";
    button.className = buttonClassName;

    //button.style = "font: bold 12px/20px 'Helvetica Neue', Arial, Helvetica, sans-serif;";
    button.innerHTML = text;
    button.id = id;
    button.onclick = function ()
    {
        onclick_event(button.id, {});
    };

    return button;
}

//--------------------------------------------------------------------------------------------------------------
function add_label(id, text)
{
    let label = document.createElement('label');
    label.id = id;
    label.innerHTML = text;
    return label;
}

/*
Add a dropdown to the html scene
 */
function add_dropdown(id, name,items, onclick_event)
{
    //if(document.getElementById(name) === null)
    {
        let group = document.createElement('div');
        group.className = 'dropdown';
        group.id= id;

        let button = document.createElement('button');
        button.className = "btn btn-secondary dropdown-toggle";
        button.type="button";
        button.text = name;
        //button.value = button.text
        button.textContent = button.text;
        button.id= id.toLowerCase()+'_button';
        button.setAttribute("data-toggle", "dropdown");

        group.appendChild(button);

        let menu = document.createElement('div');
        menu.className = "dropdown-menu";
        menu.id = id.toLowerCase()+'_menu';
        menu.name = menu.id;
        
        menu.setAttribute("aria-labelledby","new_dropdown");
        button.appendChild(menu);

        for(let i=0;i<items.length;i++)
        {
            let opt = document.createElement('a');
            opt.className = "dropdown-item";
            opt.href = '#';

            if (typeof items[i] === 'string')
            {
                opt.text = items[i];
                opt.id = id.toLowerCase()+'_'+i;

                opt.onclick = function()
                {
                    onclick_event(id, {'id':opt.id, 'text':opt.text});
                };

            }
            else
            {
                if ('text' in items[i])
                {
                    opt.text = items[i].text;
                    opt.value = opt.text;
                }
                else
                {
                    opt.text = items[i];
                }

                if ('id' in items[i])
                {
                    opt.id = items[i].id;
                }

                if ('onclick' in items[i])
                {
                    opt.onclick = items[i].onclick;
                }
            }

            menu.appendChild(opt);
        }

        return group;
    }
}

function dropdown_set_active(component, option_label)
{
    let elements = component.getElementsByClassName("dropdown-item");

    for(let i=0;i< elements.length;i++)
    {
        if(elements[i].id == option_label)
        {
            elements[i].className = "dropdown-item active";
        }
        else
        {
            elements[i].className = "dropdown-item";
        }
    }
}

function dropdown_toggle_active(component, option_label)
{
    let elements = component.getElementsByClassName("dropdown-item");

    for(let i=0;i< elements.length;i++)
    {
        if(elements[i].id == option_label)
        {
            if(elements[i].className == "dropdown-item active")
            {
                elements[i].className = "dropdown-item";
            }
            else
            {
                elements[i].className = "dropdown-item active";
            }
        }
    }
}

function dropdown_get_state(component, option_label)
{
    let elements = component.getElementsByClassName("dropdown-item");

    for(let i=0;i< elements.length;i++)
    {
        if(elements[i].id == option_label)
        {
            if(elements[i].className === "dropdown-item active")
            {
                return true;
            }
            else
            {
                return false;
            }
        }
    }

    return false;
}

function dropdown_set_active_state(component, option_label, active)
{
    let elements = component.getElementsByClassName("dropdown-item");

    for(let i=0;i< elements.length;i++)
    {
        if(elements[i].id == option_label)
        {
            if(active === true)
            {
                elements[i].className = "dropdown-item active";
            }
            else
            {
                elements[i].className = "dropdown-item";
            }
        }
    }
}



/*
create a select dropdown listbox thing

don't add to scene
 */
function create_select_option(name, values)
{
    let select = document.createElement('select');
    select.name = name;
    select.className = 'form-control w-25';
    select.id = select.name;

    for (let i=0; i < values.length;i++)
    {
        let opt = document.createElement("option");
        opt.text = values[i];
        opt.value = opt.text;
        select.options.add(opt);
    }

    return select;
}

function create_pils(name, values)
{
    let pils = document.createElement('ul');
    pils.name = name;
    pils.className = 'nav nav-pills nav-fill';
    pils.id = pils.name;

    for (let i=0; i < values.length;i++)
    {
        let item = document.createElement("li");
        item.className = "nav-item";

        pils.appendChild(item);

        let opt = document.createElement("a");

        opt.className = "nav-link";
        opt.text = values[i].text;
        opt.value = values[i].label;
        //opt.href = "#";

        if('onclick' in values[i])
        {
            opt.onclick = values[i].onclick;
        }

        item.appendChild(opt);
    }

    return pils;
}



class Pils
{
    constructor(pil_id, labels, onNewSelection)
    {
        this.pil_id = pil_id;
        this.labels = labels.slice();
        this.selected_item = '';

        this.onNewSelectionHandler = onNewSelection;
    }

    createHTML()
    {
        let nav = document.createElement('nav');
        nav.className="nav nav-pills nav-justified";
        nav.id = this.pil_id;

        let obj = this;

        for(let i=0;i< this.labels.length;i++)
        {
            let a = document.createElement('a');
            a.className="nav-item nav-link";
            a.innerHTML = this.labels[i];
            a.id = this.labels[i];
            a.href='#';
            //a.onclick = function(){obj.onclickHandler(a.id);};
            nav.appendChild(a);
        }

        return nav;
    }

    onclickHandler(item_id)
    {
        return;
        this.updateState(item_id);
        this.onNewSelection(item_id);
    }

    onNewSelection(item_id)
    {
        //do code here ...
        this.selected_item = item_id;

        if(this.onNewSelectionHandler !== undefined)
        {
            this.onNewSelectionHandler(this, item_id);
        }
    }

    updateState(item_id)
    {
        try
        {
            let elements = document.getElementById(this.pil_id);

            if (elements !== null)
            {
                elements = elements.childNodes;

                for (let i = 0; i < elements.length; i++)
                {
                    if (elements[i].id === item_id)
                    {
                        elements[i].className = "nav-item nav-link active";
                    }
                    else
                    {
                        elements[i].className = "nav-item nav-link";
                    }
                }
            }
        }catch (e)
        {
            alert_message(arguments,e);
        }

        this.selected_item = item_id;
    }


}