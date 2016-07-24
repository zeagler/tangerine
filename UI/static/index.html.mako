<html>
    <head>
        <link rel="stylesheet" type="text/css" href="static/style.css">
        <link rel="shortcut icon" type="image/x-icon" href="static/favicon.ico" />
        <link rel="stylesheet" type="text/css" href="static/sweetalerts/sweetalert2.min.css">
        <script src="https://code.jquery.com/jquery-3.0.0.min.js"></script>
        <script src="static/sweetalerts/sweetalert2.min.js"></script>
        <script src="static/scripts.js"></script> 
        <title>Tangerine Status Page</title>
        
        <!-- Bootstrap Framework
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" integrity="sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u" crossorigin="anonymous">
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css" integrity="sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp" crossorigin="anonymous">
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
        -->
    </head>
    
    <body>
        <div id="container" class="header">
            <ul class="topnav">
                <li><button onclick="toggle_visibility('success')" class="button success">Success</button></li>
                <li><button onclick="toggle_visibility('failed')" class="button failed">Failed</button></li>
                <li><button onclick="toggle_visibility('running')" class="button running">Running</button></li>
                <li><button onclick="toggle_visibility('ready')" class="button ready">Ready</button></li>
                <li><button onclick="toggle_visibility('queued')" class="button queued">Queued</button></li>
                <li class="right"><img src="static/favicon.ico" style="width:75px;height:75px;"></li>
                <li class="right"><span>Tangerine</span><li>
                <li class="right"><button onclick="addTask()" class="button addTask">+ Add Task</button></li>
            </ul>
        </div>

        <div id="container" class="content">
            % for task in tasks:
                <span class="task ${task.state}" style="" onclick="${task.state}Alert('${task.name}', '${task.imageuuid}', '${task.dependencies_str}', '${task.failures}', '${task.max_failures}', '${task.next_run_str}')">
                    <img src="static/${task.state}.png" alt="${task.state}" style="width:300px;height:113px;">
                    <p><span>${task.name}</span></p>
                </span>
            % endfor
        </div>
    </body>
</html>