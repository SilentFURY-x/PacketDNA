/**
 * PacketDNA - API Client
 * =======================
 * Handles all communication with the Flask backend API.
 */

const API_BASE = '/api/v1';

const api = {
    /**
     * Health check
     */
    async health() {
        const res = await fetch(`${API_BASE}/health`);
        return res.json();
    },

    /**
     * Generate demo analysis
     */
    async generateDemo() {
        const res = await fetch(`${API_BASE}/demo`);
        return res.json();
    },

    /**
     * Upload and analyze a PCAP file
     * @param {File} file - PCAP file to analyze
     * @param {string} modelType - ML model type
     * @param {Function} onProgress - Progress callback
     */
    async analyzePcap(file, modelType = null, onProgress = null) {
        return new Promise((resolve, reject) => {
            const formData = new FormData();
            formData.append('file', file);
            if (modelType) {
                formData.append('model_type', modelType);
            }

            const xhr = new XMLHttpRequest();
            xhr.open('POST', `${API_BASE}/analyze`);

            if (onProgress) {
                xhr.upload.addEventListener('progress', (e) => {
                    if (e.lengthComputable) {
                        onProgress(Math.round((e.loaded / e.total) * 100));
                    }
                });
            }

            xhr.onload = () => {
                try {
                    const data = JSON.parse(xhr.responseText);
                    if (xhr.status === 200) {
                        resolve(data);
                    } else {
                        reject(data);
                    }
                } catch (e) {
                    reject({ error: 'Failed to parse response' });
                }
            };

            xhr.onerror = () => reject({ error: 'Network error' });
            xhr.send(formData);
        });
    },

    /**
     * Get analysis results by session ID
     */
    async getResults(sessionId) {
        const res = await fetch(`${API_BASE}/results/${sessionId}`);
        return res.json();
    },

    /**
     * List all sessions
     */
    async listSessions() {
        const res = await fetch(`${API_BASE}/sessions`);
        return res.json();
    },

    /**
     * Get system stats
     */
    async getStats() {
        const res = await fetch(`${API_BASE}/stats`);
        return res.json();
    },
};
