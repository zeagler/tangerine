states = ["success", "failed", "running", "ready", "queued"];
enabled = [true, true, true, true, true];

function toggle_visibility(state) {
    // Check if everything is enabled
    if (enabled[0] && enabled[1] && enabled[2] && enabled[3] && enabled[4]) {
        disable_everything()
        enable_state(state)

    // Check if this toggle is being turned off
    } else if (enabled[states.indexOf(state)]) {
      
        // Check if that will turn all states off
        enabled[states.indexOf(state)] = false;
        if (!(enabled[0] || enabled[1] || enabled[2] || enabled[3] || enabled[4])) {
            enable_everything()
            
        // Just disable the state
        } else {
            disable_state(state)
        }
    
    // Just enable the state
    } else {
        enable_state(state)
    }
}

function disable_state(state) {
    var tasks = document.getElementsByClassName("task " + state);
    var buttons = document.getElementsByClassName("button "  + state);
    
    enabled[states.indexOf(state)] = false;
    buttons[0].style.backgroundColor = "forestgreen";
    for (var i=0; i<tasks.length; i++) tasks[i].style.display = 'none';
}

function enable_state(state) {
    var tasks = document.getElementsByClassName("task " + state);
    var buttons = document.getElementsByClassName("button "  + state);
    
    enabled[states.indexOf(state)] = true;
    buttons[0].style.backgroundColor = "initial";
    for (var i=0; i<tasks.length; i++) tasks[i].style.display = '';
}

function disable_everything() {
    for (var i=0; i<states.length; i++)
        disable_state(states[i])
}

function enable_everything() {
    for (var i=0; i<states.length; i++)
        enable_state(states[i])
}

function successAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str) {
    nextrun = ""; dependent = "";
    if (dependencies != "") dependent = "Dependencies: " + dependencies + "</br>"
    if (next_run_str != "") nextrun = "Next run: " + next_run_str + "</br>"

    swal({
      title: name,
      type: 'success',
      html:
        "State: Success<br>" +
        'Image: ' + imageuuid + "</br>" +
        dependent + nextrun,
      showCancelButton: 'true',
      cancelButtonText: 'Close',
      confirmButtonText: 'Misfire',
      reverseButtons: 'true',
    }).then(function(result) {
      updateTask(name, "state", "queued")
    }).done();
}

function failedAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str) {
    // add last failed time
    dependent = ""
    if (dependencies != "") dependent = "Dependencies: " + dependencies + "</br>"
    failed = failures + '/' + max_failures + " failures"
    
    swal({
      title: name,
      type: 'error',
      html:
        "State: Failed<br>" +
        'Image: ' + imageuuid + "</br>" +
        dependent +
        failed,
      showCancelButton: 'true',
      cancelButtonText: 'Close',
      confirmButtonText: 'Misfire',
      reverseButtons: 'true',
    }).then(function(result) {
      updateTask(name, "state", "queued")
    }).done();
}

function queuedAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str, state="Queued") {
    dependent = ""; failed = ""
    if (dependencies != "") dependent = "Dependencies: " + dependencies + "</br>"
    if (failures > 0) failed = failures + '/' + max_failures + " failures";
    
    swal({
      title: name,
      type: 'info',
      html:
        "State: " + state + "<br>" +
        'Image: ' + imageuuid + "</br>" +
        dependent +
        failed,
      showCancelButton: 'true',
      cancelButtonText: 'Close',
      confirmButtonText: 'Stop',
      reverseButtons: 'true',
    }).then(function(result) {
      updateTask(name, "state", "stopped")
    }).done();
}

function readyAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str) {
    queuedAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str, "Ready")
}

function runningAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str) {
    // add last run time
    queuedAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str, "Running")
}

function stoppingAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str) {
    swal({
      title: name,
      type: 'warning',
      html: "State: Stopping",
      confirmButtonText: 'Close',
    })
}

