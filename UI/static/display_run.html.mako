        <div class="modal-header">
            <button type="button" class="close" data-dismiss="modal">&times;</button>
            <h4 class="modal-title">${run.name}</h4>
        </div>

        <div class="modal-body" style="height: 60%; overflow: auto;">
            <ul id="run_switch" class="nav nav-tabs nav-justified" style="padding-bottom: 10px">
                <li class="active"><a href="#details" data-toggle="tab">Details</a></li>
                <li><a href="#metrics" data-toggle="tab">Metrics</a></li>
                <li><a href="#log" data-toggle="tab">Log</a></li>
            </ul>
            
            <div class="tab-content">
                <div class="tab-pane active" id="details">
                    <dl class="dl-horizontal pull-left">
                        <dt>Start: </dt><dd>${run.run_start_time_str}</dd>
                        <dt>Finish: </dt><dd>${run.run_finish_time_str}</dd>
                        <dt>Time Elapsed: </dt><dd>${run.elapsed_time}</dd>
                        <dt>Result: </dt><dd>${run.result_state}</dd>
                        <dt>Max Memory: </dt><dd>${run.max_memory}</dd>
                        <dt>Max CPU: </dt><dd>${run.max_cpu}</dd>
                        </br>
                        </br>
                        <dt>Run ID </dt><dd>${run.run_id}</dd>
                        <dt>Task </dt><dd>${run.name}</dd>
                        <dt>Description</dt><dd>${run.description}</dd>
                        <dt>Image </dt><dd>${run.imageuuid}</dd>
                        <dt>Command </dt><dd>${run.command}</dd>
                        <dt>Entrypoint </dt><dd>${run.entrypoint}</dd>
                        <dt>Working Dir </dt><dd></dd>
                        <dt>User </dt><dd></dd>
                        <dt>Console </dt><dd></dd>
                    </dl>
                </div>
                <div class="tab-pane" id="metrics">
                    <label for = "memory" style="height: 40%; width: 100%">
                        Memory<br />
                        <canvas id="memory"></canvas>
                    </label>
                    
                    <label for = "cpu" style="height: 40%; width: 100%">
                        CPU<br />
                    <canvas id="cpu"></canvas>
                    </label>
                </div>
                <div class="tab-pane" id="log">
                    <p>WIP</p>
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button type="button" class="btn btn-default" + data-dismiss="modal">Close</button>
        </div>
        
        <script>

        var ctx_mem = document.getElementById("memory");
        var ctx_cpu = document.getElementById("cpu");
        
        var memory = new Chart(ctx_mem, {
            type: 'line',
            data: {
                labels: ${[i for i in range(0, len(run.memory_history))]},
                datasets: [{
                    backgroundColor: 'rgba(255, 99, 132, 0.2)',
                    data: ${run.memory_history},
                    borderWidth: 1,
                    pointRadius: 0
                }]
            },
            animation:false,
            options:
            {
                maintainAspectRatio: false,
                legend: {
                  display: false
                },
                scales:
                {
                    xAxes: [{
                        display: false
                    }],
                    yAxes: [{
                        scaleOverride:true,
                        scaleSteps:9,
                        scaleStartValue:0,
                        scaleStepWidth:100,
                        gridLines: {
                            display:false
                        }   
                    }]
                }
            }
        });
        
        var cpu = new Chart(ctx_cpu, {
            type: 'line',
            data: {
                labels: ${[i for i in range(0, len(run.cpu_history))]},
                datasets: [{
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    data: ${run.cpu_history},
                    borderWidth: 1,
                    pointRadius: 0
                }]
            },
            animation:false,
            options:
            {
                maintainAspectRatio: false,
                legend: {
                  display: false
                },
                scales:
                {
                    xAxes: [{
                        display: false
                    }],
                    yAxes: [{
                        scaleOverride:true,
                        scaleSteps:9,
                        scaleStartValue:0,
                        scaleStepWidth:100,
                        gridLines: {
                            display:false
                        }   
                    }]
                }
            }
        });
        </script>
