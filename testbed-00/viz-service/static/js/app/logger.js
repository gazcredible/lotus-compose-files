let log_index = 0;

function log_message(args, msg, type= 'INFO')
{
    let data = {};
    data['loc'] = window.access_token;
    data['device'] = '';
    data['property'] = '';

    data['mode'] = type;

    try
    {
        data['message'] = args.callee.name.toString() + ' ' + msg;
    }
    catch(e)
    {
        data['message'] = '<no callee> ' + msg;
    }

    if (data['message'].includes('TypeError'))
    {
           alert(log_index.toString() + ' ' + data['mode'] +':'+data['message']);
    }

    log_index = log_index +1;


    axios.post('add_log',data);
}

function alert_message(args, msg)
{
    try
    {
        alert(args.callee.name.toString() + 'Alert:' + msg);
    }
    catch(e)
    {
        alert('Alert:' + msg);
    }
}
