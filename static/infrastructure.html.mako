<html>
    <head>
        <title>Infrastructure</title>
        
        <link rel="stylesheet" type="text/css" href="static/style.css">
        <link rel="shortcut icon" type="image/x-icon" href="static/favicon.ico" />

        <script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>

        <!-- jQuery datatables -->
        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/v/bs-3.3.6/dt-1.10.12/b-1.2.2/r-2.1.0/sc-1.4.2/datatables.min.css"/> 
        <script type="text/javascript" src="https://cdn.datatables.net/v/bs-3.3.6/dt-1.10.12/b-1.2.2/r-2.1.0/sc-1.4.2/datatables.min.js"></script>

        <!-- Bootstrap Cerulean Theme -->
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.6/cerulean/bootstrap.min.css">
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.6/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>
        
        <!-- Font Awesome  -->
        <link href="https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css" rel="stylesheet" integrity="sha384-T8Gy5hrqNKT+hzMclPo118YTQO6cYprQmhrYwIiQ/3axmI1hQomh7Ud2hPOy8SP1" crossorigin="anonymous">

        <!-- Typeahead -->
        <script src="https://twitter.github.io/typeahead.js/releases/latest/typeahead.bundle.js"></script>
        
        <!-- Plot.ly for metric charts -->
        <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
        
        <!-- Tangerine scriptes -->
        <script src="static/scripts.js"></script>
        
        <script>
            $(document).ready(function(e) {
                loadHosts()
            
                setInterval(function(){  // this will update hosts every 5 seconds
                    loadHosts()
                }, 5000);
            });
        </script>
    </head>
    
    <body>                
        <nav id="navbar" class="navbar navbar-default navbar-static-top" style="max-height: 50px;">
            <div class="container-fluid">
                <ul class="nav navbar-nav">
                    <li><a href="/">Overview</a></li>
                    <li><a href="/history">History</a></li>
                    <li class="active"><a>Infrastructure</a></li>
                </ul>
                <ul class="nav navbar-nav navbar-right">
                    % if usertype == "admin":
                        <li><a>Admin</a></li>
                    % endif
                    <li>
                        <p id="nav_user" class="navbar-text dropdown-toggle" data-toggle="dropdown">
                            <img alt="${username}" src="${userimageurl}" style="height: 24px; width: 24px;"> ${username}
                        </p>
                        <ul class="dropdown-menu">
                            <li><a href="logout">Log out</a></li>
                        </ul>
                    </li>
                    <a class="navbar-brand" style="font: bold;">Tangerine</a>
                </ul>
            </div>
        </nav>
    
        <div id="infra_view" class="container-fluid">
            <div id="infra_panel" class="panel panel-default" style="height: auto;">
                <div style="width: 98%; margin-left: 1%; overflow: hidden;">
                    <p id="host_count_p">Hosts: <span id="host_count">0</span></p>
                    <p id="task_count_p">Queued Tasks: <span id="task_count">0</span></p>
                </div>
            </div>
            
            <div id="host_container"></div>
        </div>
        
        <!-- Modals -->
        <div class="modal fade" id="displayRunModal" role="dialog">
            <div class="modal-dialog modal-lg">
                <div id="display-run-modal-content" class="modal-content">
                    <!-- Templated by mako and display_run.html.mako -->
                </div>
            </div>
        </div>
        
    </body>
</html>