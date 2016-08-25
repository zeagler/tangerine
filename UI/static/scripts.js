var button_map = {}
button_map["running"]  = "btn btn-info task Running"
button_map["starting"] = "btn btn-info task Running"
button_map["ready"]    = "btn btn-primary task Ready"
button_map["queued"]   = "btn btn-warning task Queued"
button_map["waiting"]  = "btn btn-warning task Queued"
button_map["failed"]   = "btn btn-danger task Failed"
button_map["success"]  = "btn btn-success task Success"
button_map["stopped"]  = "btn task Stopped"
button_map["stopping"] = "btn task Stopped"

var findTasks = function() {
  return function findMatches(q, cb) {
    var matches, substringRegex;

    matches = [];

    // regex used to determine if a string contains the substring `q`
    substrRegex = new RegExp(q, 'i');

    // iterate through the pool of strings and for any string that
    // contains the substring `q`, add it to the `matches` array
    $.each($tasks, function(i, str) {
      if (str.state !== "disabled")
      if (substrRegex.test(str.name)) {
        matches.push(str.name);
      }
    });

    cb(matches);
  };
};

var add_more_handler = function(button) {
    if (button == "add-env") {
        split = " = "
        type = "env";
    } else if (button == "add-dvl") {
        split = " : "
        type = "dvl";
    } else if (button == "add-prt") {
        split = " : "
        type = "prt";
    }
    
    $("#" + type).append('<span class="form-inline col-sm-10 pull-right added '+type+'"><span class="pull-left" style="width: 100%">' +
                  '<input class="input form-control" style="width: 46%" type="text">' +
                  split +
                  '<input class="input form-control" style="width: 46%" type="text">' +
                  ' ' +
                  '<button class="btn btn-danger remove-this" >-</button>' +
                  '</span></span>');
    
    $('.remove-this').click(function(e) {
        e.preventDefault();
        $(this).parent().parent().remove();
    });
}

$(document).ready(function(e) {
    // Add type ahead for the search box
/*
    $('#find-task .typeahead').typeahead({
        hint: false,
        highlight: true,
        minLength: 1
    },
    {
        name: 'tasks',
        source: findTasks()
    });
*/
});

$(document).on('click', '#switch li', function (e) {
    show_state($(this).text());
});

// Clear the DOM whenever a modal is dismissed
$('#displayTaskModal, #addTaskModal, #updateTaskModal, #cloneTaskModal').on('hidden.bs.modal',function(e){
    $($(this).find('.modal-content')).html("")
});

// Auto expand description box
$(document)
    .one('focus.textarea', '.autoExpand', function() {
        this.baseScrollHeight = this.scrollHeight;
        this.maxRows = this.getAttribute('data-max-rows');
    })
    .on('input.textarea', '.autoExpand', function(){
        this.rows = 1
        rows = Math.ceil((this.scrollHeight - this.baseScrollHeight) / 36)+1;
        this.rows = (rows<this.maxRows) ? rows : this.maxRows;
    });

// refresh the tasks
function loadTasks() {
    $.get('get_tasks', function(data) {
        $tasks = JSON.parse(data);
        updated = "";
        for (var i = 0; i < $tasks.length; i++) {
            if ($tasks[i].state == "disabled" || $tasks[i].state == "disabling") continue

            updated +=
            '<button id="task" type="button" ' +
                     'class="'+button_map[$tasks[i].state]+' d-inline-block"' +
                     'onclick="displayTaskModal(\''+$tasks[i].id+'\')' +
            '">' + 
                '<p>'+$tasks[i].name+'</p>' +
            '</button>';
        }
        $('#tasks').html(updated)
        show_state($(".active")[1].textContent)
    });
}

function show_state(state) {
    var tasks = document.getElementsByClassName("task");
    var i = 0;
    
    if (state == "All")
        for (i=0; i<tasks.length; i++)
            tasks[i].style.display = '';
    else {
        for (i=0; i<tasks.length; i++)
            tasks[i].style.display = 'none';

        tasks = document.getElementsByClassName("task " + state);
        for (i=0; i<tasks.length; i++)
            tasks[i].style.display = '';
    }
}

function addTaskModal(id) {
    $('#add-task-modal-content').load("new_task_form", function(result) {
        $('#addTaskModal').modal('show');
    });
}

function updateTaskModal(id) {
    $('#update-task-modal-content').load("update_task_form?id=" + id, function() {
        $('#updateTaskModal').modal('show');
    });
}

function displayTaskModal(id) {
    $('#display-task-modal-content').load("display_task?id=" + id, function() {
        $('#displayTaskModal').modal('show');
    });
}

function cloneTask(id) {
    $('#clone-task-modal-content').load("update_task_form?id=" + id + "&clone=true", function() {
        $('#cloneTaskModal').modal('show');
    });
}