// this will be the basic class that handles a layer in the map visualisation scheme of our choice
class map_layer
{
    constructor(layer_name)
    {
        this.isvisible = false;
        this.map = window.mapview.map;
        this.layer_name = layer_name;
        this.data = undefined;

        //get layer_name passed into leave function so we can work out what's going on
        let self = this;
        this.actual_on_mouse_leave_function = function(e)
        {
            self.onMouseLeave(e, self);
        };
    }

    load_data(data)
    {
        this.data = data;
    }

    set_visible(visible)
    {
        if(visible === undefined)
        {
            this.isvisible = !this.isvisible;
        }
        else
        {
            this.isvisible = visible;
        }

        if(this.data !== undefined)
        {
            if(this.is_layer_in_map() === true)
            {
                if (this.isvisible === true)
                {
                    window.mapview.map.setLayoutProperty(this.layer_name, 'visibility', 'visible');
                }
                else
                {
                    window.mapview.map.setLayoutProperty(this.layer_name, 'visibility', 'none');
                }
            }
        }
    }

    is_layer_in_map()
    {
        let layers = window.mapview.map.getStyle().layers;

        for(let i=0;i<layers.length;i++)
        {
            if (layers[i]['id'] === this.layer_name)
            {
                return true;
            }
        }

        return false;
    }

    //override this for each layer type
    load_data_into_layer()
    {
    }

    //:) - make layer listeners work nice
    isListener()
    {
        if(window.mapview.map._delegatedListeners === undefined)
        {
            return false;
        }

        for(let i=0; i <window.mapview.map._delegatedListeners.mouseenter.length;i++)
        {
            if (window.mapview.map._delegatedListeners.mouseenter[i].layer == this.layer_name)
            {
                return true;
            }
        }

        return false;
    }

    on_styleload()
    {
        if ((window.mapview.map !== undefined) && (this.layer_name != undefined) && (this.data !== undefined))
        {
            this.load_data_into_layer();

            if(this.isListener() == false)
            {
                window.mapview.map.on('mouseenter', this.layer_name, this.onMouseEnter);
                window.mapview.map.on('mouseleave', this.layer_name, this.actual_on_mouse_leave_function);
                window.mapview.map.on('click', this.layer_name, this.onClick);
            }
        }
    }

    onMouseEnter(e)
    {
        if(window.mapview.map !== undefined)
        {
            window.mapview.map.getCanvas().style.cursor = 'pointer';
        }
        if (e.features[0]['properties']['index'] !== -1)
        {
            window.mapview.add_to_layer_popup(e.features[0]['layer']['id'], e.features[0]['properties']['index'], e.lngLat);
        }
        else
        {
            window.mapview.add_to_layer_popup(e.features[0]['layer']['id'], 'No Sim Data', e.lngLat);
        }

    }

    onMouseLeave(e,self)
    {
        if(window.mapview.map !== undefined)
        {
            window.mapview.map.getCanvas().style.cursor = '';
        }

        window.mapview.remove_from_layer_popup(self.layer_name);
    }

    onClick(e)
    {
        if(window.mapview.map !== undefined)
        {
            window.mapview.map.getCanvas().style.cursor = 'pointer';
        }

        window.mapview.add_to_layer_popup(e.features[0]['layer']['id'], e.features[0]['properties']['index'],e.lngLat);
    }
}