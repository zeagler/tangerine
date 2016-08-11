<html>
    <head>
        <title>Tangerine Status Page</title>
        
        <link rel="stylesheet" type="text/css" href="static/style.css">
        <link rel="shortcut icon" type="image/x-icon" href="static/favicon.ico" />

        <script src="https://code.jquery.com/jquery-2.2.4.min.js"></script>

        <link rel="stylesheet" type="text/css" href="https://cdn.datatables.net/v/bs-3.3.6/dt-1.10.12/b-1.2.2/r-2.1.0/sc-1.4.2/datatables.min.css"/> 
        <script type="text/javascript" src="https://cdn.datatables.net/v/bs-3.3.6/dt-1.10.12/b-1.2.2/r-2.1.0/sc-1.4.2/datatables.min.js"></script>

        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/patternfly/3.8.1/css/patternfly.min.css">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/patternfly/3.8.1/css/patternfly-additions.min.css">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/patternfly/3.8.1/js/patternfly.min.js"></script>

        <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootswatch/3.3.6/cerulean/bootstrap.min.css">
        <script type="text/javascript" src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.2.1/Chart.min.js"></script>

        <!-- Tangerine Scripts -->
        <script src="static/scripts.js"></script>
    </head>
    
    <body>
        <nav id="navbar" class="navbar navbar-default navbar-static-top" style="max-height: 50px;">
            <div class="container-fluid">
                <ul class="nav navbar-nav">
                    <li><a href="/">Overview</a></li>
                    <li class="active"><a>History</a></li>
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
        
        <!-- Modals -->
        <div class="modal fade" id="displayRunModal" role="dialog">
            <div class="modal-dialog modal-lg">
                <div id="display-run-modal-content" class="modal-content">
                    <!-- Templated by mako and display_run.html.mako -->
                </div>
            </div>
        </div>

        <div class="container-fluid" id="run_history">
            <table id="run_table" class="datatable table table-striped table-bordered" style="background-color: white!important">
              <thead>
                <tr>
                  <th>Id</th>
                  <th>Task</th>
                  <th>Result</th>
                  <th>Finished</th>
                </tr>
              </thead>
            </table>
            <script>
                // Initialize Datatables
                $(document).ready(function() {
                  $('#run_table').dataTable( {
                      ajax: "/get_runs",
                      columns: [
                          { data: 'run_id', width: "10%" },
                          { data: 'name', width: "30%" },
                          { data: 'result_state', width: "30%" },
                          { data: 'run_finish_time_str', width: "30%" }
                      ],
                      scrollY:        "100%",
                      order: [[0, 'desc']],
                      orderMulti: false,
                      autoWidth: true
                  });

                // Add event listener for opening and closing details
                $('#run_table tbody').on("mouseover", "tr", function () {
                    $(this).css({backgroundColor: 'f1f1f1'});
                }).on("mouseout", "tr", function () {
                    $(this).css({backgroundColor: 'f9f9f9'});
                }).on("click", "tr", function () {
                    $(this).css({backgroundColor: 'f9f9f9'});
                    id = $($(this).find('td')[0]).text();

                    $('#display-run-modal-content').load("display_run?id=" + id, function() {
                        $('#displayRunModal').modal('show');
                    });
                });
                
                });
                
            </script>
        </div>
    </body>
</html>