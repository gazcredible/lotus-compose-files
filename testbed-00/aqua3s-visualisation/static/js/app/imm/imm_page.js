
class IMMMode extends component_base
{
    constructor()
    {
        super();
    }

    onInit(container, data)
    {

    }

    handle_ui_event(id, data)
    {
        console.log(id + ' ' + JSON.stringify(data));
    }
}

class IdleMode extends IMMMode
{
    constructor()
    {
        super();
        this.current_pipe = '';
        this.repair_duration = '';
        this.current_max_results = 1;
    }

    onInit(container, data)
    {
        try
        {
            this.current_pipe = data.pipe_List[0];

            let pipelist = add_dropdown('select_a_pipe', 'Select A Pipe', data.pipe_List, immpage_ui_event);

            let element = get_by_id(pipelist, ('select_a_pipe_menu'));
            if (element !== null)
            {
                element.style.maxHeight = '280px';
                element.style.width = '100%';
                element.style.overflowY = 'auto';
            }

            element = get_by_id(pipelist, ('select_a_pipe_button'));
            if (element !== null)
            {
                element.className += ' w-100 mb-2';
            }


            this.repair_duration = data.repair_duration[0];

            let repair_duration = add_dropdown('repair_duration', 'Repair Duration:' + this.repair_duration, data.repair_duration, immpage_ui_event);
            element = get_by_id(repair_duration, ('repair_duration_menu'));
            if (element !== null)
            {
                element.style.maxHeight = '280px';
                element.style.width = '100%';
                element.style.overflowY = 'auto';
            }

            element = get_by_id(repair_duration, ('repair_duration_button'));
            if (element !== null)
            {
                element.className += ' w-100 mb-2';
            }

            this.current_max_results = data.number_of_solutions[0];

            let resultslist = add_dropdown('results_list', 'Maximum number of Solutions:' + this.current_max_results, data.number_of_solutions, immpage_ui_event);

            element = get_by_id(resultslist, ('results_list_menu'));
            if (element !== null)
            {
                element.style.maxHeight = '280px';
                element.style.width = '100%';
                element.style.overflowY = 'auto';
            }

            element = get_by_id(resultslist, ('results_list_button'));
            if (element !== null)
            {
                element.className += ' w-100 mb-2';
            }

            let root = document.createElement('div');
            root.className = 'flex-container';
            container.appendChild(root);

            let row =  document.createElement('div');
            row.className = 'row';
            root.appendChild(row);

            let div = document.createElement('div');
            div.className = "col-4";
            row.appendChild(div);

            let div2 = document.createElement('div');
            div2.className = "col-4";
            row.appendChild(div2);

            let div3 = document.createElement('div');
            div3.className = "col-4";
            row.appendChild(div3);

            div2.appendChild(repair_duration);
            div2.appendChild(resultslist);

            div2.appendChild(pipelist);

            let sim_button = add_button('button_imm', 'Run IMM', "btn btn-primary w-100", immpage_ui_event);
            sim_button.innerHTML = 'Run IMM:' + this.current_pipe;
            div2.appendChild(sim_button);

            this.handle_ui_event(undefined, undefined);

        }catch (error)
        {
            alert_message(arguments,error.toString());
            return;
        }
    }

    handle_ui_event(id, data)
    {
        if (id === 'results_list')
        {
            this.current_max_results = data['text'];
        }


        if (id === 'select_a_pipe')
        {
            this.current_pipe = data['text'];
        }

        if (id === 'repair_duration')
        {
            this.repair_duration = data['text'];
        }

        let element = get_by_id(document.getElementById(window.imm_page.root_label), 'results_list_button');
        element.firstChild.data = 'Maximum number of Solutions:' + this.current_max_results;

        element = get_by_id(document.getElementById(window.imm_page.root_label), 'repair_duration_button');
        element.firstChild.data = 'Repair Duration:' + this.repair_duration;

        element = get_by_id(document.getElementById(window.imm_page.root_label), 'select_a_pipe_button');
        element.firstChild.data = 'Select A Pipe:' + this.current_pipe;

        element = get_by_id(document.getElementById(window.imm_page.root_label), 'button_imm');
        element.innerHTML = 'Run IMM<br>pipe' + this.current_pipe + ' Duration:' + this.repair_duration +' Max.Solutions:' + this.current_max_results;


        if(id === 'button_imm')
        {
            let cmd = 'post_imm_start';

            let data = {};
            data['access_token'] = window.access_token;
            data['selected_pipe'] = this.current_pipe;
            data['repair_duration'] = this.repair_duration;
            data['max_number_of_solutions'] = this.current_max_results;
            axios.post(cmd, data).then(function (response)
            {
                window.imm_page.periodic_update();
            }).catch(function (error)
            {
                alert_message(arguments, error);
            });
        }
    }
}

