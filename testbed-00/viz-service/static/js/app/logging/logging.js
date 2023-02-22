/*jshint -W069*/
/*jshint -W080*/
/*jshint -W104*/
/*jshint -W117*/
/* jshint strict: false */
/*jshint esversion: 6*/

function logging_init()
{
    let periodic_update_time_as_seconds = 60;

    window.setInterval(function ()
    {
        pilot_log_periodic_update();
    }, (1000 * periodic_update_time_as_seconds));

    pilot_log_periodic_update();
}

function pilot_log_periodic_update()
{
    let payload = {};
    payload['access_token'] = 0;
    let cmd = 'get_log_data';

    axios.get(cmd, {params: payload}).then(response =>
    {
        if (response.status === 200)
        {
            build_ui(response.data);
        }
        else
        {
            alert_message(arguments,'failed to read data');
        }
    }).catch(function (error)
    {
        alert_message(arguments,'failed to read data: ' + error);
    });
}

function build_ui(data)
{
    let element = document.getElementById("log_table");

    if(element !== null)
    {
        element.parentNode.removeChild(element);
    }

    let container = document.createElement('div');
    container.className = 'container-fluid';
    container.id = 'log_table';

    let table = document.createElement('table');
    table.className = 'table';

    container.appendChild(table);

    let head = document.createElement('thead');
    table.appendChild(head);


    let tr = document.createElement('tr');
    head.appendChild(tr);

    let columns = [{name:'Time', width:'width:15%'},
        {name:'Message',width:'width:65%'},
        {name:'File', width:'width:20%'},
        ];

    for(let i=0;i<columns.length;i++)
    {
        let th = document.createElement('th');
        th.scope = 'col';
        th.style = columns[i]['width'];
        th.innerText = columns[i]['name'];
        tr.appendChild(th);
    }

    let body = document.createElement('tbody');
    table.appendChild(body);

    if(data !== undefined)
    {
        for(let index = 0;index < data.length;index++)
        {
            tr = document.createElement('tr');
            body.appendChild(tr);

            //time
            let th = document.createElement('th');
            th.scope = 'row';
            th.innerHTML = data[index]['time'];
            tr.appendChild(th);

            //message
            td = document.createElement('td');
            td.innerHTML = data[index]['message'];
            tr.appendChild(td);

            //file
            td = document.createElement('td');
            td.innerHTML = data[index]['file'];
            tr.appendChild(td);
        }

        {
            let text = document.createElement('div');
            text.className = 'container';
            let h1 = document.createElement('p');
            h1.className = 'text-center';
            text.appendChild(h1);
            h1.innerText = 'End of list';

            container.appendChild(text);

            for(let i=0;i<5;i++)
            {
                container.appendChild(document.createElement('br') );
            }
        }
    }

    document.body.appendChild(container);
}
