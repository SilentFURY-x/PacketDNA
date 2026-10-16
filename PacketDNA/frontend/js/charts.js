/**
 * PacketDNA - Chart Manager
 * ==========================
 * Creates and manages Chart.js visualizations.
 */

const ChartManager = {
    charts: {},

    // Color palette for charts
    colors: {
        primary: ['#6366f1', '#8b5cf6', '#a855f7', '#c084fc', '#e9d5ff'],
        classification: [
            '#6366f1', // web_browsing - Indigo
            '#ef4444', // video_streaming - Red
            '#10b981', // file_transfer - Emerald
            '#f59e0b', // voip - Amber
            '#3b82f6', // dns - Blue
            '#ec4899', // social_media - Pink
            '#8b5cf6', // email - Violet
            '#14b8a6', // gaming - Teal
            '#f97316', // vpn - Orange
            '#06b6d4', // p2p - Cyan
            '#84cc16', // cloud_storage - Lime
            '#64748b', // unknown - Slate
        ],
        protocol: ['#06b6d4', '#6366f1', '#10b981', '#f59e0b', '#ef4444'],
    },

    // Default chart options
    defaultOptions: {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: '#94a3b8',
                    font: { family: 'Inter', size: 12 },
                    padding: 15,
                    usePointStyle: true,
                    pointStyleWidth: 10,
                },
            },
            tooltip: {
                backgroundColor: 'rgba(17, 24, 39, 0.95)',
                titleColor: '#f1f5f9',
                bodyColor: '#94a3b8',
                borderColor: 'rgba(99, 102, 241, 0.3)',
                borderWidth: 1,
                padding: 12,
                cornerRadius: 8,
                titleFont: { family: 'Inter', weight: '600' },
                bodyFont: { family: 'Inter' },
            },
        },
    },

    /**
     * Create a doughnut chart for traffic classification
     */
    createClassificationChart(canvasId, data) {
        this.destroyChart(canvasId);

        const labels = Object.keys(data);
        const values = Object.values(data);

        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.map(l => this.formatLabel(l)),
                datasets: [{
                    data: values,
                    backgroundColor: this.colors.classification.slice(0, labels.length),
                    borderColor: 'rgba(10, 14, 26, 0.8)',
                    borderWidth: 2,
                    hoverBorderWidth: 3,
                    hoverBorderColor: '#f1f5f9',
                    spacing: 2,
                }],
            },
            options: {
                ...this.defaultOptions,
                cutout: '60%',
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: {
                        ...this.defaultOptions.plugins.legend,
                        position: 'right',
                    },
                },
                animation: {
                    animateRotate: true,
                    animateScale: true,
                    duration: 1000,
                    easing: 'easeOutQuart',
                },
            },
        });
    },

    /**
     * Create a bar chart for protocol distribution
     */
    createProtocolChart(canvasId, data) {
        this.destroyChart(canvasId);

        const labels = Object.keys(data);
        const values = Object.values(data);

        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Flow Count',
                    data: values,
                    backgroundColor: this.colors.protocol.slice(0, labels.length).map(c => c + '80'),
                    borderColor: this.colors.protocol.slice(0, labels.length),
                    borderWidth: 1,
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 60,
                }],
            },
            options: {
                ...this.defaultOptions,
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: { display: false },
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(148, 163, 184, 0.06)' },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'JetBrains Mono', size: 11 },
                        },
                    },
                    y: {
                        grid: { color: 'rgba(148, 163, 184, 0.06)' },
                        ticks: {
                            color: '#64748b',
                            font: { family: 'Inter', size: 11 },
                        },
                        beginAtZero: true,
                    },
                },
                animation: {
                    duration: 800,
                    easing: 'easeOutCubic',
                },
            },
        });
    },

    /**
     * Create a horizontal bar chart for feature importance
     */
    createFeatureImportanceChart(canvasId, data) {
        this.destroyChart(canvasId);

        const sorted = Object.entries(data)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 12);

        const labels = sorted.map(([k]) => k);
        const values = sorted.map(([, v]) => v);

        const ctx = document.getElementById(canvasId);
        if (!ctx) return;

        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Importance',
                    data: values,
                    backgroundColor: 'rgba(99, 102, 241, 0.3)',
                    borderColor: '#6366f1',
                    borderWidth: 1,
                    borderRadius: 4,
                }],
            },
            options: {
                ...this.defaultOptions,
                indexAxis: 'y',
                plugins: {
                    ...this.defaultOptions.plugins,
                    legend: { display: false },
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(148, 163, 184, 0.06)' },
                        ticks: { color: '#64748b', font: { size: 10 } },
                    },
                    y: {
                        grid: { display: false },
                        ticks: {
                            color: '#94a3b8',
                            font: { family: 'JetBrains Mono', size: 10 },
                        },
                    },
                },
            },
        });
    },

    /**
     * Destroy a chart instance
     */
    destroyChart(canvasId) {
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
            delete this.charts[canvasId];
        }
    },

    /**
     * Format a label for display
     */
    formatLabel(label) {
        return label
            .replace(/_/g, ' ')
            .replace(/\b\w/g, c => c.toUpperCase());
    },
};
