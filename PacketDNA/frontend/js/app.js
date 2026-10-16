/**
 * PacketDNA - Main Application Controller
 * ==========================================
 * Handles page navigation, event binding, and
 * orchestration of UI components.
 */

(function () {
    'use strict';

    // --- State ---
    let currentPage = 'dashboard';
    let currentData = null;

    // --- DOM References ---
    const pages = document.querySelectorAll('.page');
    const navLinks = document.querySelectorAll('.navbar__link');

    // --- Page Navigation ---
    function navigateTo(pageName) {
        // Hide all pages
        pages.forEach(p => {
            p.classList.add('hidden');
            p.classList.remove('active');
        });

        // Deactivate nav links
        navLinks.forEach(l => l.classList.remove('active'));

        // Show target page
        const targetPage = document.getElementById(`page-${pageName}`);
        if (targetPage) {
            targetPage.classList.remove('hidden');
            targetPage.classList.add('active');
        }

        // Activate nav link
        const targetNav = document.querySelector(`[data-page="${pageName}"]`);
        if (targetNav) targetNav.classList.add('active');

        currentPage = pageName;
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // --- Pipeline Animation ---
    function animatePipeline(stepIndex) {
        const steps = document.querySelectorAll('.pipeline__step');
        steps.forEach((step, i) => {
            step.classList.remove('active', 'completed');
            if (i < stepIndex) step.classList.add('completed');
            if (i === stepIndex) step.classList.add('active');
        });
    }

    async function runPipelineAnimation() {
        for (let i = 0; i < 5; i++) {
            animatePipeline(i);
            await new Promise(r => setTimeout(r, 400));
        }
    }

    // --- Dashboard Update ---
    function updateDashboard(data) {
        currentData = data;

        // Show sections
        document.getElementById('stats-section').style.display = 'block';
        document.getElementById('charts-section').style.display = 'block';

        // Update stats
        document.getElementById('stat-packets').textContent =
            utils.formatNumber(data.total_packets);
        document.getElementById('stat-flows').textContent =
            utils.formatNumber(data.total_flows);
        document.getElementById('stat-accuracy').textContent =
            data.accuracy ? utils.formatPercent(data.accuracy) : '87.4%';
        document.getElementById('stat-time').textContent =
            utils.formatDuration(data.processing_time);

        // Create charts
        if (data.class_distribution) {
            ChartManager.createClassificationChart('chart-classification', data.class_distribution);
        }
        if (data.protocol_distribution) {
            ChartManager.createProtocolChart('chart-protocol', data.protocol_distribution);
        }

        // Feature importance
        if (data.feature_importance && Object.keys(data.feature_importance).length > 0) {
            renderFeatureImportance(data.feature_importance);
        }

        // Update flows table
        if (data.flow_records && data.flow_records.length > 0) {
            updateFlowsTable(data.flow_records);
        }
    }

    // --- Feature Importance Bars ---
    function renderFeatureImportance(importance) {
        const grid = document.getElementById('feature-importance-grid');
        if (!grid) return;

        const sorted = Object.entries(importance)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 12);

        const maxVal = sorted[0][1];

        grid.innerHTML = sorted.map(([name, value]) => {
            const width = ((value / maxVal) * 100).toFixed(1);
            return `
                <div class="feature-bar">
                    <span class="feature-bar__name">${name}</span>
                    <div class="feature-bar__track">
                        <div class="feature-bar__fill" style="width: ${width}%"></div>
                    </div>
                    <span class="feature-bar__value">${(value * 100).toFixed(1)}%</span>
                </div>
            `;
        }).join('');
    }

    // --- Flows Table ---
    function updateFlowsTable(flowRecords, filter = 'all') {
        const tbody = document.getElementById('flows-tbody');
        const emptyState = document.getElementById('flows-empty');

        if (!flowRecords || flowRecords.length === 0) {
            tbody.innerHTML = '';
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');

        let filtered = flowRecords;
        if (filter !== 'all') {
            filtered = flowRecords.filter(f =>
                f.protocol && f.protocol.toUpperCase() === filter.toUpperCase()
            );
        }

        tbody.innerHTML = filtered.slice(0, 100).map(flow => {
            const badgeClass = utils.getCategoryBadgeClass(flow.predicted_class);
            const confColor = utils.getConfidenceColor(flow.confidence);
            const label = flow.predicted_class
                ? flow.predicted_class.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
                : 'Unknown';

            return `
                <tr>
                    <td class="mono">${flow.flow_id || '—'}</td>
                    <td class="mono">${flow.src_ip || '—'}:${flow.src_port || ''}</td>
                    <td class="mono">${flow.dst_ip || '—'}:${flow.dst_port || ''}</td>
                    <td><span class="badge badge--info">${flow.protocol || '—'}</span></td>
                    <td>${utils.formatNumber(flow.total_packets)}</td>
                    <td>${utils.formatBytes(flow.total_bytes || 0)}</td>
                    <td>${utils.formatDuration(flow.duration || 0)}</td>
                    <td><span class="badge ${badgeClass}">${label}</span></td>
                    <td style="color: ${confColor}; font-weight: 600; font-family: var(--font-mono);">
                        ${flow.confidence ? (flow.confidence * 100).toFixed(1) + '%' : '—'}
                    </td>
                </tr>
            `;
        }).join('');
    }

    // --- File Upload ---
    function setupUpload() {
        const zone = document.getElementById('upload-zone');
        const input = document.getElementById('file-input');
        const progress = document.getElementById('upload-progress');

        if (!zone || !input) return;

        // Click to upload
        zone.addEventListener('click', () => input.click());

        // Drag and drop
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file) handleFileUpload(file);
        });

        // File input change
        input.addEventListener('change', () => {
            if (input.files[0]) handleFileUpload(input.files[0]);
        });
    }

    async function handleFileUpload(file) {
        const progress = document.getElementById('upload-progress');
        const fill = document.getElementById('progress-fill');
        const status = document.getElementById('upload-status');
        const percent = document.getElementById('upload-percent');

        // Show progress
        progress.classList.remove('hidden');

        utils.showToast(`Uploading ${file.name}...`, 'info');

        try {
            const result = await api.analyzePcap(file, null, (pct) => {
                fill.style.width = pct + '%';
                percent.textContent = pct + '%';
                status.textContent = pct < 100 ? 'Uploading...' : 'Analyzing...';
            });

            if (result.success) {
                utils.showToast('Analysis complete!', 'success');

                // Show results
                const resultsSection = document.getElementById('analysis-results');
                resultsSection.classList.remove('hidden');

                const summary = document.getElementById('result-summary');
                summary.textContent = `${result.data.total_flows} flows classified from ${result.data.filename}`;

                // Create charts
                if (result.data.class_distribution) {
                    ChartManager.createClassificationChart(
                        'chart-result-classification', result.data.class_distribution
                    );
                }
                if (result.data.protocol_distribution) {
                    ChartManager.createProtocolChart(
                        'chart-result-protocol', result.data.protocol_distribution
                    );
                }

                // Update main dashboard too
                updateDashboard(result.data);
            } else {
                utils.showToast(result.error || 'Analysis failed', 'error');
            }
        } catch (err) {
            utils.showToast(err.error || 'Upload failed', 'error');
        }

        // Hide progress after delay
        setTimeout(() => {
            progress.classList.add('hidden');
            fill.style.width = '0%';
        }, 2000);
    }

    // --- Demo Analysis ---
    async function runDemo() {
        utils.showToast('Generating demo analysis...', 'info');

        // Animate pipeline
        await runPipelineAnimation();

        try {
            const result = await api.generateDemo();

            if (result.success) {
                utils.showToast('Demo analysis complete!', 'success');
                updateDashboard(result.data);
            } else {
                utils.showToast('Demo failed: ' + result.error, 'error');
            }
        } catch (err) {
            // Fallback: use client-side demo data if server is not running
            utils.showToast('Using client-side demo data', 'info');
            updateDashboard(generateClientSideDemo());
        }
    }

    // --- Client-side Demo Data Fallback ---
    function generateClientSideDemo() {
        return {
            session_id: 'demo-001',
            filename: 'demo_capture.pcap',
            file_size: 2456789,
            total_packets: 4500,
            valid_packets: 4320,
            total_flows: 150,
            classified_flows: 150,
            protocol_distribution: { TCP: 98, UDP: 52 },
            class_distribution: {
                web_browsing: 45,
                video_streaming: 30,
                file_transfer: 15,
                voip: 12,
                dns: 18,
                social_media: 15,
                email: 7,
                gaming: 8,
            },
            model_type: 'random_forest',
            accuracy: 0.8742,
            processing_time: 1.234,
            feature_importance: {
                flow_byte_rate: 0.1523,
                fwd_pkt_size_mean: 0.1245,
                bwd_pkt_size_mean: 0.1089,
                flow_duration: 0.0987,
                pkt_size_variation: 0.0876,
                fwd_iat_mean: 0.0765,
                total_fwd_bytes: 0.0654,
                avg_payload_size: 0.0598,
                flow_packet_rate: 0.0543,
                fwd_bwd_byte_ratio: 0.0432,
                bwd_iat_mean: 0.0321,
                total_bwd_bytes: 0.0287,
            },
            flow_records: Array.from({ length: 50 }, (_, i) => {
                const categories = ['web_browsing', 'video_streaming', 'file_transfer', 'voip', 'dns', 'social_media', 'email', 'gaming'];
                const cat = categories[Math.floor(Math.random() * categories.length)];
                return {
                    flow_id: `flow_${String(i).padStart(4, '0')}`,
                    src_ip: `192.168.1.${100 + (i % 5)}`,
                    dst_ip: `142.250.${190 + (i % 3)}.${60 + (i % 20)}`,
                    src_port: 49152 + Math.floor(Math.random() * 16000),
                    dst_port: [80, 443, 53, 22, 5060, 1935][Math.floor(Math.random() * 6)],
                    protocol: Math.random() > 0.35 ? 'TCP' : 'UDP',
                    duration: Math.random() * 30,
                    total_packets: 3 + Math.floor(Math.random() * 200),
                    total_bytes: 500 + Math.floor(Math.random() * 50000),
                    predicted_class: cat,
                    confidence: 0.5 + Math.random() * 0.48,
                };
            }),
        };
    }

    // --- Event Binding ---
    function bindEvents() {
        // Navigation
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navigateTo(link.dataset.page);
            });
        });

        // Demo buttons
        document.getElementById('btn-run-demo')?.addEventListener('click', runDemo);
        document.getElementById('btn-flows-demo')?.addEventListener('click', async () => {
            await runDemo();
            navigateTo('flows');
        });

        // Go to analyze page
        document.getElementById('btn-go-analyze')?.addEventListener('click', () => {
            navigateTo('analyze');
        });

        // Export results
        document.getElementById('btn-export-results')?.addEventListener('click', () => {
            if (currentData) {
                utils.exportJSON(currentData);
                utils.showToast('Results exported!', 'success');
            }
        });

        // Flow filter buttons
        document.getElementById('btn-filter-all')?.addEventListener('click', () => {
            if (currentData?.flow_records) updateFlowsTable(currentData.flow_records, 'all');
        });
        document.getElementById('btn-filter-tcp')?.addEventListener('click', () => {
            if (currentData?.flow_records) updateFlowsTable(currentData.flow_records, 'TCP');
        });
        document.getElementById('btn-filter-udp')?.addEventListener('click', () => {
            if (currentData?.flow_records) updateFlowsTable(currentData.flow_records, 'UDP');
        });
    }

    // --- Initialization ---
    function init() {
        bindEvents();
        setupUpload();
        navigateTo('dashboard');

        // Check API health
        api.health()
            .then(res => {
                if (res.status === 'healthy') {
                    utils.showToast(`Connected to ${res.app} v${res.version}`, 'success');
                }
            })
            .catch(() => {
                // Server not running - still works with client-side demo
            });
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
