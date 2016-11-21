<script>
    /***
     * "Pre"-validation
     *
     * Ensure fields are proper while filling out the form, present the user
     *   with a visual error if there is a problem with the input
     ***/
    $("#name,#image").focusout(function() {
        if ($(this)[0].name == "image" && $("#parent_job").val() != "NULL") return

        if ($(this).val() == "") {
            $(this).parent().addClass("has-error");
            $(this).tooltip('enable')
            $(this).tooltip('show');
        }
    }).on('input',function(e){
        if ($(this).val() == "") {
            if ($(this)[0].name == "image" && $("#parent_job").val() != "NULL") return
            
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
        
        document.getElementById('add_task_form').reset();
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
     * Enable typeahead and use the tasks from the main page as the datasource
     ***/
    $('[data-toggle="tooltip"]').tooltip();
    $("#name,#image").tooltip('disable');
    $("#err_alert").hide()
    $('#add-dep').pillbox();
    
    // Add type ahead for dependencies
    $('#find-dep .typeahead').typeahead({
        hint: false,
        highlight: true,
        minLength: 1
    },
    {
        name: 'tasks',
        source: findTasks()
    });

    // Add type ahead for dependencies
    $('#find-tag .typeahead').typeahead({
        hint: false,
        highlight: true,
        minLength: 1
    },
    {
        name: 'tasks',
        source: findTags()
    });
    
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
    
    /***
     * Try to add a task
     *
     * First do client side validatation of the request to ensure there are no errors
     * Then send the request to the the server which will return a success or error message.
     * If there is an error message present it to the user and allow them to correct the fields.
     * If the request succeeds close the modal to return the user to the overview display
     ***/
    function addTask(modal) {
        // Is the task name valid?
        if ($('#name').val() == "") {
            $(this).parent().addClass("has-error");
            $("#err_msg").html("<strong>Error</strong> Name cannot be blank")
            $("#err_alert").show()
            return
        } else if ($('#name').val().length > 100) {
            $(this).parent().addClass("has-error");
            $("#err_msg").html("<strong>Error</strong> Name must be 100 characters or less")
            $("#err_alert").show()
            return
        }
        
        
        // Is the image valid?
        if ($('#image').val() == "" && $("#parent_job").val() == "NULL") {
            $(this).parent().addClass("has-error");
            $("#err_msg").html("<strong>Error</strong> Image must be set")
            $("#err_alert").show()
            return
        }
        
        // Are the environment variables valid?
        
        // Are the data-volumes valid?
      
        // Start serializing the form with the name
        form = "name=" + encodeURIComponent($("#name").val())
        
        if ($("#parent_job").val() != "NULL")
            form += "&parent_job=" + encodeURIComponent($("#parent_job").val())
        
        fields = ["description", "image", "command", "entrypoint",
                  "state", "cron", "exitcodes", "max_failures", "delay", "faildelay"]

        // Only add the fields that are filled in and not disbled
        for (var i=0; i < fields.length; i++) {
            field = fields[i]
            if ($("#" + field).val() == "" || $("#" + field).prop("disabled"))
                continue
            else
                form += "&" + field + "=" + encodeURIComponent($("#" + field).val())
        }
        
        form += "&restartable=" + $('#restartable')[0].checked
        
        // Add each environment variable to the request string
        $('.env').each(function(i, obj) {
            if ($(obj).find("input")[0].value !== "") {
                form += "&environment=" + encodeURIComponent($(obj).find("input")[0].value + "=" + $(obj).find("input")[1].value);
            }
        });
        $('.job_env').each(function(i, obj) {
            if ($(obj).find("input")[1].value !== "") {
                form += "&environment=" + encodeURIComponent($(obj).find("input")[0].value + "=" + $(obj).find("input")[1].value);
            }
        });
        $('.removed-default.job_env').each(function(i, obj) {
            form += "&removed_parent_defaults=" + encodeURIComponent($(obj).find("input")[0].value);
        });
        
        // Add each data volume to the request string
        $('.dvl').each(function(i, obj) {
            if ($(obj).find("input")[0].value !== "" && $(obj).find("input")[1] !== "") {
                form += "&datavolumes=" + encodeURIComponent($(obj).find("input")[0].value) + ":" + encodeURIComponent($(obj).find("input")[1].value);
            }
        });
        $('.job_dvl').each(function(i, obj) {
            if ($(obj).find("input")[0].value !== "") {
                form += "&datavolumes=" + encodeURIComponent($(obj).find("input")[0].value) + ":" + encodeURIComponent($(obj).find("input")[1].value);
            }
        });
        $('.removed-default.job_dvl').each(function(i, obj) {
            form += "&removed_parent_defaults=" + encodeURIComponent($(obj).find("input")[1].value);
        });
                
        // Add each tag to the request string
        $.each($('#add-tag').pillbox('items'), function(i, tag) {
            form += "&tag=" + encodeURIComponent(tag.value);
        });
        
        // Add each dependencies to the request string
        $.each($('#add-dep').pillbox('items'), function(i, dep) {
            form += "&dependency=" + encodeURIComponent(dep.value);
        });
        
        // Send the request
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "add_task?" + form, true);
        xhttp.send();
        
        // TODO: Check the return value to see if we succeeded
        //       If the JSON response shows an error alert the user
        //         do not close the modal if an error occurs
        $('#'+modal).modal('hide');
        loadTasks()
    }
    
    function set_defaults(job_id) {
        $(".job_env").remove()
        $(".job_dvl").remove()
    
        if (job_id == "undefined" || job_id == "") {
            $("#image").attr("placeholder", "")
            $("#command").attr("placeholder", "")
            $("#entrypoint").attr("placeholder", "")
            $("#exitcodes").attr("placeholder", "")
            $("#delay").attr("placeholder", "0")
            $("#max_failures").attr("placeholder", "3")
            $("#faildelay").attr("placeholder", "5")
            return
        } else {
            job = findJob(job_id)

            if (job == "undefined" || job == null) {
                return
            } else {
                for (var i=0; i<job.environment.length; i++) {
                    env = job.environment[i]
                    $("#environment").append('<span class="form-inline col-sm-10 pull-right added job_env"><span class="pull-left" style="width: 100%">' +
                                              '<input class="input form-control" disabled style="width: 46%" type="text" value="' + env[0] + '">' +
                                              " = " +
                                              '<input class="input form-control" style="width: 46%" type="text" placeholder="' + env[1] + '">' +
                                              ' ' +
                                              '<button class="btn btn-danger toggle-job-default" >-</button>' +
                                              '</span></span>');
                }
                
                for (var i=0; i<job.datavolumes.length; i++) {
                    dvl = job.datavolumes[i].split(":")
                    $("#datavolumes").append('<span class="form-inline col-sm-10 pull-right added job_dvl"><span class="pull-left" style="width: 100%">' +
                                              '<input class="input form-control" style="width: 46%" type="text" placeholder="' + dvl[0] + '">' +
                                              " : " +
                                              '<input class="input form-control" disabled style="width: 46%" type="text" value="' + dvl[1] + '">' +
                                              ' ' +
                                              '<button class="btn btn-danger toggle-job-default" >-</button>' +
                                              '</span></span>');
                }
                
                $(".toggle-job-default").off('click').on('click', function(e) {
                    e.preventDefault();
                    
                    var state
                    
                    if ($(this).parent().parent().css('opacity') == "0.6") {
                        // enable this default
                        state = "enabled"
                        $(this).parent().parent().css({'opacity' : 1.0});
                        $(this).parent().parent().removeAttr("data-toggle");
                        $(this).parent().parent().removeAttr("data-placement");
                        $(this).parent().parent().removeAttr("title");
                        $(this).parent().parent().tooltip('disable');
                        $(this).addClass("btn-danger").removeClass("btn-primary");
                        $(this).parent().parent().removeClass("removed-default");
                        $(this).html("-");
                    } else {
                        // disable this default
                        state = "disabled"
                        $(this).parent().parent().css({'opacity' : 0.6});
                        $(this).parent().parent().attr("data-toggle", "tooltip");
                        $(this).parent().parent().attr("data-placement", "top");
                        $(this).parent().parent().attr("title", "The task will ignore this inherited default");
                        $(this).parent().parent().tooltip('enable');
                        $(this).addClass("btn-primary").removeClass("btn-danger");
                        $(this).parent().parent().addClass("removed-default");
                        $(this).html("+");
                    }

                    if ($(this).parent().parent().attr("class").split(" ").indexOf("job_env") >= 0) {
                        if (state == "disabled") {
                            $(this).parent().parent().find("input")[1].value = "";
                            $(this).parent().parent().find("input")[1].disabled = true;
                        } else {
                            $(this).parent().parent().find("input")[1].disabled = false;
                        }
                    } else if ($(this).parent().parent().attr("class").split(" ").indexOf("job_dvl") >= 0) {
                        if (state == "disabled") {
                            $(this).parent().parent().find("input")[0].value = "";
                            $(this).parent().parent().find("input")[0].disabled = true;
                        } else {
                            $(this).parent().parent().find("input")[0].disabled = false;
                        }
                    }
                });
                
                $("#image").attr("placeholder", job.imageuuid)
                $("#command").attr("placeholder", job.command_raw)
                $("#entrypoint").attr("placeholder", job.entrypoint_raw)
                $("#exitcodes").attr("placeholder", job.recoverable_exitcodes)
                $("#delay").attr("placeholder", job.delay)
                $("#max_failures").attr("placeholder", job.max_failures)
                $("#faildelay").attr("placeholder", job.reschedule_delay)
                
                $("#image").parent().removeClass("has-error");
                $("#image").tooltip('disable');
                $("#image").tooltip('hide');
                $("#err_alert").hide()
            }
        }
    }
    
    $("#parent_job").change(function() {
        if ($("#parent_job").val() == "NULL") {
            $("#cron").prop('disabled', false);
            $("#cron").val($("#parent_job option:selected").attr("cron"))
            set_defaults("")
        } else {
            $("#cron").prop('disabled', true);
            $("#cron").val($("#parent_job option:selected").attr("cron") + " - Task will follow the parent job's schedule (" + $("#parent_job option:selected").text() + ")")
            set_defaults($("#parent_job").val())
        }
    });
    
    // Load the parent job combobox
    var parent_job = $("#parent_job");
    parent_job.append($("<option />").val("NULL").text("No Parent").attr('cron', ""));
    $.each(findJobs(), function() {
        cron = this.cron
        if (cron == 'undefined') cron = "None"
        parent_job.append($("<option />").val(this.id).text(this.name).attr('cron', cron));
    });
    
</script>












<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal">&times;</button>
    <h4 class="modal-title">Add a Task</h4>
</div>

<div id="add-task-modal-body" class="modal-body" style="text-align: center;">
    <div id="err_alert" class="alert alert-danger fade in" role="alert">
        <div id="err_msg"></div>
    </div>
    <form class="form-horizontal" id="add_task_form" role="form" autocomplete="off">
        <div class="form-group">
            <div class="col-sm-4">
                <input class="form-control" id="name" name="name" placeholder="Name" type="text" data-toggle="tooltip" data-placement="bottom" title="Name cannot be blank">
            </div>
            
            <div class="col-sm-3">
                <select class="form-control" id="parent_job" name="parent_job">
                </select>
            </div>
            
            <div class="col-sm-5">
              <textarea class="form-control autoExpand" id="description" name="description" rows='1' data-max-rows='3' placeholder="Description" style="overflow-x:hidden; resize: none;"></textarea>
            </div>
        </div>
        <ul id="task_switch" class="nav nav-tabs nav-justified" style="padding-bottom: 10px">
            <li class="active"><a href="#container" data-toggle="tab">Container</a></li>
            <li><a href="#env-pane" data-toggle="tab">Environment</a></li>
            <li><a href="#sch" data-toggle="tab">Scheduling</a></li>
            <li><a href="#restart" data-toggle="tab">Restart</a></li>
        </ul>
        <div class="tab-content">
            <div class="tab-pane active" id="container">
                <div class="form-group">
                    <label class="control-label col-sm-2">
                        Image <span class="glyphicon glyphicon-question-sign" style="color: lightgrey" data-toggle="tooltip" data-placement="top" title="The images this task will be ran on. You can use `image` or `image:tag`"></span>
                    </label>
                    <div class="col-sm-10"><input class="form-control" id="image" name="image" data-toggle="tooltip" data-placement="bottom" title="Image cannot be blank"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Command</label>
                    <div class="col-sm-10"><input class="form-control" id="command" name="command"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Entrypoint</label>
                    <div class="col-sm-10"><input class="form-control" id="entrypoint" name="entrypoint"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2 disabled">Working Dir</label>
                    <div class="col-sm-10"><input class="form-control" disabled id="wdr" name="wdr"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2 disabled">User</label>
                    <div class="col-sm-10"><input class="form-control" disabled id="usr" name="usr"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Console</label>
                    <div class="col-sm-10"><input class="form-control" disabled id="csl" name="csl"></div>
                </div>
            </div>
            <div class="tab-pane" id="env-pane">
                <div class="form-group">
                    <span class="col-sm-2">
                        <label class="control-label">Environment</label>
                        <button id="add-env" class="center-block img-circle btn btn-primary btn-add-glyphicon add-more">
                            <span class="glyphicon glyphicon-plus"></span>
                        </button>
                    </span>
                    <div id="environment">
                        <span class="form-inline col-sm-10 pull-right added env"><span class="pull-left" style="width: 100%">
                            <input class="input form-control" style="width: 46%" type="text">
                            <span> = </span>
                            <input class="input form-control" style="width: 46%" type="text">
                            <span> </span>
                            <button class="btn btn-danger remove-this" >-</button>
                        </span></span>
                    </div>
                </div>
                <div class="form-group">
                    <span class="col-sm-2">
                        <label class="control-label">Data Volumes</label>
                        <button id="add-dvl" class="center-block img-circle btn btn-primary btn-add-glyphicon add-more">
                            <span class="glyphicon glyphicon-plus"></span>
                        </button>
                    </span>
                    <div id="datavolumes">
                        <span class="form-inline col-sm-10 pull-right added dvl"><span class="pull-left" style="width: 100%">
                            <input class="input form-control" style="width: 46%" type="text">
                            <span> : </span>
                            <input class="input form-control" style="width: 46%" type="text">
                            <span> </span>
                            <button class="btn btn-danger remove-this" >-</button>
                        </span></span>
                    </div>
                </div>
                <div class="form-group disabled">
                    <span class="col-sm-2">
                        <label class="control-label">Exposed Ports</label>
                        <button id="add-prt" class="disabled center-block img-circle btn btn-primary btn-add-glyphicon add-more">
                            <span class="glyphicon glyphicon-plus"></span>
                        </button>
                    </span>
                    <div id="prt">
                        <span class="form-inline col-sm-5 pull-left added prt"><span class="pull-left" style="width: 100%">
                            <input class="disabled input form-control" style="width: 40%" type="text">
                            <span> : </span>
                            <input class="disabled input form-control" style="width: 40%" type="text">
                            <span> </span>
                            <button class="disabled btn btn-danger remove-this" >-</button>
                        </span></span>
                    </div>
                </div>
            </div>
            <div class="tab-pane" id="sch">
                <div class="form-group">
                    <label class="control-label col-sm-2">State</label>
                    <div class="col-sm-10">
                        <select class="form-control radio-inline" id="state" name="state" style="display: inline-block;" placeholder="queued">
                            <option value="queued">queue to run now</option>
                            <option value="waiting">wait until next cron time</option>
                            <option value="stopped">disable until user intervention</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label class="control-label col-sm-2">Cron</label>
                    <div class="col-sm-10"><input class="form-control" id="cron" name="cron"></div>
                </div>

                <div class="form-group fuelux">
                    <label class="control-label col-sm-2">Tags<span class="glyphicon glyphicon-question-sign" style="color: lightgrey" data-toggle="tooltip" data-placement="top" title="Start typing to find existing tags or create a new one. *You must press enter to create a pillbox for each tag*"></span></label>
                    <div class="col-sm-10 pillbox pull-right" data-initialize="pillbox" id="add-tag">
                        <ul class="clearfix pill-group">
                            <li class="pillbox-input-wrap btn-group" id="find-tag">
                                <input type="text" class="form-control typeahead pillbox-add-item" style="min-width: 240px;" placeholder="start typing to find tags">
                            </li>
                        </ul>
                    </div>
                </div>
                
                <div class="form-group fuelux">
                    <label class="control-label col-sm-2">Dependencies<span class="glyphicon glyphicon-question-sign" style="color: lightgrey" data-toggle="tooltip" data-placement="top" title="Start typing to find tasks. Only tasks that are inside the parent job will be displayed. *You must press enter to create a pillbox for each dependency*"></span></label>
                    <div class="col-sm-10 pillbox pull-right" data-initialize="pillbox" id="add-dep">
                        <ul class="clearfix pill-group">
                            <li class="pillbox-input-wrap btn-group" id="find-dep">
                                <input type="text" class="form-control typeahead pillbox-add-item" style="min-width: 240px;" placeholder="start typing to find dependencies">
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
            <div class="tab-pane" id="restart">
                <div class="form-group">
                    <input type="checkbox" class="checkbox-inline" id="restartable" checked="true">
                    <label class="control-label">Restartable</label>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Recoverable Exit Codes</label>
                    <div class="col-sm-10"><input class="form-control" id="exitcodes" name="exitcodes" placeholder="" value="""></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Max Failures</label>
                    <div class="col-sm-10"><input class="form-control" id="max_failures" name="max_failures" placeholder="3" value=""></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Inital Delay (seconds)</label>
                    <div class="col-sm-10"><input class="form-control" id="delay" name="delay" placeholder="0" value=""></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Delay After Failure (seconds)</label>
                    <div class="col-sm-10"><input class="form-control" id="faildelay" name="faildelay" placeholder="5" value=""></div>
                </div>
            </div>
        </div>
    </form>
</div>

<div class="modal-footer" style="width: 100%; text-align:center">
    <button type="button" class="btn btn-default pull-left" style="width: 100px;" data-dismiss="modal">Close</button>
    <button type="button" class="btn btn-default pull-left reset-form" style="width: 100px;">Clear</button>
    <button type="button" class="btn btn-primary pull-right" style="width: 100px;" onclick="addTask('addTaskModal')">Add</button>
</div>