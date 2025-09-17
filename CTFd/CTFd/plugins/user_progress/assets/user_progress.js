document.addEventListener('DOMContentLoaded', function () {
    const userSelect = document.getElementById('user-select');
    const categorySelect = document.getElementById('category-select');

    const attemptedChart = echarts.init(document.getElementById('attempted-chart'));
    const solvedChart = echarts.init(document.getElementById('solved-chart'));

    function getChartOption(title, completed, total) {
        const remaining = total - completed;
        return {
            title: {
                text: title,
                subtext: `${completed} / ${total}`,
                left: 'center'
            },
            tooltip: {
                trigger: 'item'
            },
            legend: {
                orient: 'vertical',
                left: 'left',
            },
            series: [
                {
                    name: 'Progress',
                    type: 'pie',
                    radius: '50%',
                    data: [
                        { value: completed, name: title },
                        { value: remaining, name: 'Remaining' },
                    ],
                    emphasis: {
                        itemStyle: {
                            shadowBlur: 10,
                            shadowOffsetX: 0,
                            shadowColor: 'rgba(0, 0, 0, 0.5)'
                        }
                    }
                }
            ]
        };
    }

    function updateCharts(userId, category) {
        if (!userId) return;

        fetch(`/api/v1/user_progress/stats?user_id=${userId}&category=${category}`)
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    const { total, attempted, solved } = result.data;

                    attemptedChart.setOption(getChartOption('Attempted', attempted, total));
                    solvedChart.setOption(getChartOption('Solved', solved, total));
                }
            });
    }

    function populateUsers() {
        fetch('/api/v1/user_progress/users')
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    result.data.forEach(user => {
                        const option = document.createElement('option');
                        option.value = user.id;
                        option.textContent = user.name;
                        userSelect.appendChild(option);
                    });
                    // Trigger initial chart load
                    if (userSelect.value) {
                         updateCharts(userSelect.value, categorySelect.value);
                    }
                }
            });
    }

    function populateCategories() {
        fetch('/api/v1/user_progress/categories')
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    result.data.forEach(category => {
                        const option = document.createElement('option');
                        option.value = category;
                        option.textContent = category;
                        categorySelect.appendChild(option);
                    });
                }
            });
    }

    userSelect.addEventListener('change', () => {
        updateCharts(userSelect.value, categorySelect.value);
    });

    categorySelect.addEventListener('change', () => {
        updateCharts(userSelect.value, categorySelect.value);
    });

    populateUsers();
    populateCategories();
});
