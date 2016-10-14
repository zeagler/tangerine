<html>
    <head>
        <title>Tangerine Status Page</title>
        
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
        
        <!-- FuelUX, to be removed -->
        <link href="https://www.fuelcdn.com/fuelux/3.13.0/css/fuelux.min.css" rel="stylesheet">
        <script src="https://www.fuelcdn.com/fuelux/3.13.0/js/fuelux.min.js"></script>

        <!-- Typeahead -->
        <script src="https://twitter.github.io/typeahead.js/releases/latest/typeahead.bundle.js"></script>

        <!-- Tangerine scriptes -->
        <script src="static/scripts.js"></script>
        
        <script>
            $(document).ready(function(e) {
                set_job(null);// This will set the job and load tasks

                setInterval(function(){  // this will update tasks every 5 seconds
                    loadTasks()
                }, 5000);
            });
        </script>
    </head>
    
    <body>                
        <nav id="navbar" class="navbar navbar-default navbar-static-top" style="max-height: 50px;">
            <div class="container-fluid">
                <ul class="nav navbar-nav">
                    <li class="active"><a>Overview</a></li>
                    <li><a href="/history">History</a></li>
                    <li><a>Infrastructure</a></li>
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
    
        <div class="container-fluid">
            <div id="task_panel" class="panel panel-default">
                <div class="panel-heading">
                    <button id="addTask" class="btn icon-btn btn-success" data-toggle="modal" onclick="addTaskModal()">
                        <span class="glyphicon btn-glyphicon glyphicon-plus img-circle text-success"></span>
                        Add Task
                    </button>
                    <button id="addJob" class="btn icon-btn btn-success" data-toggle="modal" onclick="addJobModal()" style="margin-left: 10px">
                        <span class="glyphicon btn-glyphicon glyphicon-plus img-circle text-success"></span>
                        Add Job
                    </button>
                    <button id="addBulk" class="btn icon-btn btn-success" data-toggle="modal" onclick="addBulkModal()" style="margin-left: 10px">
                        <span class="glyphicon btn-glyphicon glyphicon-upload img-circle text-success"></span>
                        Bulk Add
                    </button>
                    <div id="find-task" class="col-xs-2 pull-right">
                        <input class="form-control typeahead" id="searchTasks" type="text" placeholder="search">
                    </div>
                    
                    <hr id="panel-divider">
                    
                    <ul id="switch" class="nav nav-pills nav-justified">
                        <li class="active"><a data-toggle="tab">All</a></li>
                        <li><a data-toggle="tab">Running</a></li>
                        <li><a data-toggle="tab">Ready</a></li>
                        <li><a data-toggle="tab">Queued</a></li>
                        <li><a data-toggle="tab">Success</a></li>
                        <li><a data-toggle="tab">Failed</a></li>
                        <li><a data-toggle="tab">Stopped</a></li>
                    </ul>
                </div>
                    
                <div class="panel-body">
                    <div id="job_panel" class="container"></div>
                    <div id="tasks" class="container"></div>
                </div>
            </div>
        </div>
        
        <!-- Modals -->
        <div class="modal fade" id="jobModal" role="dialog">
            <div class="modal-dialog modal-md">
                <div id="display-job-modal-content" class="modal-content">
                    <!-- Filled in with javascipt -->
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="displayTaskModal" role="dialog">
            <div class="modal-dialog modal-lg">
                <div id="display-task-modal-content" class="modal-content">
                    <!-- Templated by mako and display_task.html.mako -->
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="updateTaskModal" role="dialog" data-backdrop="static">
            <div class="modal-dialog modal-lg">
                <div id="update-task-modal-content" class="modal-content">
                    <!-- Templated by mako and update_task.html.mako -->
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="cloneTaskModal" role="dialog" data-backdrop="static">
            <div class="modal-dialog modal-lg">
                <div id="clone-task-modal-content" class="modal-content">
                    <!-- Templated by mako and update_task.html.mako -->
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="addTaskModal" role="dialog" data-backdrop="static">
            <div class="modal-dialog modal-lg">
                <div id="add-task-modal-content" class="modal-content">
                    <!-- Templated by mako and new_task.html.mako -->
                </div>
            </div>
        </div>
    </body>
</html>