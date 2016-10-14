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

            <div class="tab-content" style="width: 100%;">
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
                <div class="tab-pane" id="metrics" style="width: 100%;">
                    <div id="memory"></div>
                    <div id="cpu"></div>
                </div>
                <div class="tab-pane" id="log" style="width: 100%; height: 90%;">
                    <button type="button" class="btn btn-default" style="margin-bottom: 5px" onclick="window.location = 'get_log?log_name=${run.log}&full_log=True';">
                        Download Full Log
                    </button>
                    <div id="log_well" class="well" style="height: 85%; overflow-y: scroll; margin-bottom: 0px">
                        ${log.replace("\n", "<br>")}
                    </div>
                </div>
            </div>
        </div>

        <div class="modal-footer">
            <button type="button" class="btn btn-default" data-dismiss="modal">Close</button>
        </div>

        <script>
            var memory = {
                name: 'Memory',
                y: ${run.memory_history},
                fillcolor: "rgba(255, 99, 132, 0.2)",
                line: {color: "rgba(255, 99, 132, 0.3)"},
                fill: 'tozeroy',
                type: 'scatter',
            };
            
            var mem_layout = {
                autosize: false,
                height: 200,
                width: 800,
                margin: {l: 30, r: 20, b: 20, t: 25},
                title: 'Memory',
                yaxis: {
                    exponentformat: 'SI',
                },
            };
            
            var cpu = {
                name: 'CPU',
                y: ${run.cpu_history},
                fillcolor: "rgba(54, 162, 235, 0.2)",
                line: {color: "rgba(54, 162, 235, 0.3)"},
                fill: 'tozeroy',
                type: 'scatter',
            };     
            
            var cpu_layout = {
                autosize: false,
                height: 200,
                width: 800,
                margin: {l: 30, r: 20, b: 20, t: 25},
                title: 'CPU',
            };
            
            Plotly.newPlot('memory', [memory], mem_layout);
            Plotly.newPlot('cpu', [cpu], cpu_layout);
        </script>
