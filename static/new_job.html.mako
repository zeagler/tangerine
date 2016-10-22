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
    
    /***
     * Try to add a job
     *
     * First do client side validatation of the request to ensure there are no errors
     * Then send the request to the the server which will return a success or error message.
     * If there is an error message present it to the user and allow them to correct the fields.
     * If the request succeeds close the modal to return the user to the overview display
     ***/
    function addJob(modal) {
        // Is the job name valid?
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
        if ($('#image').val() == "") {
            $(this).parent().addClass("has-error");
            $("#err_msg").html("<strong>Error</strong> Image must be set")
            $("#err_alert").show()
            return
        }
        
        // Are the environment variables valid?
        
        // Are the data-volumes valid?
      
        // Serialize the form to get a request string
        form = $("#add_job_form").serialize()
          
        // Add the restart value to the request string
        form += "&restartable=" + $('#restartable')[0].checked
        
        // Add each environment variable to the request string
        $('.env').each(function(i, obj) {
            if ($(obj).find("input")[0].value !== "") {
                form += "&environment=" + $(obj).find("input")[0].value + "=" + $(obj).find("input")[1].value;
            }
        });
        
        // Add each data volume to the request string
        $('.dvl').each(function(i, obj) {
            if ($(obj).find("input")[0].value !== "" && $(obj).find("input")[1] !== "") {
                form += "&datavolumes=" + $(obj).find("input")[0].value + ":" + $(obj).find("input")[1].value;
            }
        });
        
        // Send the request
        xhttp = new XMLHttpRequest();
        xhttp.open("GET", "add_job?" + form, true);
        xhttp.send();
        
        // TODO: Check the return value to see if we succeeded
        //       If the JSON response shows an error alert the user
        //         do not close the modal if an error occurs
        $('#'+modal).modal('hide');
    }
</script>












<div class="modal-header">
    <button type="button" class="close" data-dismiss="modal">&times;</button>
    <h4 class="modal-title">Add a Job</h4>
</div>

<div id="modal-body" class="modal-body" style="text-align: center;">
    <div id="err_alert" class="alert alert-danger fade in" role="alert">
        <div id="err_msg"></div>
    </div>
    <form class="form-horizontal" id="add_job_form" role="form" autocomplete="off">
        <div class="form-group">
            <div class="col-sm-6">
                <input class="form-control" id="name" name="name" placeholder="Name" type="text" data-toggle="tooltip" data-placement="bottom" title="Name cannot be blank">
            </div>

            <div class="col-sm-6">
              <textarea class="form-control autoExpand" name="description" rows='1' data-max-rows='3' placeholder="Description" style="overflow-x:hidden; resize: none;" value=""></textarea>
            </div>
        </div>
        <ul id="job_switch" class="nav nav-tabs nav-justified" style="padding-bottom: 10px">
            <li class="active"><a href="#container" data-toggle="tab">Container</a></li>
            <li><a href="#env-pane" data-toggle="tab">Environment</a></li>
            <li><a href="#sch" data-toggle="tab">Scheduling</a></li>
            <li><a href="#restart" data-toggle="tab">Restart</a></li>
        </ul>
        <div class="tab-content">
            <div class="tab-pane active" id="container">
                <div class="form-group">
                    <label class="control-label col-sm-2">
                        Image <span class="glyphicon glyphicon-question-sign" style="color: lightgrey" data-toggle="tooltip" data-placement="top" title="The image that all tasks within this job will be ran with. You can use `image` or `image:tag`"></span>
                    </label>
                    <div class="col-sm-10"><input class="form-control" id="image" name="image" data-toggle="tooltip" data-placement="bottom" title="Image cannot be blank"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Command</label>
                    <div class="col-sm-10"><input class="form-control" name="command" value=""></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Entrypoint</label>
                    <div class="col-sm-10"><input class="form-control" name="entrypoint" value=""></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2 disabled">Working Dir</label>
                    <div class="col-sm-10"><input class="form-control" disabled name="wdr" value=""></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2 disabled">User</label>
                    <div class="col-sm-10"><input class="form-control" disabled name="usr" value=""></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Console</label>
                    <div class="col-sm-10"><input class="form-control" disabled name="csl" value=""></div>
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
                                <input class="input form-control" style="width: 46%" type="text" value="">
                                <span> = </span>
                                <input class="input form-control" style="width: 46%" type="text" value="">
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
                                <input class="input form-control" style="width: 46%" type="text" value="">
                                <span> : </span>
                                <input class="input form-control" style="width: 46%" type="text" value="">
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
                    <div id="port">
                        <span class="form-inline col-sm-5 pull-left added port"><span class="pull-left" style="width: 100%">
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
                            <option value="running">queue to run now</option>
                            <option value="waiting">wait until next cron time</option>
                            <option value="stopped">disable until user intervention</option>
                        </select>
                    </div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Cron</label>
                    <div class="col-sm-10"><input class="form-control" name="cron" value=""></div>
                </div>
            </div>
            <div class="tab-pane" id="restart">
                <div class="form-group">
                    <input type="checkbox" class="checkbox-inline" id="restartable" checked="true">
                    <label class="control-label">Restartable</label>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Recoverable Exit Codes</label>
                    <div class="col-sm-10"><input class="form-control" name="exitcodes" value="0"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Max Failures</label>
                    <div class="col-sm-10"><input class="form-control" name="max_failures" value="3"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Inital Delay (seconds)</label>
                    <div class="col-sm-10"><input class="form-control" name="delay" value="0"></div>
                </div>
                <div class="form-group">
                    <label class="control-label col-sm-2">Delay After Failure (seconds)</label>
                    <div class="col-sm-10"><input class="form-control" name="faildelay" value="5"></div>
                </div>
            </div>
        </div>
    </form>
</div>

<div class="modal-footer" style="width: 100%; text-align:center">
    <button type="button" class="btn btn-default pull-left" style="width: 100px;" data-dismiss="modal">Close</button>
    <button type="button" class="btn btn-default pull-left reset-form" style="width: 100px;">Clear</button>
    <button type="button" class="btn btn-primary pull-right" style="width: 100px;" onclick="addJob('addTaskModal')">Add</button>
</div>