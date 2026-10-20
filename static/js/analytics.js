/* Analytics workspace — chart rendering and live session count. */
document.addEventListener('DOMContentLoaded', function () {
    const canvas = document.getElementById('analyticsChart');
    const dataEl = document.getElementById('analyticsSeries');
    if (!canvas || !dataEl || typeof Chart === 'undefined') {
        return;
    }

    let rows = [];
    try {
        rows = JSON.parse(dataEl.textContent) || [];
    } catch (error) {
        rows = [];
    }

    const styles = getComputedStyle(document.documentElement);
    const readVar = (name, fallback) => (styles.getPropertyValue(name) || fallback).trim();
    const palette = () => ({
        sessions: readVar('--chart-1', '#17654a'),
        pageViews: readVar('--chart-3', '#56789b'),
        devices: readVar('--chart-2', '#b08243'),
        text: readVar('--text-muted', '#717d75'),
        grid: readVar('--chart-grid', '#eceee9'),
        surface: readVar('--surface', '#ffffff'),
        border: readVar('--border', '#e4e7e1'),
        ink: readVar('--text', '#17211c'),
    });

    const labels = rows.map((row) => row.date);
    const sessions = rows.map((row) => row.sessions);
    const views = rows.map((row) => row.page_views);
    const devices = rows.map((row) => row.devices);

    const alpha = (color, value) => `${color}${value}`;

    function makeChart() {
        const colors = palette();
        return new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Sessions',
                        data: sessions,
                        borderColor: colors.sessions,
                        backgroundColor: alpha(colors.sessions, '1f'),
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        pointHoverBackgroundColor: colors.surface,
                        pointHoverBorderColor: colors.sessions,
                        pointHoverBorderWidth: 2,
                        tension: 0.35,
                        fill: true,
                    },
                    {
                        label: 'Page views',
                        data: views,
                        borderColor: colors.pageViews,
                        backgroundColor: alpha(colors.pageViews, '18'),
                        borderWidth: 2,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        pointHoverBackgroundColor: colors.surface,
                        pointHoverBorderColor: colors.pageViews,
                        pointHoverBorderWidth: 2,
                        tension: 0.35,
                        fill: true,
                    },
                    {
                        label: 'Devices',
                        data: devices,
                        borderColor: colors.devices,
                        backgroundColor: 'transparent',
                        borderWidth: 1.6,
                        borderDash: [4, 4],
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        tension: 0.35,
                        fill: false,
                        hidden: true,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 320 },
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: colors.ink,
                        titleColor: '#ffffff',
                        bodyColor: 'rgba(255, 255, 255, 0.82)',
                        titleFont: { family: 'Inter', size: 11, weight: '600' },
                        bodyFont: { family: 'Inter', size: 11.5 },
                        padding: 10,
                        cornerRadius: 6,
                        boxPadding: 4,
                        usePointStyle: true,
                        callbacks: {
                            label(context) {
                                return ` ${context.dataset.label}: ${context.parsed.y}`;
                            },
                        },
                    },
                },
                scales: {
                    x: {
                        grid: { display: false, drawBorder: false },
                        border: { display: false },
                        ticks: {
                            color: colors.text,
                            font: { family: 'Inter', size: 10.5 },
                            maxTicksLimit: 8,
                            maxRotation: 0,
                            autoSkip: true,
                        },
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: colors.grid, drawBorder: false },
                        border: { display: false },
                        ticks: {
                            color: colors.text,
                            font: { family: 'Inter', size: 10.5 },
                            precision: 0,
                            maxTicksLimit: 5,
                            padding: 8,
                        },
                    },
                },
            },
        });
    }

    let chart = null;
    if (rows.length) {
        chart = makeChart();
    }

    document.querySelectorAll('.chart-toggle').forEach((button) => {
        button.addEventListener('click', function () {
            if (!chart) return;
            const key = button.dataset.series;
            const index = { sessions: 0, page_views: 1, devices: 2 }[key];
            if (index === undefined) return;
            const isVisible = chart.isDatasetVisible(index);
            chart.setDatasetVisibility(index, !isVisible);
            button.classList.toggle('is-active', !isVisible);
            button.setAttribute('aria-pressed', String(!isVisible));
            chart.update();
        });
    });

    // Keep the chart in step with the theme toggle.
    const observer = new MutationObserver(() => {
        if (!chart) return;
        chart.destroy();
        chart = makeChart();
        document.querySelectorAll('.chart-toggle').forEach((button) => {
            const index = { sessions: 0, page_views: 1, devices: 2 }[button.dataset.series];
            const visible = index !== undefined ? chart.isDatasetVisible(index) : true;
            button.classList.toggle('is-active', visible);
            button.setAttribute('aria-pressed', String(visible));
        });
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] });

    // Live "online now" counter, refreshed once a minute.
    const live = document.getElementById('liveOnline');
    const count = document.getElementById('onlineCount');
    if (live && count) {
        window.setInterval(() => {
            fetch('/analytics/live-stats/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then((response) => (response.ok ? response.json() : null))
                .then((payload) => {
                    if (payload && payload.success && payload.stats) {
                        count.textContent = payload.stats.online_sessions;
                    }
                })
                .catch(() => {});
        }, 60000);
    }
});