class BusyMode extends IMMMode
{
    constructor()
    {
        super();
    }

    onInit(container, data)
    {
        let label = add_label('busymode_text', 'Working on IMM');
        container.appendChild(label);

    }
}

class CompleteMode extends IMMMode
{
    constructor()
    {
        super();
    }

    add_text(element, text)
    {
        let text_div = document.createElement('p');
        text_div.innerHTML = text;
        element.appendChild(text_div);

    }

    onInit(container, data)
    {
        let result_holder = document.createElement('div');
        result_holder.className = 'container-fluid mb-2';
        result_holder.style.overflowY = 'scroll';
        result_holder.style.overflowX = 'hidden';
        result_holder.style.height = '100px' ; //'calc(100vh - 13em)'; //GARETH - this is a bit dodgy ;) -> see testbed header and  number of rows
        result_holder.style.height = 'calc(100vh - 13em)'; //GARETH - this is a bit dodgy ;) -> see testbed header and  number of rows
        result_holder.id = 'imm_result_holder';
        container.appendChild(result_holder);


        let row = document.createElement('div');
        row.className = 'row';
        result_holder.appendChild(row);

        let col = document.createElement('div');
        col.className = 'col-1';
        row.appendChild(col);

        col = document.createElement('div');
        col.className = 'col-10';
        row.appendChild(col);

        if(data['new_results']['found_solution'] === true)
        {
            let acc = document.createElement('div');
            acc.id = 'imm_accordian';
            col.appendChild(acc);

            for(let i=0;i<data['new_results']['solutions'].length;i++)
            {
                let card = document.createElement('div');
                card.className='card';
                acc.appendChild(card);

                let header = document.createElement('div');
                header.className ='card-header';
                card.appendChild(header);

                let row1 = document.createElement('div');
                row1.className = 'row';
                header.appendChild(row1);

                let col1 = document.createElement('div');
                col1.className = 'col-6';
                row1.appendChild(col1);

                let col2 = document.createElement('div');
                col2.className = 'col-6';
                row1.appendChild(col2);

                let h5 = document.createElement('h5');
                //h5.className = 'mb-0';
                //col1.appendChild(h5);
                let button = document.createElement('button');
                col1.appendChild(button);
                button.className="btn btn-link collapsed";
                button.dataset.target = '#imm_target_' + (i+1).toString();
                button.dataset.toggle ="collapse";
                //data-toggle="collapse"
                // data-target="#collapseThree">
                button.innerHTML = 'Intervention ' + (i+1).toString();

                let text_div = document.createElement('p');
                text_div.className = 'mt-1';
                text_div.style.textAlign = 'right';


                text_div.innerHTML = 'Score:'+data['new_results']['solutions'][i]['PTOTAL'].toString();
                col2.appendChild(text_div);

                let collapse = document.createElement('div');
                collapse.className="collapse";
                collapse.dataset.parent = '#' + acc.id;
                collapse.id = 'imm_target_' + (i+1).toString();
                card.appendChild(collapse);
                //data-parent="#accordion">
                let body = document.createElement('div');
                body.className ='card-body';


                this.add_text(body, '<strong>Intervention Steps</strong>');


                for(let step = 0;step < data['new_results']['solutions'][i]['STEPS'].length;step++)
                {
                    this.add_text(body, data['new_results']['solutions'][i]['STEPS'][step]);
                }

                this.add_text(body, '<br><br> ');
                this.add_text(body, '<strong>Performance Indicators</strong>');
                this.add_text(body,'P1 (Number of Customer Minutes with Zero Pressure):' + data['new_results']['solutions'][i]['P1'].toString() );
                this.add_text(body,'P2 (Number of Customer Minutes with Low Pressure (<6m):' + data['new_results']['solutions'][i]['P2'].toString() );
                this.add_text(body,'P3 (Unmet Demand (m3)):' + data['new_results']['solutions'][i]['P3'].toString() );
                this.add_text(body,'P4 (Discoloration Risk Increase Score):' + data['new_results']['solutions'][i]['P4'].toString() );
                this.add_text(body,'P5 (Total Leak Volume (m3):' + data['new_results']['solutions'][i]['P5'].toString() );

                collapse.appendChild(body);
            }
        }
        else
        {
            for(let i = 0;i < data['new_results']['diagnostics'].length;i++)
            {
                this.add_text(col, data['new_results']['diagnostics'][i]);
            }
        }
        /*
        let text = [];
        text.push('IMM Finished!');
        text.push('Instructions');

        for(let i=0;i<data['instructions'].length;i++)
        {
            text.push(data['instructions'][i]);
        }
        
        for(let i=0;i<text.length;i++)
        {
            let p = document.createElement('p');
            p.innerText = text[i];
            col.appendChild(p);
        }*/



        let sim_button = add_button('busymode_restart_button','Reset IMM', "btn btn-primary w-100", immpage_ui_event);

        sim_button.className += ' mb-2';
        container.appendChild(sim_button);
    }

