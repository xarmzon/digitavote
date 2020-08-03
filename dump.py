<li class="dropdown nav-item">
    <a aria-expanded="false" href="javascript:;" class="dropdown-toggle nav-link" data-toggle="dropdown">Poll<div class="ripple-container"></div></a>
    <div class="dropdown-menu">
        <a href="javascript:;" class="dropdown-item">Action</a>
        <a href="javascript:;" class="dropdown-item">Another action</a>
        <a href="javascript:;" class="dropdown-item">Something else here</a>
        <div class="dropdown-divider"></div>
        <a href="javascript:;" class="dropdown-item">Separated link</a>
        <div class="dropdown-divider"></div>
        <a href="javascript:;" class="dropdown-item">One more separated link</a>
    </div>
</li>


choices = []
        other_choices = Posts.query.filter(Posts.id != int(id)).all()

        choices.append((post.id, post.post_name))
        for choice in other_choices:
            choices.append((choice.id, choice.post_name))


                
                var ch = new CanvasJS.Chart("post-{{item['post']['id']}}a",{
                    theme: "light2",
                    axisY: {
                        margin: 0,
                        interval: 0
                    },

                    data:[
                        {
                            type: "bar",
                            dataPoints:[
                                {y: 3, label: "Olatoyan Gorge James"},
                                {y:10, label: "Jamiu A"},
                                {y:4, label: "Wakili Woru"},
                                {y:7, label: "Adelola Kayode Samson"}
                            ]
                        }
                    ]
                });
                ch.render();


{% if data %}
    {% block scripts %}
        {{super()}}
        <script src="{{ url_for('static', filename='js/plotly-basic.min.js') }}" type="text/javascript"></script>
        <script src="{{ url_for('static', filename='js/chartjs.min.js') }}" type="text/javascript"></script>
        <script type="text/javascript">
            
            {% for item in data %}
                var ctx = document.getElementById("post-{{item['post']['id']}}").getContext('2d');

                var ctx_data_list = {"names": [], "vcounts": []};
                {% for c in item['candidates'] %}
                    ctx_data_list["names"].push("{{c['cname']}}".split(" ")) ;
                    ctx_data_list["vcounts"].push({{c['vcounts']}});
                    
                    
                {% endfor %}
                var vote_chart = new Chart(ctx,{
                    type: 'horizontalBar',
                    data: {
                            labels: ctx_data_list['names'],
                            datasets: [{
                                label: '# of votes',
                                barPercentage: 0.5,
                                backgroundColor: "#0E7B65",
                                data: ctx_data_list['vcounts']
                            }]
                    },
                    options: {
                        legend: {
                            display: false
                        },
                        responsive: true,
                        scales: {
                            xAxes: [{
                                display: false,
                                gridLines: {
                                    display: false,
                                    drawBorder: false
                                },
                                ticks:{
                                    beginAtZero: true,

                                }
                            }],
                            yAxes: [{
                                barPercentage: 0.5,
                                gridLines: {
                                    display: false,
                                }
                            }],
                        },
                        
                        
                    },

                });
            {% endfor %}
        </script>
    {% endblock scripts %}
{% endif %}