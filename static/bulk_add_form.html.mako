<script>
    /***
     * "Pre"-validation
     *
     * Ensure fields are proper while filling out the form, present the user
     *   with a visual error if there is a problem with the input
     ***/
    $("#name,#image").focusout(function() {
        if ($(this).val() == "") {
            $(this).parent().addClass("has-error");
            $(this).tooltip('enable')
            $(this).tooltip('show');
        }
    }).on('input',function(e){
        if ($(this).val() == "") {
            $(this).parent().addClass("has-error");
            $(this).tooltip('enable')
            $(this).tooltip('show');
        } else {
            $(this).parent().removeClass("has-error");
            $(this).tooltip('disable');
            $(this).tooltip('hide');
            $("#err_alert").hide()
        }
    });
    
    /***
     * Reset the form to it original values
     *
     * TODO: HIGHPRIORITY: environment and data volumes do not reset
     ***/
    $('.reset-form').on('click', function(e) {
        e.preventDefault();
        
        document.getElementById('add_job_form').reset();
        $.each($('.added'), function(i, obj) {
            if ($(obj).find("input")[0].value === "") {
                obj.remove();
            }
        });
    });
    
    /***
     * Initialize UI components
     *
     * Enable jQuery tooltips, hide the error tooltips and error alert
     * Enable the pillbox for adding dependencies
     ***/
    $('[data-toggle="tooltip"]').tooltip();
    $("#name,#image").tooltip('disable');
    $("#err_alert").hide()

    /***
     * Enable the "add" button for environment and data volumes
     * Destroy the previous listeners and create new ones
     ***/
    $(".add-more").off('click').on('click', function(e) {
        e.preventDefault();
        add_more_handler(this.id)
    });
    
    $(".remove-this").off('click').on('click', function(e) {
        e.preventDefault();
        $(this).parent().parent().remove();
    });
    
    /*****
     * Move the modal back a step, clear or reset fields based on which page the modal is returning to.
     *
     * 1: Go to the input page from the display page
     * 2: Go to the display page from the add page
     *****/
    $go_back = 0
    function back() {
        if ($go_back == 1) {
            $("#input_config").show()
            $("#show_config").addClass("hidden")
            $("#back-btn").addClass("hidden")
            $("#next-btn").removeClass("hidden")
            $("#add-btn").addClass("hidden")
            $go_back = 0
        } else if ($go_back == 2) {
            $("#show_config").removeClass("hidden")
            $("#add-btn").removeClass("hidden")
            $("#add_config").addClass("hidden")
            $go_back = 1
        }
    }
    
    /*****
     * Check that the configuration is valid JSON or YAML, check that each job and task has a name
     *    and image defined. Add each job or task to an array, and move the modal to the next page.
     *****/
    function checkConfig() {
        // Parse the config into jobs and tasks
        $config_arr = []
        $config_task_names = []
        $config_job_names = []
        
        if ($("#config").val() == "") {
            console.log('{"error": "No input"}')
            return
        }
        
        try {
            if ($("#json_format").prop("checked")) {
                config = JSON.parse($("#config").val());
            } else if ($("#yaml_format").prop("checked")) {
                config = YAML.parse($("#config").val());
            } else {
                console.log('{"error": "Pick a format"}')
                return JSON.parse('{"error": "Pick a format"}')
            }
        } catch (e) {
            console.log('{"error": "Could not parse document"}')
            return JSON.parse('{"error": "Could not parse document"}')
        }
        
        if (typeof(config.jobs) == 'undefined' && typeof(config.tasks) == 'undefined') {
            console.log('{"error": "Configuration is not valid. It must containe `jobs` or `tasks`"}')
            returnJSON.parse('{"error": "Configuration is not valid. It must containe `jobs` or `tasks`"}')
        }

        if (typeof(config.jobs) != 'undefined' && config.jobs != null) {
            for (var i=0; i<config.jobs.length; i++) {
                if (config.jobs[i] == null) continue
                
                if (typeof(config.jobs[i].name) == 'undefined') {
                    console.log('{"error": "All jobs need a name"}')
                    return JSON.parse('{"error": "All jobs need a name"}')
                }
                if (typeof(config.jobs[i].image) == 'undefined') {
                    console.log('{"error": "All jobs need an image. Check the job `' + config.jobs[i].name + '`"}')
                    return JSON.parse('{"error": "All jobs need an image. Check the job `' + config.jobs[i].name + '`"}')
                }
                if (typeof(config.jobs[i].tasks) !== 'undefined') {
                    for (var j=0; j<config.jobs[i].tasks.length; j++) {
                        if (typeof(config.jobs[i].tasks[j].name) == 'undefined') {
                            console.log('{"error": "All tasks need a name. Check tasks in the job `' + config.jobs[i].name + '`"}')
                            return JSON.parse('{"error": "All tasks need a name. Check tasks in the job `' + config.jobs[i].name + '`"}')
                        }
                    }
                }
                
                config.jobs[i].type = "job"
                $config_arr.push(config.jobs[i])
                $config_job_names.push(config.jobs[i].name)
            }
        }
        
        if (typeof(config.tasks) != 'undefined' && config.tasks != null) {
            for (var i=0; i<config.tasks.length; i++) {
                if (config.tasks[i] == null) continue

                if (typeof(config.tasks[i].name) == 'undefined') {
                    console.log('{"error": "All tasks need a name"}')
                    return JSON.parse('{"error": "All tasks need a name"}')
                }
                if (typeof(config.tasks[i].image) == 'undefined') {
                    console.log('{"error": "All tasks without a parent need an image". Check the task `' + config.tasks[i].name + '`"}')
                    return JSON.parse('{"error": "All tasks without a parent need an image. Check the task `' + config.tasks[i].name + '`"}')
                }
                
                config.tasks[i].type = "task"
                $config_arr.push(config.tasks[i])
                $config_task_names.push(config.tasks[i].name)
            }
        }
        
        if ($config_arr.length == 0) {
            console.log('{"error": "Blank config"}')
            return JSON.parse('{"error": "Blank config"}')
        }
        
        $go_back = 1
        $("#input_config").hide()
        $("#show_config").removeClass("hidden")
        $("#next-btn").addClass("hidden")
        $("#add-btn").removeClass("hidden")
        $("#back-btn").removeClass("hidden")
        display_config($config_arr)
    }
  
    /*****
     * Build the panel for an object. Only include a field if the object has a value for it.
     *****/
    function build_html_panel(panel_id, panel_object) {
        var html = '<div class="panel panel-default">' +
                      '<div class="row" style="width: 100%; margin-left: 1%; overflow: hidden">' +
                          '<div id="' + panel_id + '" class="col-xs-12">' +
                              '<div style="margin-top: 1%; margin-bottom: 1%; width: 100%; text-overflow: ellipsis; overflow: hidden;">' +
                                  '<font size="3" class="pull-left" onclick="toggle_panel_collapse(\'' + panel_id + '\')"><small id="collapse-state-' + panel_id + '" class="hidden-xs">[-]</small> <strong>' + panel_object.name + '</strong></font>' +
                              '</div>' +
                              '<div id="panels-' + panel_id + '" class="collapse in collapse-' + panel_id + '" style="margin: 2%; text-align: left">' +
                                  '<div class="row hidden-xs hidden-sm">' +
                                      '<div class="col-md-12 hide-overflow">'
        // Add Image
        if (typeof(panel_object.image) != "undefined" && panel_object.image != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Image:</div><div class="hide-overflow">' + panel_object.image + '</div></span>'
        
        // Add Cron
        if (typeof(panel_object.cron) != "undefined" && panel_object.cron != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Cron:</div><div class="hide-overflow">' + panel_object.cron + '</div></span>'
            
        // Add Command
        if (typeof(panel_object.command) != "undefined" && panel_object.command != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Command:</div><div class="hide-overflow">' + panel_object.command + '</div></span>'
            
        // Add Entrypoint
        if (typeof(panel_object.entrypoint) != "undefined" && panel_object.entrypoint != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Entrypoint:</div><div class="hide-overflow">' + panel_object.entrypoint + '</div></span>'
            
        // Add Description
        if (typeof(panel_object.description) != "undefined" && panel_object.description != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Description:</div><div class="hide-overflow">' + panel_object.description + '</div></span>'

        // Add every environment variable
        if (typeof(panel_object.environment) != "undefined" && panel_object.environment != null) {
            var env = ""
            for (key in panel_object.environment)
                env += key + ' = ' + panel_object.environment[key] + "</br>"
                
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Environment:</div><div class="hide-overflow">' + env + '</div></span>'
        }
             
        // Add every data volume
        if (typeof(panel_object.datavolumes) != "undefined" && panel_object.datavolumes != null) {
            var dvl = ""
            for (key in panel_object.datavolumes)
                dvl += key + ':' + panel_object.datavolumes[key] + "</br>"
                
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Data Volumes:</div><div class="hide-overflow">' + dvl + '</div></span>'
        }
        
        // Add every dependency
        if (typeof(panel_object.dependencies) != "undefined" && panel_object.dependencies != null) {
            var dep = ""
            for (key in panel_object.dependencies)
                dep += panel_object.dependencies[key] + "</br>"
                
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Dependencies:</div><div class="hide-overflow">' + dep + '</div></span>'
        }
        
        // Add every tag
        if (typeof(panel_object.tags) != "undefined" && panel_object.tags != null) {
            var tags = ""
            for (key in panel_object.tags)
                tags += panel_object.tags[key] + "</br>"
                
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Tags:</div><div class="hide-overflow">' + tags + '</div></span>'
        }
        
        // Add the recoverable exitcodes
        if (typeof(panel_object.exitcodes) != "undefined" && panel_object.exitcodes != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Exit Codes:</div><div class="hide-overflow">' + panel_object.exitcodes + '</div></span>'
        
        // Set the restartable flag
        if (typeof(panel_object.restartable) != "undefined" && panel_object.restartable != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Restartable:</div><div class="hide-overflow">' + panel_object.restartable + '</div></span>'
        
        // Add the maximum retry limit
        if (typeof(panel_object.max_failures) != "undefined" && panel_object.max_failures != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Retry Limit:</div><div class="hide-overflow">' + panel_object.max_failures + '</div></span>'

        // Add the delay
        if (typeof(panel_object.delay) != "undefined" && panel_object.delay != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Initial Delay:</div><div class="hide-overflow">' + panel_object.delay + '</div></span>'

        // Add the restart delay on failure
        if (typeof(panel_object.faildelay) != "undefined" && panel_object.faildelay != null)
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Restart Delay:</div><div class="hide-overflow">' + panel_object.faildelay + '</div></span>'

        // Add the parent overrides
        if (typeof(panel_object.removed_parent_defaults) != "undefined" && panel_object.removed_parent_defaults != null) {
            var rpd = ""
            for (key in panel_object.removed_parent_defaults)
                rpd += panel_object.removed_parent_defaults[key] + "</br>"
                
            html += '<span style="display: flex;"><div style="font-weight: bold; margin-right: 4px;">Parent Overrides:</div><div class="hide-overflow">' + rpd + '</div></span>'
        }
        
        html +=                       '</div>' +
                                  '</div>' +
                                  '<div class="row hidden-xs hidden-md hidden-lg hidden-xl">' +
                                      '<div class="hide-overflow" style="display: flex;">' +
                                          '<div style="font-weight: bold; margin-right: 4px; text-align: right;">Image:</br>Command:</br>Entrypoint:</div>' +
                                          '<div class="hide-overflow">' + panel_object.image + '</br>' + panel_object.command + '</br>' + panel_object.entrypoint + '</div>' +
                                      '</div>' +
                                  '</div>' +
                              '</div>' +
                          '</div>' +
                      '</div>' +
                  '</div>'
              
        return html
    }
    
    function build_html_adding(adding_id, adding_object) {
        var html = '<div style="margin-left: 1%;">' +
                        '<div id="' + adding_id + '">' +
                            '<div style="width: auto; text-overflow: ellipsis; overflow: hidden;">' +
                                '<font id="tooltip-' + adding_id + '" size="3" class="pull-left"><span id="status-' + adding_id + '" class="fa"/> ' + adding_object.name + '</font>' +
                            '</div>' +
                            '<div id="children-' + adding_id + '"></div>'
                        '</div>' +
                    '</div>'
              
        return html
    }
    
    /*****
     * Display a panel for each job and task in the modal
     *****/
    function display_config(config_arr) {
         $("#panel-container").html("")
    
        if (config_arr == null || typeof(config_arr) == 'undefined') {
            console.log('{"error": "Invalid configuration"}')
            return JSON.parse('{"error": "Invalid configuration"}')
        }
        
        $.each($config_arr, function(i, work) {
            if (work.type == "job") {
                $("#panel-container").append(build_html_panel("job" + i, work))
                
                $.each(work.tasks, function(j, task) {
                    $("#panels-job" + i).append(build_html_panel("job" + i + "task" + j, task))
                })
            } else if (work.type == "task") {
                $("#panel-container").append(build_html_panel("task" + i, work))
            }
        });
    }
    
    /*****
     * Collapse or expand a panel in the modal
     *****/
    function toggle_panel_collapse(panel_id) {
        var panel = $('#' + panel_id)
        
        if (panel.find("#collapse-state-" + panel_id).text() == "[+]") {
            panel.find("#collapse-state-" + panel_id).text("[-]")
            panel.find(".collapse-"+panel_id).collapse("show")
        } else {
            panel.find("#collapse-state-" + panel_id).text("[+]")
            panel.find(".collapse-"+panel_id).collapse("hide")
        }
    }
    
    /*****
     * Expand all panel in the modal
     *****/
    function expland_all() {
        $(".collapse").collapse("show")
        $("font small").text("[-]")
    }
    
    /*****
     * Collapse all panel in the modal
     *****/
    function collapse_all() {
        $(".collapse").collapse("hide")
        $("font small").text("[+]")
    }
    
    function add_tooltip(object_id, message) {
        $("#" + object_id).attr("data-toggle", "tooltip");
        $("#" + object_id).attr("data-placement", "top");
        $("#" + object_id).attr("title", message);
        $("#" + object_id).tooltip('enable');
    }
    
    /*******
     * Count the occurance of a name in an object array
     *******/
    function name_in_object_array(name, array) {
        return $.grep(array, function(obj) {
                    return obj.name == name;
                }).length
    }
    
    /*******
     * Count the occurance of a string in an array
     *******/
    function name_in_array(name, array) {
        return $.grep(array, function(obj) {
                    return obj == name;
                }).length
    }
    
    function check_for_job_conflicts(name, work_id) {
        // Check if the name is already used
        if (name_in_object_array(name, findJobs())) {
            $("#status-" + work_id).addClass("fa-times-circle-o").css({"color": "red"});
            add_tooltip("tooltip-" + work_id, "A job already exists with this name");
        } else if (name_in_array(name, $config_job_names) != 1) {
            $("#status-" + work_id).addClass("fa-times-circle-o").css({"color": "red"});
            add_tooltip("tooltip-" + work_id, "The name of this job is duplicated in the configuration");
        }
    }
    
    function check_for_task_conflicts(name, work_id) {
        // Check if the name of a task is repeated
        // If the name is repeated the other task must have a parent
        if ($.grep(getTasks(), function(obj) {
                    return (obj.name == name && obj.parent_job == null);
                }).length) {
            $("#status-" + work_id).addClass("fa-times-circle-o").css({"color": "red"});
            add_tooltip("tooltip-" + work_id, "A task already exists with this name");
        } else if (name_in_array(name, $config_task_names) != 1) {
            $("#status-" + work_id).addClass("fa-times-circle-o").css({"color": "red"});
            add_tooltip("tooltip-" + work_id, "The name of this task is duplicated in the configuration");
        }
    }
    
    function check_for_task_child_conflicts(name, tasks, work_id) {
        // Check if the name is repeated in the job
        if (name_in_object_array(name, tasks) != 1) {
            $("#status-" + work_id).addClass("fa-times-circle-o").css({"color": "red"});
            add_tooltip("tooltip-" + work_id, "The name of this task is duplicated in the job");
        }
    }
    
    function addConfig() {
        $go_back = 2
        $("#show_config").addClass("hidden")
        $("#add-btn").addClass("hidden")
        $("#add_config").removeClass("hidden")
        
        $("#add-container").html("")

        // First build the status page for adding the tasks
        $.each($config_arr, function(i, work) {
            if (work.type == "job") {
                $("#add-container").append(build_html_adding("add-job" + i, work))
                check_for_job_conflicts(work.name, "add-job" + i)
                
                $.each(work.tasks, function(j, task) {
                    $("#children-add-job" + i).append(build_html_adding("add-job" + i + "task" + j, task))
                    check_for_task_child_conflicts(task.name, work.tasks, "add-job" + i + "task" + j)
                })
            } else if (work.type == "task") {
                $("#add-container").append(build_html_adding("add-task" + i, work))
                check_for_task_conflicts(work.name, "add-task" + i)
            }
        });

        $('[data-toggle="tooltip"]').tooltip();
        
        if ($(".fa-times-circle-o").length == 0) {
            startAdd()
        }
    }
    
    $cant_close = 0
    function closeModal() {
        if ($cant_close)
            return
            
        $('#addTaskModal').modal('hide');
    }
    
    /***
     * Try to add a job
     ***/
    function createJobRequest(job) {
        // Start serializing the object
        form = "name=" + job.name
        
        fields = ["description", "image", "command", "entrypoint",
                  "cron", "exitcodes", "max_failures", "delay", "faildelay"]

        // Only add the fields that are filled in and not disbled
        for (var i=0; i < fields.length; i++) {
            field = fields[i]
            if (typeof(job[field]) == "undefined")
                continue
            else
                form += "&" + field + "=" + job[field]
        }
        
        form += "&state=stopped";
        
        if (typeof(job["restartable"]) != "undefined")
            form += "&restartable=" + job["restartable"]
        
        // Add each environment variable to the request string
        $.each(job.environment, function(env_key, env_value) {
            if (env_value != "")
                form += "&environment=" + env_key + "=" + env_value;
        });
        
        // Add each data volume to the request string
        $.each(job.datavolumes, function(dvl_key, dvl_value) {
            if (dvl_key != "" && dvl_value != "")
                form += "&datavolumes=" + dvl_key + ":" + dvl_value;
        });

        return form
    }
    
    /***
     * Try to add a task
     ***/
    function createTaskRequest(task) {
        // Start serializing the object
        
        form = "name=" + encodeURIComponent(task.name)
        
        if (typeof(task.parent_job) != 'undefined')
            form += "&parent_job=" + encodeURIComponent(task.parent_job)
        
        fields = ["description", "image", "command", "entrypoint",
                  "cron", "exitcodes", "max_failures", "delay", "faildelay"]

        // Only add the fields that are filled in and not disbled
        for (var i=0; i < fields.length; i++) {
            field = fields[i]
            if (typeof(task[field]) == "undefined")
                continue
            else
                form += "&" + field + "=" + encodeURIComponent(task[field])
        }
        
        form += "&state=stopped";
        
        if (typeof(task["restartable"]) != "undefined")
            form += "&restartable=" + task["restartable"]
        
        // Add each environment variable to the request string
        $.each(task.environment, function(env_key, env_value) {
            if (env_value != "")
                form += "&environment=" + encodeURIComponent(env_key + "=" + env_value);
        });
        
        $.each(task.removed_parent_defaults, function(i, rpd) {
            form += "&removed_parent_defaults=" + encodeURIComponent(rpd);
        });
        
        // Add each data volume to the request string
        $.each(task.datavolumes, function(dvl_key, dvl_value) {
            if (dvl_key != "" && dvl_value != "")
                form += "&datavolumes=" + encodeURIComponent(dvl_key + ":" + dvl_value);
        });
         
        // Add each tag to the request string
        $.each(task.tags, function(i, tag) {
            form += "&tag=" + encodeURIComponent(tag);
        });
        
        // Add each dependencies to the request string
        $.each(task.dependencies, function(i, dep) {
            form += "&dependency=" + encodeURIComponent(dep);
        });
        
        return form
    }
    
    function startAdd() {
        if ($(".fa-times-circle-o").length > 0) {
            return
        }
        
        $("#back-btn").addClass("hidden")
        $("#close-btn").addClass("disabled")
        $cant_close = 1
        
        $("font span.fa").addClass("fa-spinner fa-spin").css({"color": ""});
        
        $.each($config_arr, function(i, work) {
            if (work.type == "job") {
                // Send the request
                var work_id = "add-job" + i
                $.get('add_job?' + createJobRequest(work), function(response) {
                    json = JSON.parse(response);
                    
                    if (typeof(json.error) != 'undefined') {
                        $("#status-" + work_id).addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin").css({"color": "red"});
                        add_tooltip("tooltip-" + work_id, json.error);
                        return true;
                    } else if (typeof(json.id) == 'undefined') {
                        $("#status-" + work_id).addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin").css({"color": "red"});
                        add_tooltip("tooltip-" + work_id, "The job did not return it's id");
                        return true;
                    }
                    
                    $("#status-" + work_id).addClass("fa-check-circle-o").removeClass("fa-spinner fa-spin").css({"color": "green"});
                    var parent_job = json.id
                    
                    $.each(work.tasks, function(j, task) {
                        task.parent_job = parent_job
                        $.get('add_task?' + createTaskRequest(task), function(child_response) {
                            var child_json = JSON.parse(child_response)
                            var child_work_id = "add-job" + i + "task" + j
                            
                            if (typeof(child_json.error) != 'undefined') {
                                $("#status-" + child_work_id).addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin").css({"color": "red"});
                                add_tooltip("tooltip-" + child_work_id, child_json.error);
                                return true;
                            } else if (typeof(child_json.id) == 'undefined') {
                                $("#status-" + child_work_id).addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin").css({"color": "red"});
                                add_tooltip("tooltip-" + child_work_id, "The task did not return it's id");
                                return true;
                            }
                            
                            $("#status-" + child_work_id).addClass("fa-check-circle-o").removeClass("fa-spinner fa-spin").css({"color": "green"});
                        });
                    })
                });
            } else if (work.type == "task") {
                $.get('add_task?' + createTaskRequest(work), function(response) {
                    var json = JSON.parse(response)
                    var work_id = "add-task" + i
                    
                    if (typeof(json.error) != 'undefined') {
                        $("#status-" + work_id).addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin").css({"color": "red"});
                        add_tooltip("tooltip-" + work_id, json.error);
                        return true;
                    } else if (typeof(json.id) == 'undefined') {
                        $("#status-" + work_id).addClass("fa-times-circle-o").removeClass("fa-spinner fa-spin").css({"color": "red"});
                        add_tooltip("tooltip-" + work_id, "The task did not return it's id");
                        return true;
                    }
                    
                    $("#status-" + work_id).addClass("fa-check-circle-o").removeClass("fa-spinner fa-spin").css({"color": "green"});
                });
            }
        });
        $("#close-btn").removeClass("disabled")
        $cant_close = 0
    }
    
</script>


<!-- https://github.com/jeremyfa/yaml.js -->
<script src="static/yaml.min.js"></script>

<div class="modal-header">
    <button type="button" class="close" onclick="closeModal()">&times;</button>
    <h4 class="modal-title">Bulk Add</h4>
</div>

<div id="modal-body" class="modal-body" style="text-align: center; position:static;">
    <span id="input_config" style="height: 100%">
        <textarea id="config" class="form-control" style="height: 98%; width:100%; resize: none;"></textarea>
        <label class="radio-inline"><input type="radio" id="json_format" name="configformat" value="JSON" checked>JSON</label>
        <label class="radio-inline"><input type="radio" id="yaml_format" name="configformat" value="YAML">YAML</label>
    </span>
    <span id="show_config" style="height: 100%" class="hidden">
        <div style="width: 100%; color: blue; cursor: default; margin-bottom: 1%; text-align: right;"><small onclick="expland_all()">[+] Expand All </small><small onclick="collapse_all()"> [-] Collapse All</small></div>
        <div id="panel-container"></div>
    </span>
    <span id="add_config" style="height: 100%" class="hidden">
        <div id="add-container"></div>
    </span>
</div>

<div class="modal-footer" style="width: 100%; text-align:center">
    <div class="pull-left">
        <button id="close-btn" type="button" class="btn btn-default" onclick="closeModal()">Close</button>
    </div>
    <div class="pull-right">
        <button id="back-btn" type="button" class="btn btn-default hidden" onclick="back()">Back</button>
        <button id="next-btn" type="button" class="btn btn-success" onclick="checkConfig()">Next</button>
        <button id="add-btn" type="button" class="btn btn-success hidden" onclick="addConfig()">Add</button>
    </div>
</div>