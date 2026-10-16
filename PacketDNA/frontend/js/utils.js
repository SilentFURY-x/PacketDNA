/**
 * PacketDNA - Utility Functions
 * ==============================
 */

const utils = {
    /**
     * Format bytes to human-readable string
     */
    formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    },

    /**
     * Format number with commas
     */
    formatNumber(num) {
        if (num === null || num === undefined) return '—';
        return num.toLocaleString();
    },

    /**
     * Format duration in seconds
     */
    formatDuration(seconds) {
        if (seconds < 1) return (seconds * 1000).toFixed(0) + 'ms';
        if (seconds < 60) return seconds.toFixed(2) + 's';
        const mins = Math.floor(seconds / 60);
        const secs = (seconds % 60).toFixed(0);
        return `${mins}m ${secs}s`;
    },

    /**
     * Format percentage
     */
    formatPercent(value) {
        if (value === null || value === undefined) return '—';
        return (value * 100).toFixed(1) + '%';
    },

    /**
     * Show a toast notification
     */
    showToast(message, type = 'info', duration = 4000) {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast toast--${type}`;
        
        const icons = { success: '✅', error: '❌', info: 'ℹ️', warning: '⚠️' };
        toast.innerHTML = `
            <span>${icons[type] || 'ℹ️'}</span>
            <span style="flex:1; font-size: var(--font-size-sm); color: var(--color-text-secondary);">
                ${message}
            </span>
        `;
        
        container.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100px)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    },

    /**
     * Get badge class based on traffic category
     */
    getCategoryBadgeClass(category) {
        const map = {
            web_browsing: 'badge--primary',
            video_streaming: 'badge--danger',
            file_transfer: 'badge--success',
            voip: 'badge--warning',
            dns: 'badge--info',
            social_media: 'badge--primary',
            email: 'badge--info',
            gaming: 'badge--success',
            vpn: 'badge--danger',
            p2p: 'badge--warning',
            cloud_storage: 'badge--info',
            unknown: 'badge--primary',
        };
        return map[category] || 'badge--primary';
    },

    /**
     * Get confidence color based on value
     */
    getConfidenceColor(confidence) {
        if (confidence >= 0.8) return 'var(--color-accent-success)';
        if (confidence >= 0.6) return 'var(--color-accent-warning)';
        return 'var(--color-accent-danger)';
    },

    /**
     * Debounce function
     */
    debounce(fn, delay = 300) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), delay);
        };
    },

    /**
     * Export data as JSON file
     */
    exportJSON(data, filename = 'packetdna_results.json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    },
};