    handle_ui_event(id, data)
    {
        if (id === 'busymode_restart_button')
        {
            console.log('do IMM');
            let cmd = 'post_imm_reset';

            let data = {};
            data['access_token'] = window.access_token;
            data['selected_pipe'] = this.current_pipe;
            axios.post(cmd, data).then(function (response)
            {
                window.imm_page.periodic_update();
            }).catch(function (error)
            {
                alert_message(arguments, error);
            });
        }
    }
}

class IMMPage extends charting_base
{
    constructor()
    {
        super();
        this.my_root = undefined;
        this.current_mode = 'undefined';
        this.periodic_update_time_as_seconds = 10;

        this.mode_lookup = {};
        this.mode_lookup['idle'] = {'mode': new IdleMode()};
        this.mode_lookup['busy'] = {'mode': new BusyMode()};
        this.mode_lookup['complete'] = {'mode': new CompleteMode()};
    }

    onInit(root)
    {
        this.current_mode = 'undefined';
        window.imm_page = this;
        this.root_label = 'imm_page_root';
        super.onInit(root);

        window.setInterval(function ()
        {
            window.imm_page.periodic_update();
        }, (1000 * this.periodic_update_time_as_seconds));

        window.imm_page.periodic_update();
    }

    periodic_update()
    {
        //do an arbitrary GET to see if the user is still valid/logged in etc
        let payload = {};
        payload['access_token'] = window.access_token;
        let cmd = 'get_imm_data';

        axios.get(cmd, {params: payload}).then(response =>
        {
            if (response.status !== 200)
            {
                alert_message(arguments,'Can\'t load data from server');
                return;
            }

            if (this.current_mode != response.data.status)
            {
                let element = document.getElementById(this.root_label);

                if(element !== null)
                {
                    element.parentNode.removeChild(element);
                }

                let container = document.createElement('div');
                container.className = 'container-fluid';
                container.id = this.root_label;

                document.body.appendChild(container);

                this.mode_select(response.data);
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

    mode_select(data)
    {
        console.log();
        try
        {
            this.current_mode = data.status;
            let container = document.getElementById(this.root_label);

            if (this.current_mode in this.mode_lookup)
            {
                this.mode_lookup[this.current_mode]['mode'].onInit(container, data);
            }
            else
            {
                alert_message(arguments,'Unknown mode:' + this.current_mode);
                return;
            }
        }catch (error)
        {
            alert_message(arguments,error.toString() +' ' + this.current_mode);
            return;
        }
    }

    handle_ui_event(id, data)
    {
        this.mode_lookup[this.current_mode]['mode'].handle_ui_event(id, data);
    }
}

function immpage_ui_event(id, data)
{
    window.imm_page.handle_ui_event(id, data);
}