function stoppedAlert(name, imageuuid, dependencies, failures, max_failures, next_run_str) {
    dependent = ""; failed = ""
    if (dependencies != "") dependent = "Dependencies: " + dependencies + "</br>"
    if (failures > 0) failed = failures + '/' + max_failures + " failures";
    
    swal({
      title: name,
      type: 'warning',
      html:
        "State: Stopped<br>" +
        'Image: ' + imageuuid + "</br>" +
        dependent +
        failed,
      showCancelButton: 'true',
      cancelButtonText: 'Close',
      confirmButtonText: 'Misfire',
      reverseButtons: 'true',
    }).then(function(result) {
      updateTask(name, "state", "queued")
    }).done();
}

function addTask() {
  swal({
    title: 'Add a task',
    showCancelButton: 'true',
    confirmButtonText: 'Add',
    reverseButtons: 'true',
    html:
      '<table align="center" cellpadding="5" cellspacing="0" height="88" style="border-collapse:collapse;">' +
        '<tbody>' +
           '<tr><td style="text-align: right;">Name<span style="color: red;">*</span></td><td><input id="swal-name" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;">State</td><td><select id="swal-state"><option selected="selected" value="queued">queued</option><option value="success">success</option><option value="stopped">stopped</option></select></td></tr>' +
           '<tr><td style="text-align: right;">Dependencies</td><td><input id="swal-dep" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;">Image<span style="color: red;">*</span></td><td><input id="swal-image" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;">Command</td><td><input id="swal-command" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;">Entrypoint</td><td><input id="swal-entrypoint" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;">Environment</td><td><input id="swal-environment" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;">Data Volumes</td><td><input id="swal-datavolumes" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;">Cron</td><td><input id="swal-cron" type="text" /></td></tr>' +
           '<tr><td style="text-align: right;"></td><td><input checked="checked" id="swal-restartable" type="checkbox">Restartable</input></td></tr>' +    
           '<tr><td style="text-align: right;">Recoverable Exit Codes</td><td><input id="swal-exitcodes" type="text" value="0" /></td></tr>' +
           '<tr><td style="text-align: right;">Max Failures</td><td><input id="swal-failures" type="text" value="3" /></td></tr>' +
           '<tr><td style="text-align: right;">Inital Delay</td><td><input id="swal-delay" type="text" value="0" /></td></tr>' +
           '<tr><td style="text-align: right;">Delay After Failure (min)</td><td><input id="swal-fail-delay" type="text" value="5" /></td></tr>' +
        '</tbody>' +
      '</table>' +
      '<p style="color: red; margin-bottom: 0px; margin-top: 10px; line-height: 0; font-size: 75%;">* Required</p>',
    preConfirm: function() {
      return new Promise(function(resolve) {
          resolve([
            $('#swal-name').val(),
            $('#swal-state').val(),
            $('#swal-dep').val(),
            $('#swal-image').val(),
            $('#swal-command').val(),
            $('#swal-entrypoint').val(),
            $('#swal-cron').val(),
            $('#swal-restartable').is(":checked"),
            $('#swal-exitcodes').val(),
            $('#swal-failures').val(),
            $('#swal-delay').val(),
            $('#swal-fail-delay').val(),
            $('#swal-environment').val(),
            $('#swal-datavolumes').val()
          ]);
      });
    }
  }).then(function(result) {
    res = JSON.stringify(result);

    xhttp = new XMLHttpRequest();
    xhttp.open("GET", "add_task?" +
                        "name=" + result[0] +
                        "&state=" + result[1] +
                        "&dep=" + result[2] +
                        "&image=" + result[3] +
                        "&command=" + result[4] +
                        "&entrypoint=" + result[5] +
                        "&cron=" + result[6] +
                        "&restartable=" + result[7] +
                        "&exitcodes=" + result[8] +
                        "&max_failures=" + result[9] +
                        "&delay=" + result[10] +
                        "&faildelay=" + result[11] +
                        "&environment=" + result[12] +
                        "&datavolumes=" + result[13]
                    , true);
    xhttp.send();
  }).done();
}

function updateTask(name, column, value) {
    xhttp = new XMLHttpRequest();
    xhttp.open("GET", "update?name="+name+"&column="+column+"&value="+value, true);
    xhttp.send();
}