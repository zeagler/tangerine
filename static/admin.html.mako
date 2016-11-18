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
            var settings = {  ec2_scaling_enabled: "${settings['ec2_scaling_enabled']}",
                              spot_fleet_request_id: "${settings['spot_fleet_request_id']}",
                              ec2_scale_limit: "${settings['ec2_scale_limit']}",
                              agent_development_mode: "${settings['agent_development_mode']}",
                              docker_log_directory: "${settings['docker_log_directory']}",
                              docker_registry_url: "${settings['docker_registry_url']}",
                              docker_registry_username: "${settings['docker_registry_username']}",
                              postgres_host: "${settings['postgres_host']}",
                              postgres_port: "${settings['postgres_port']}",
                              postgres_dbname: "${settings['postgres_dbname']}",
                              postgres_user: "${settings['postgres_user']}",
                              slack_enabled: "${settings['slack_enabled']}",
                              slack_webhook: "${settings['slack_webhook']}",
                              web_use_auth: "${settings['web_use_auth']}",
                              web_github_oauth_id: "${settings['web_github_oauth_id']}",
                              web_ssl_cert_path: "${settings['web_ssl_cert_path']}",
                              web_ssl_key_path: "${settings['web_ssl_key_path']}",
                              web_ssl_chain_path: "${settings['web_ssl_chain_path']}"
                           }
            var users = {}
            % for user in users:
                  users[${user.userid}] = ${user.__dict__}
            % endfor
            
            function add_tooltip(object_id, message) {
                $(object_id).attr("data-toggle", "tooltip");
                $(object_id).attr("data-placement", "top");
                $(object_id).attr("title", message);
                $(object_id).attr('data-original-title', message);
                $(object_id).tooltip("enable");
            }
            
            function load_users() {
                $("#admin-panel-body-users-content").html("")
                $.each(users, function(i, user) {
                    $("#admin-panel-body-users-content").append(
                        '<div class="panel panel-default user_panel" style="height: auto; width: 30%; margin-right: 10px;" onclick="show_user(\'' + user.userid + '\')">' +
                            '<div style="width: 98%; overflow: hidden; padding: 5px;">' +
                                '<span class="col-xs-2">' +
                                    '<img src="https://avatars.githubusercontent.com/u/' + user.userid + '" width=60 heigth=60>' +
                                '</span>' +
                                '<span class="col-xs-9 col-xs-offset-1">' +
                                    '<span style="font-size: 18px;">' + user.username + '</span>' +
                                    '</br>' +
                                    '<span class="small">' + user.usertype + '</span>' +
                                '</span>' +
                            '</div>' +
                        '</div>'
                    )
                });
            }
            
            function show_user(userid) {
                $(".fa-spinner, .fa-spin, .fa-check-circle-o, .fa-times-circle-o").removeClass("fa-spinner fa-spin fa-check-circle-o fa-times-circle-o");
                $("#user-update-status").html("").addClass("hide")
                    
                $('#modal-username').html(users[userid].username)
                $('#modal-userid').html(users[userid].userid)
                
                if (users[userid].usertype == "user") {
                    $('#modal-type-user').prop("checked", true)
                    $('#modal-type-admin').prop("checked", false)
                } else if (users[userid].usertype == "admin") {
                    $('#modal-type-user').prop("checked", false)
                    $('#modal-type-admin').prop("checked", true)
                }
                
                $('#displayUserModal').modal('show');
            }
            
            function addUserModal() {
                $("#user-add-status").addClass("hide").html("");
                $.get('https://api.github.com/users/' + $("#search-users-text").val(), function(response) {
                    $("#add-usericon").html('<img src="https://avatars.githubusercontent.com/u/' + response.id + '" width=60 heigth=60>')
                    $('#add-username').html(response.login)
                    $('#add-type-user').prop("checked", true);
                    $('#add-type-admin').prop("checked", false);
                    
                    $(document).off('click', '#add-user-confirm').on('click', '#add-user-confirm', function (e) {
                        var username = response.login
                        var userid = response.id
                        var usertype
                        
                        if ($('#add-type-admin').prop("checked") == true) {
                            usertype = "admin"
                        } else {
                            usertype = "user"
                        }
                        
                        $.get('/add_user?userid=' + userid + '&username=' + username + '&usertype=' + usertype, function(add_response) {
                            var json = JSON.parse(add_response)
                            if (typeof(json.error) != 'undefined') {
                                // adding failed
                                $("#user-add-status").removeClass("hide").html("Failed to add user '" + username + "'").css({"color": "red"});
                                $('#addUserModal').modal('hide');
                                return true;
                            }
                        
                            // updating succeded
                            $("#user-add-status").removeClass("hide").html("Added '" + username + "' as " + usertype).css({"color": "green"});
                            users[userid] = {usertype: usertype, username: username, userid: userid}
                            load_users()
                            
                            $('#addUserModal').modal('hide');
                        });
                    });
                    
                    $('#addUserModal').modal('show');
                }).fail(function() {
                    $("#user-add-status").removeClass("hide").html("Could not find '" + $("#search-users-text").val() + "'").css({"color": "red"});
                });
            }
        
            $(document).ready(function(e) {
                load_users()
                
                $(document).on("click", "#search-users", function (e) {
                    addUserModal();
                });
            
                $(document).on('click', '#admin-panel-sidebar-links li', function (e) {
                                        
                    // clear update statuses
                    $(".fa-spinner, .fa-spin, .fa-check-circle-o, .fa-times-circle-o").removeClass("fa-spinner fa-spin fa-check-circle-o fa-times-circle-o");
                    $(".update-status").html("").addClass("hide")
                    
                
                    var displayed = $("#admin-panel-sidebar-links .active").attr("display")
                    var target = $(this).attr("display")
                    
                    
                    $("#admin-panel-sidebar-links .active").removeClass("active")
                    $("#admin-panel-body-" + displayed).addClass("hide")
                    
                    
                    $(this).addClass("active")
                    $("#admin-panel-body-" + target).removeClass("hide")
                });
                
                $(document).on('click', '#delete-user', function (e) {
                    e.preventDefault()

                    var userid = $('#modal-userid').html()

                    $.get('delete_user?userid=' + userid, function(response) {
                        var json = JSON.parse(response)

                        if (typeof(json.error) != 'undefined') {
                            // adding failed
                            $("#user-add-status").removeClass("hide").html("Failed to delete user '" + users[userid].username + "'").css({"color": "red"});
                            $('#addUserModal').modal('hide');
                            return true;
                        }
                            
                        $("#user-add-status").removeClass("hide").html("Deleted '" + users[userid].username + "'").css({"color": "green"});
                        $('#displayUserModal').modal('hide');
                        delete users[userid];
                        load_users()
                    });
                });
                
                $(document).on('click', '#update-user-type', function (e) {
                    e.preventDefault()
                    
                    $(".fa-spinner, .fa-spin, .fa-check-circle-o, .fa-times-circle-o").removeClass("fa-spinner fa-spin fa-check-circle-o fa-times-circle-o");
                    $("#user-update-status").html("").addClass("hide")
                    
                    var type = ""
                    var userid = $('#modal-userid').html()
                    
                    if ($('#modal-type-user').prop("checked") == true) {
                        if (users[userid].usertype == "user") return
                        type = "user"
                    } else if ($('#modal-type-admin').prop("checked") == true) {
                        if (users[userid].usertype == "admin") return
                        type = "admin"
                    } else {
                        return
                    }
                    
                    $.get('update_user?userid=' + userid + '&usertype=' + type, function(response) {
                        var json = JSON.parse(response)
                        
                        $("#user-update-status").html("").removeClass("hide")

                        if (typeof(json.error) != 'undefined') {
                            // updating failed
                            $("#user-update-status").addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin fa-check-circle-o").css({"color": "red"});
                            $("#user-add-status").removeClass("hide").html("Failed to change '"+ users[userid].username +"' to " + type).css({"color": "red"});
                            add_tooltip("#user-update-status", "User type failed to update");
                            return true;
                        }
                    
                        // updating succeded
                        $("#user-update-status").addClass("fa-check-circle-o").removeClass("fa-spinner fa-spin fa-times-circle-o").css({"color": "green"});
                        $("#user-add-status").removeClass("hide").html("Changed '" + users[userid].username + "' to " + type).css({"color": "green"});
                        add_tooltip("#user-update-status", "User type was updated");
                        users[userid].usertype = type
                        load_users()
                    });
                });
                
                $(document).on('click', '.btn-update', function (e) {
                    e.preventDefault()
                    
                    // clear update statuses
                    $(".fa-spinner, .fa-spin, .fa-check-circle-o, .fa-times-circle-o").removeClass("fa-spinner fa-spin fa-check-circle-o fa-times-circle-o");
                    $(".update-status").html("").addClass("hide")
                    
                    // [setting_name, setting_value, html_element_id]
                    var requests = []
                    var group = $(this).attr('id')
                    
                    // TODO: validate the settings request
                    // Amazon settings
                    if ($(this).attr('id') == "update-amazon") {
                        if ($("#enable-ec2-scale").prop("checked").toString() != settings['ec2_scaling_enabled'])
                            requests.push(["ec2_scaling_enabled", $("#enable-ec2-scale").prop("checked").toString(), "#enable-ec2-scale-status"])
                        
                        if ($("#spot-fleet-id").val() != settings['spot_fleet_request_id'])
                            requests.push(["spot_fleet_request_id", $("#spot-fleet-id").val(), "#spot-fleet-id-status"])
                        
                        if ($("#ec2-scale-limit").val() != settings['ec2_scale_limit'])
                            requests.push(["ec2_scale_limit", $("#ec2-scale-limit").val(), "#ec2-scale-limit-status"])
                    
                    // Agent settings
                    } else if ($(this).attr('id') == "update-agent") {
                        if ($("#agent-development").prop("checked").toString() != settings['agent_development_mode'])
                            requests.push(["agent_development_mode", $("#agent-development").prop("checked").toString(), "#agent-development-status"])
                    
                    // Docker settings
                    } else if ($(this).attr('id') == "update-docker") {
                        if ($("#docker-log-directory").val() != settings['docker_log_directory'])
                            requests.push(["docker_log_directory", $("#docker-log-directory").val(), "#docker-log-directory-status"])
                        
                        if ($("#docker-registry").val() != settings['docker_registry_url'])
                            requests.push(["docker_registry_url", $("#docker-registry").val(), "#docker-registry-status"])
                        
                        if ($("#docker-username").val() != settings['docker_registry_username'])
                            requests.push(["docker_registry_username", $("#docker-username").val(), "#docker-username-status"])
                        
                        if ($("#docker-password").val() != "" && $("#docker-password").val() != settings['docker_registry_password'])
                            requests.push(["docker_registry_password", $("#docker-password").val(), "#docker-password-status"])
                        
                    // Postgres settings
                    } else if ($(this).attr('id') == "update-postgres") {
                        if ($("#postgres-host-address").val() != settings['postgres_host'])
                            requests.push(["postgres_host", $("#postgres-host-address").val(), "#postgres-host-address-status"])
                        
                        if ($("#postgres-port").val() != settings['postgres_port'])
                            requests.push(["postgres_port", $("#postgres-port").val(), "#postgres-port-status"])
                        
                        if ($("#postgres-database").val() != settings['postgres_dbname'])
                            requests.push(["postgres_dbname", $("#postgres-database").val(), "#postgres-database-status"])
                        
                        if ($("#postgres-username").val() != settings['postgres_user'])
                            requests.push(["postgres_user", $("#postgres-username").val(), "#postgres-username-status"])
                        
                        if ($("#postgres-password").val() != "" && $("#postgres-password").val() != settings['postgres_pass'])
                            requests.push(["postgres_pass", $("#postgres-password").val(), "#postgres-password-status"])
                        
                    // Slack settings
                    } else if ($(this).attr('id') == "update-slack") {
                        if ($("#enable-slack-alerts").prop("checked").toString() != settings['slack_enabled'])
                            requests.push(["slack_enabled", $("#enable-slack-alerts").prop("checked").toString(), "#enable-slack-alerts-status"])
                    
                        if ($("#slack-webhook").val() != settings['slack_webhook'])
                            requests.push(["slack_webhook", $("#slack-webhook").val(), "#slack-webhook-status"])
                        
                    // Web settings
                    } else if ($(this).attr('id') == "update-web") {
                        if ($("#enable-auth").prop("checked").toString() != settings['web_use_auth'])
                            requests.push(["web_use_auth", $("#enable-auth").prop("checked").toString(), "#enable-auth-status"])
                    
                        if ($("#github-outh-id").val() != settings['web_github_oauth_id'])
                            requests.push(["web_github_oauth_id", $("#github-outh-id").val(), "#github-outh-id-status"])
                                            
                        if ($("#github-outh-secret").val() != "" && $("#github-outh-secret").val() != settings['web_github_oauth_secret'])
                            requests.push(["web_github_oauth_secret", $("#github-outh-secret").val(), "#github-outh-secret-status"])
                                            
                        if ($("#ssl-cert-path").val() != settings['web_ssl_cert_path'])
                            requests.push(["web_ssl_cert_path", $("#ssl-cert-path").val(), "#ssl-cert-path-status"])
                                            
                        if ($("#ssl-key-path").val() != settings['web_ssl_key_path'])
                            requests.push(["web_ssl_key_path", $("#ssl-key-path").val(), "#ssl-key-path-status"])
                                            
                        if ($("#ssl-chain-path").val() != settings['web_ssl_chain_path'])
                            requests.push(["web_ssl_chain_path", $("#ssl-chain-path").val(), "#ssl-chain-path-status"])

                    // invalid
                    } else {
                        return
                    }
                    
                    if (requests.length == 0)
                        $("#" + group + "-status").removeClass("hide").html("Settings are unchanged");
                    
                    $.each(requests, function(i, setting) {
                        $.get('set_setting?setting=' + setting[0] + '&value=' + setting[1], function(response) {
                            var json = JSON.parse(response)

                            if (typeof(json.error) != 'undefined') {
                                // updating failed
                                $(setting[2]).addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin fa-check-circle-o").css({"color": "red"});
                                add_tooltip(setting[2], "Setting failed to update");
                                return true;
                            }
                        
                            // updating succeded
                            $(setting[2]).addClass("fa-check-circle-o").removeClass("fa-spinner fa-spin fa-times-circle-o").css({"color": "green"});
                            add_tooltip(setting[2], "Setting was updated");
                            settings[setting[0]] = setting[1]
                        });
                    });
                });
            });
        </script>
    </head>
    
    <body>                
        <nav id="navbar" class="navbar navbar-default navbar-static-top" style="max-height: 50px;">
            <div class="container-fluid">
                <ul class="nav navbar-nav">
                    <li><a href="/">Overview</a></li>
                    <li><a href="/history">History</a></li>
                    <li><a href="/infrastructure">Infrastructure</a></li>
                    <li class="active"><a href="/admin">Admin</a></li>
                </ul>
                <ul class="nav navbar-nav navbar-right">
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
            <div id="admin-panel" class="panel panel-default">
                <div id="admin-panel-sidebar" class="container background-default">
                    <ul id="admin-panel-sidebar-links" class="nav nav-pills nav-stacked">
                      </br>
                      <span class="section-header">Tangerine</span>
                      <li display="users" class="active"><a>Users</a></li>
                      <li display="webhooks"><a>Webhooks</a></li>
                      <li display="instance-configurations"><a>Instance Configurations</a></li>
                      </br></br>
                      <span class="section-header">Settings</span>
                      <li display="amazon"><a>Amazon</a></li>
                      <li display="agent"><a>Agent</a></li>
                      <li display="docker"><a>Docker</a></li>
                      <li display="postgresql"><a>Postgresql</a></li>
                      <li display="slack"><a>Slack</a></li>
                      <li display="web"><a>Web Console</a></li>
                    </ul>
                </div>
                <div id="admin-panel-body" class="container">
                    <div id="admin-panel-body-users">
                        <h2>Users</h2>
                        
                        <div class="col-xs-12">
                            <div class="input-group col-xs-4">
                                <input type="text" class="form-control" id="search-users-text" placeholder="search for github user"/>
                                <span id="search-users" class="input-group-addon cursor-pointer">Add User</span>
                            </div>
                            <div id="user-add-status" class="hide update-status"></div>
                        </div>
                        
                        </br>
                        </br>
                        
                        <div class="col-xs-12" style="margin-top: 10px;">
                            <div id="admin-panel-body-users-content"></div>
                        </div>
                    </div>
                    
                    <div id="admin-panel-body-webhooks" class="hide">
                        <h2>Webhooks</h2>
                        
                    </div>
                    
                    <div id="admin-panel-body-instance-configurations" class="hide">
                        instance configs
                    </div>
                    
                    <div id="admin-panel-body-amazon" class="hide">
                        <h2>Amazon</h2>
                        </br>
                        <form class="form-horizontal">
                            <div class="checkbox">
                                <label class="col-sm-offset-2 col-sm-10">
                                    % if settings['ec2_scaling_enabled'] == "true":
                                        <input type="checkbox" id="enable-ec2-scale" checked>
                                    % else:
                                        <input type="checkbox" id="enable-ec2-scale">
                                    % endif
                                    Enable EC2 Scaling?<span id="enable-ec2-scale-status" class="fa"/>
                                </label>
                            </div>
                            </br>
                            <div class="form-group">
                                <label for="spot-fleet-id" class="col-sm-2 control-label">Spot Fleet Id<span id="spot-fleet-id-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="spot-fleet-id" placeholder="" value="${settings['spot_fleet_request_id']}">
                                    <span id="spot-fleet-id-help" class="help-block hide">The spot fleet request id to use when scaling up hosts.</span>
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="ec2-scale-limit" class="col-sm-2 control-label">EC2 Scale limit<span id="ec2-scale-limit-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="ec2-scale-limit" placeholder="" value="${settings['ec2_scale_limit']}">
                                    <span id="ec2-scale-limit-help" class="help-block hide">The maximum number of instance Tangerine is allowed to have running simultaneously.</span>
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="col-sm-offset-2 col-sm-10">
                                    <button id="update-amazon" class="btn btn-default btn-update">Update</button>
                                    <span id="update-amazon-status" class="update-status hide"></span>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <div id="admin-panel-body-agent" class="hide">
                        <h2>Agent</h2>
                        </br>
                        <form class="form-horizontal">
                            <div class="checkbox">
                                <label class="col-sm-offset-2 col-sm-10">
                                    % if settings['agent_development_mode'] == "true":
                                        <input type="checkbox" id="agent-development" checked>
                                    % else:
                                        <input type="checkbox" id="agent-development">
                                    % endif
                                    Start agents in development mode?<span id="agent-development-status" class="fa"/>
                                </label>
                            </div>
                            </br>
                            <div class="form-group">
                                <div class="col-sm-offset-2 col-sm-10">
                                    <button id="update-agent" class="btn btn-default btn-update">Update</button>
                                    <span id="update-agent-status" class="update-status hide"></span>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <div id="admin-panel-body-docker" class="hide">
                        <h2>Docker</h2>
                        </br>
                        <form class="form-horizontal">
                            <div class="form-group">
                                <label for="docker-log-directory" class="col-sm-2 control-label">Container log directory<span id="docker-log-directory-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="docker-log-directory" placeholder="" value="${settings['docker_log_directory']}">
                                </div>
                            </div>
                            </br></br>
                            <div class="form-group">
                                <label for="docker-registry" class="col-sm-2 control-label">Registry URL<span id="docker-registry-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="docker-registry" placeholder="" value="${settings['docker_registry_url']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="docker-username" class="col-sm-2 control-label">Registry username<span id="docker-username-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="docker-username" placeholder="" value="${settings['docker_registry_username']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="docker-password" class="col-sm-2 control-label">Registry password<span id="docker-password-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input type="password" class="form-control" id="docker-password" placeholder="" value="">
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="col-sm-offset-2 col-sm-10">
                                    <button id="update-docker" class="btn btn-default btn-update">Update</button>
                                    <span id="update-docker-status" class="update-status hide"></span>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <div id="admin-panel-body-postgresql" class="hide">
                        <h2>Postgres</h2>
                        </br>
                        <form class="form-horizontal">
                            <div class="form-group">
                                <label for="postgres-host-address" class="col-sm-2 control-label">Postgres host address<span id="postgres-host-address-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="postgres-host-address" placeholder="" value="${settings['postgres_host']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="postgres-port" class="col-sm-2 control-label">Postgres port<span id="postgres-port-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="postgres-port" placeholder="" value="${settings['postgres_port']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="postgres-database" class="col-sm-2 control-label">Postgres database<span id="postgres-database-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="postgres-database" placeholder="" value="${settings['postgres_dbname']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="postgres-username" class="col-sm-2 control-label">Postgres username<span id="postgres-username-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="postgres-username" placeholder="" value="${settings['postgres_user']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="postgres-password" class="col-sm-2 control-label">Postgres password<span id="postgres-password-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input type="password" class="form-control" id="postgres-password" placeholder="" value="">
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="col-sm-offset-2 col-sm-10">
                                    <button id="update-postgres" class="btn btn-default btn-update">Update</button>
                                    <span id="update-postgres-status" class="update-status hide"></span>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <div id="admin-panel-body-slack" class="hide">
                        <h2>Slack</h2>
                        </br>
                        <form class="form-horizontal">
                            <div class="checkbox">
                                <label class="col-sm-offset-2 col-sm-10">
                                    % if settings['slack_enabled'] == "true":
                                        <input type="checkbox" id="enable-slack-alerts" checked>
                                    % else:
                                        <input type="checkbox" id="enable-slack-alerts">
                                    % endif
                                    Enable Slack Alerts?<span id="enable-slack-alerts-status" class="fa"/>
                                </label>
                            </div>
                            </br>
                            <div class="form-group">
                                <label for="slack-webhook" class="col-sm-2 control-label">Slack Webhook<span id="slack-webhook-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="slack-webhook" placeholder="" value="${settings['slack_webhook']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="col-sm-offset-2 col-sm-10">
                                    <button id="update-slack" class="btn btn-default btn-update">Update</button>
                                    <span id="update-slack-status" class="update-status hide"></span>
                                </div>
                            </div>
                        </form>
                    </div>
                    
                    <div id="admin-panel-body-web" class="hide">
                        <h2>Web Console</h2>
                        </br>
                        <form class="form-horizontal">
                            <div class="checkbox">
                                <label class="col-sm-offset-2 col-sm-10">
                                    % if settings['web_use_auth'] == "true":
                                        <input type="checkbox" id="enable-auth" checked>
                                    % else:
                                        <input type="checkbox" id="enable-auth">
                                    % endif
                                    Use authentication?<span id="enable-auth-status" class="fa"/>
                                </label>
                            </div>
                            </br>
                            <div class="form-group">
                                <label for="github-outh-id" class="col-sm-2 control-label">Github OAuth ID<span id="github-outh-id-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="github-outh-id" placeholder="" value="${settings['web_github_oauth_id']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="github-outh-secret" class="col-sm-2 control-label">Github OAuth Secret<span id="github-outh-secret-alerts-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="github-outh-secret" placeholder="" value="">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="ssl-cert-path" class="col-sm-2 control-label">SSL Cert Path<span id="ssl-cert-path-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="ssl-cert-path" placeholder="" value="${settings['web_ssl_cert_path']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="ssl-key-path" class="col-sm-2 control-label">SSL Key Path<span id="ssl-key-path-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="ssl-key-path" placeholder="" value="${settings['web_ssl_key_path']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <label for="ssl-chain-path" class="col-sm-2 control-label">SSL Chain Path<span id="ssl-chain-path-alerts-status" class="fa"/></label>
                                <div class="col-sm-10">
                                    <input class="form-control" id="ssl-chain-path" placeholder="" value="${settings['web_ssl_chain_path']}">
                                </div>
                            </div>
                            <div class="form-group">
                                <div class="col-sm-offset-2 col-sm-10">
                                    <button id="update-web" class="btn btn-default btn-update">Update</button>
                                    <span id="update-web-status" class="update-status hide"></span>
                                </div>
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Modals -->
        <div class="modal fade" id="displayUserModal" role="dialog">
            <div class="modal-dialog modal-md">
                <div id="display-user-modal-content" class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                        <h4 id="modal-title-user-name" class="modal-title">Alter User</h4>
                    </div>

                    <div class="modal-body" style="height: auto; overflow: auto;">
                        <button id="delete-user" class="btn btn-danger pull-right">Delete User</button>
                        <dl class="dl-horizontal">
                            <dt>Username </dt><dd id="modal-username"></dd>
                            <dt>User id </dt><dd id="modal-userid"></dd>
                            </br>
                            <dt>User Type <span id="user-update-status" class="fa"/> </dt><dd>
                                <label class="radio-inline"><input id="modal-type-user" name="usertype" type="radio" value="user">user</label>
                                <label class="radio-inline"><input id="modal-type-admin" name="usertype" type="radio" value="admin">admin</label>
                                </br>
                                <button id="update-user-type" class="btn btn-default" style="margin-top: 10px">Update</button>
                            </dd>
                        </dl>
                    </div>

                    <div class="modal-footer">
                        <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="modal fade" id="addUserModal" role="dialog">
            <div class="modal-dialog modal-sm">
                <div id="add-user-modal-content" class="modal-content">
                    <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal">&times;</button>
                        <h4 id="modal-title-user-name" class="modal-title">Add User</h4>
                    </div>

                    <div class="modal-body" style="height: auto; overflow: auto;">
                        <div class="panel panel-default" style="height: auto; margin-right: 10px;">
                            <div style="width: 98%; overflow: hidden; padding: 5px;">
                                <span id="add-usericon" class="col-xs-2">
                                </span>
                                <span class="col-xs-8 col-xs-offset-2">
                                    <span id="add-username" style="font-size: 18px;"></span>
                                    </br>
                                    <span id="add-usertype" class="small">
                                        <label class="radio-inline"><input id="add-type-user" name="addusertype" type="radio" value="user">user</label>
                                        <label class="radio-inline"><input id="add-type-admin" name="addusertype" type="radio" value="admin">admin</label>
                                    </span>
                                </span>
                            </div>
                        </div>
                    </div>

                    <div class="modal-footer">
                        <button type="button" class="btn btn-default pull-left" data-dismiss="modal">Close</button>
                        <button id="add-user-confirm" type="button" class="btn btn-success pull-right">Add</button>
                    </div>
                </div>
            </div>
        </div>
        
    </body>
</html>