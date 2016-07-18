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

function displayTask(name, state, imageuuid, dependencies, cron, failures, max_failures) {
    cronjob = ""; dependent = ""; failed = "";
    if (dependencies != "") dependent = "Dependencies: " + dependencies + "</br>"
    if (cron != "") cronjob = "Cron: [" + cron + "]</br>"
  
    switch (state) {
        case "success":
            type = "success";
            break;
        case "failed": 
            type = "error";
            failed = failures + '/' + max_failures + " failures";
            break;
        default:
            type="info";
            if (failures > 0) failed = failures + '/' + max_failures + " failures";
    }
    
 
    swal({
      title: name,
      type: type,
      html:
        'State: ' + state + "<br>" +
        'Image: ' + imageuuid + "</br>" +
        dependent + cronjob +
        failed,
      showCloseButton: true,
      confirmButtonText:
        '<i class="fa fa-thumbs-up"></i> Close'
    })
}