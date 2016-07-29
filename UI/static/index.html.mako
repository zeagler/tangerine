<html>
    <head>
        <title>Tangerine Status Page</title>
        
        <link rel="stylesheet" type="text/css" href="static/style.css">
        <link rel="stylesheet/less" type="text/css" href="bootswatch.less" />
        <link rel="stylesheet/less" type="text/css" href="variables.less" />
        <link rel="shortcut icon" type="image/x-icon" href="static/favicon.ico" />

        <!-- Bootstrap -->
        <script src="https://code.jquery.com/jquery-3.0.0.min.js"></script>
        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.6/cerulean/bootstrap.min.css">
        <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js" integrity="sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa" crossorigin="anonymous"></script>

        <!-- Typeahead -->
        <script src="https://twitter.github.io/typeahead.js/releases/latest/typeahead.bundle.js"></script>

        <!-- FuelUX -->
        <link href="https://www.fuelcdn.com/fuelux/3.13.0/css/fuelux.min.css" rel="stylesheet">
        <script src="https://www.fuelcdn.com/fuelux/3.13.0/js/fuelux.min.js"></script>

        <script src="static/scripts.js"></script>
        
        <script>
            $(document).ready(function(e) {
                loadTasks(); // This will load tasks on page load

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
                    <li><a>History</a></li>
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
                        Add
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
                    <div id="tasks" class="container">
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modals -->
        <div class="modal fade" id="displayTaskModal" role="dialog">
            <div class="modal-dialog modal-lg">
                <div id="display-task-modal-content" class="modal-content">
                    <!-- Templated by mako and display_task.html.mako -->
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="updateTaskModal" role="dialog" data-backdrop="static">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                        <h4 class="modal-title">Update a Task</h4>
                    </div>
                    
                    <div id="update-task-modal-body" class="modal-body" style="text-align: center;">
                        <!-- Templated by mako and update_task.html.mako -->
                    </div>
                    
                    <div class="modal-footer" style="width: 100%; text-align:center">
                        <button type="button" class="btn btn-default pull-left" style="width: 100px;" data-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-default pull-left reset-form" style="width: 100px;">Reset</button>
                        <button type="button" class="btn btn-primary pull-right" style="width: 100px;" onclick="addTask()" data-dismiss="modal">Update</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="cloneTaskModal" role="dialog" data-backdrop="static">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                        <h4 class="modal-title">Add a Task</h4>
                    </div>
                    
                    <div id="clone-task-modal-body" class="modal-body" style="text-align: center;">
                        <!-- Templated by mako and update_task.html.mako -->
                    </div>
                    
                    <div class="modal-footer" style="width: 100%; text-align:center">
                        <button type="button" class="btn btn-default pull-left" style="width: 100px;" data-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-default pull-left reset-form" style="width: 100px;">Reset</button>
                        <button type="button" class="btn btn-primary pull-right" style="width: 100px;" onclick="addTask()" data-dismiss="modal">Add</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="addTaskModal" role="dialog" data-backdrop="static">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                        <h4 class="modal-title">Add a Task</h4>
                    </div>

                    <div id="add-task-modal-body" class="modal-body" style="text-align: center;">
                        <!-- filled with /static/new_task.html.mako -->
                    </div>

                    <div class="modal-footer" style="width: 100%; text-align:center">
                        <button type="button" class="btn btn-default pull-left" style="width: 100px;" data-dismiss="modal">Close</button>
                        <button type="button" class="btn btn-default pull-left reset-form" style="width: 100px;">Clear</button>
                        <button type="button" class="btn btn-primary pull-right" style="width: 100px;" onclick="addTask()" data-dismiss="modal">Add</button>
                    </div>
                </div>
            </div>
        </div>
    </body>
</html>