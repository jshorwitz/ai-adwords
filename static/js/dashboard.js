// AI AdWords Dashboard JavaScript

class Dashboard {
    constructor() {
        this.chart = null;
        this.refreshInterval = null;
        this.init();
    }

    async init() {
        this.setupEventListeners();
        this.showLoading();
        await this.loadDashboardData();
        this.hideLoading();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        document.getElementById('refreshBtn').addEventListener('click', () => {
            this.refreshData();
        });
    }

    showLoading() {
        document.getElementById('loading').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    async loadDashboardData() {
        try {
            // Load all dashboard data
            const [kpiData, platformData, agentData, activityData] = await Promise.all([
                this.fetchKPIData(),
                this.fetchPlatformData(),
                this.fetchAgentData(),
                this.fetchActivityData()
            ]);

            // Update UI with data
            this.updateKPICards(kpiData);
            this.updatePlatformCards(platformData);
            this.updateChart(platformData);
            this.updateAgentCards(agentData);
            this.updateActivityFeed(activityData);
            this.updateLastUpdated();

        } catch (error) {
            console.error('Error loading dashboard data:', error);
            this.showError('Failed to load dashboard data');
        }
    }

    async fetchKPIData() {
        try {
            const response = await fetch('/dashboard/kpis');
            if (!response.ok) throw new Error('Failed to fetch KPI data');
            const data = await response.json();
            
            return {
                totalSpend: data.total_spend,
                totalImpressions: data.total_impressions,
                totalClicks: data.total_clicks,
                totalConversions: data.total_conversions,
                avgCTR: data.avg_ctr,
                avgROAS: data.avg_roas,
                changes: data.changes
            };
        } catch (error) {
            console.error('Error fetching KPI data:', error);
            // Fallback to mock data
            return {
                totalSpend: 45250.75,
                totalImpressions: 2847391,
                totalClicks: 127583,
                totalConversions: 3492,
                avgCTR: 4.48,
                avgROAS: 3.2,
                changes: {
                    spend: 12.5,
                    impressions: 8.7,
                    clicks: 15.2,
                    conversions: 22.1,
                    ctr: -2.3,
                    roas: 18.9
                }
            };
        }
    }

    async fetchPlatformData() {
        try {
            const response = await fetch('/dashboard/platforms');
            if (!response.ok) throw new Error('Failed to fetch platform data');
            const platforms = await response.json();
            
            return platforms.map(p => ({
                platform: p.platform,
                name: p.name,
                spend: p.spend,
                impressions: p.impressions,
                clicks: p.clicks,
                conversions: p.conversions,
                ctr: p.ctr,
                roas: p.roas,
                status: p.status
            }));
        } catch (error) {
            console.error('Error fetching platform data:', error);
            // Fallback to mock data
            return [
                {
                    platform: 'google',
                    name: 'Google Ads',
                    spend: 28450.25,
                    impressions: 1847291,
                    clicks: 89234,
                    conversions: 2134,
                    ctr: 4.83,
                    roas: 3.5,
                    status: 'active'
                },
                {
                    platform: 'reddit',
                    name: 'Reddit Ads',
                    spend: 8950.50,
                    impressions: 567000,
                    clicks: 23419,
                    conversions: 789,
                    ctr: 4.13,
                    roas: 2.8,
                    status: 'mock'
                },
                {
                    platform: 'x',
                    name: 'X (Twitter) Ads',
                    spend: 7850.00,
                    impressions: 433100,
                    clicks: 14930,
                    conversions: 569,
                    ctr: 3.45,
                    roas: 2.9,
                    status: 'mock'
                }
            ];
        }
    }

    async fetchAgentData() {
        try {
            const response = await fetch('/agents/list');
            if (!response.ok) throw new Error('Failed to fetch agents');
            
            const agents = await response.json();
            
            // Get agent status
            const statusResponse = await fetch('/agents/status?limit=10');
            const statusData = statusResponse.ok ? await statusResponse.json() : [];

            return agents.map(agent => ({
                ...agent,
                status: this.getAgentStatus(agent.agent_name, statusData),
                lastRun: this.getLastRunTime(agent.agent_name, statusData)
            }));
        } catch (error) {
            console.error('Error fetching agent data:', error);
            return [
                { agent_name: 'ingestor-google', type: 'Ingestor', description: 'Pull Google Ads metrics', status: 'idle' },
                { agent_name: 'ingestor-reddit', type: 'Ingestor', description: 'Pull Reddit Ads metrics', status: 'idle' },
                { agent_name: 'ingestor-x', type: 'Ingestor', description: 'Pull X Ads metrics', status: 'idle' },
                { agent_name: 'touchpoint-extractor', type: 'Transform', description: 'Extract touchpoints', status: 'idle' },
                { agent_name: 'conversion-uploader', type: 'Activation', description: 'Upload conversions', status: 'idle' },
                { agent_name: 'budget-optimizer', type: 'Decision', description: 'Optimize budgets', status: 'idle' },
                { agent_name: 'keywords-hydrator', type: 'Decision', description: 'Enrich keywords', status: 'idle' }
            ];
        }
    }

    async fetchActivityData() {
        try {
            const response = await fetch('/agents/status?limit=5');
            if (!response.ok) throw new Error('Failed to fetch activity');
            
            const runs = await response.json();
            return runs.map(run => ({
                id: run.run_id,
                title: `${run.agent} ${run.ok ? 'completed successfully' : 'failed'}`,
                time: this.formatTime(run.started_at),
                type: run.ok ? 'success' : 'error',
                details: run.error || `Processed ${run.records_written || 0} records`
            }));
        } catch (error) {
            console.error('Error fetching activity data:', error);
            return [
                { id: 1, title: 'Budget optimizer completed successfully', time: '2 minutes ago', type: 'success' },
                { id: 2, title: 'Google Ads data ingested', time: '15 minutes ago', type: 'success' },
                { id: 3, title: 'Touchpoint extraction completed', time: '32 minutes ago', type: 'success' },
                { id: 4, title: 'Conversion upload in progress', time: '1 hour ago', type: 'warning' }
            ];
        }
    }

    updateKPICards(data) {
        document.getElementById('totalSpend').textContent = `$${this.formatNumber(data.totalSpend)}`;
        document.getElementById('totalImpressions').textContent = this.formatNumber(data.totalImpressions);
        document.getElementById('totalClicks').textContent = this.formatNumber(data.totalClicks);
        document.getElementById('totalConversions').textContent = this.formatNumber(data.totalConversions);
        document.getElementById('avgCTR').textContent = `${data.avgCTR}%`;
        document.getElementById('avgROAS').textContent = `${data.avgROAS}x`;

        // Update change indicators
        this.updateChangeIndicator('spendChange', data.changes.spend);
        this.updateChangeIndicator('impressionsChange', data.changes.impressions);
        this.updateChangeIndicator('clicksChange', data.changes.clicks);
        this.updateChangeIndicator('conversionsChange', data.changes.conversions);
        this.updateChangeIndicator('ctrChange', data.changes.ctr);
        this.updateChangeIndicator('roasChange', data.changes.roas);
    }

    updateChangeIndicator(elementId, change) {
        const element = document.getElementById(elementId);
        const isPositive = change >= 0;
        element.textContent = `${isPositive ? '+' : ''}${change}%`;
        element.className = `kpi-change ${isPositive ? 'positive' : 'negative'}`;
    }

    updatePlatformCards(platforms) {
        platforms.forEach(platform => {
            const prefix = platform.platform;
            document.getElementById(`${prefix}Spend`).textContent = `$${this.formatNumber(platform.spend)}`;
            document.getElementById(`${prefix}Conversions`).textContent = this.formatNumber(platform.conversions);
            document.getElementById(`${prefix}ROAS`).textContent = `${platform.roas}x`;
            document.getElementById(`${prefix}CTR`).textContent = `${platform.ctr}%`;

            const statusElement = document.getElementById(`${prefix}Status`);
            statusElement.textContent = platform.status === 'active' ? 'Active' : 'Mock Mode';
            statusElement.className = `platform-status ${platform.status === 'active' ? '' : 'mock'}`;
        });
    }

    updateChart(platforms) {
        const ctx = document.getElementById('platformChart').getContext('2d');
        
        if (this.chart) {
            this.chart.destroy();
        }

        this.chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: platforms.map(p => p.name),
                datasets: [{
                    data: platforms.map(p => p.spend),
                    backgroundColor: [
                        '#4285f4',
                        '#ff4500', 
                        '#000000'
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true
                        }
                    },
                    title: {
                        display: true,
                        text: 'Spend by Platform',
                        font: {
                            size: 16,
                            weight: '600'
                        }
                    }
                }
            }
        });
    }

    updateAgentCards(agents) {
        const container = document.getElementById('agentsGrid');
        container.innerHTML = '';

        agents.forEach(agent => {
            const card = document.createElement('div');
            card.className = `agent-card ${agent.status}`;
            card.innerHTML = `
                <div class="agent-name">${agent.agent_name}</div>
                <div class="agent-type">${agent.type}</div>
                <div class="agent-status ${agent.status}">${agent.status}</div>
                ${agent.lastRun ? `<div class="agent-last-run">${agent.lastRun}</div>` : ''}
            `;
            container.appendChild(card);
        });
    }

    updateActivityFeed(activities) {
        const container = document.getElementById('activityFeed');
        container.innerHTML = '';

        if (activities.length === 0) {
            container.innerHTML = '<div class="text-center mt-4">No recent activity</div>';
            return;
        }

        activities.forEach(activity => {
            const item = document.createElement('div');
            item.className = 'activity-item';
            item.innerHTML = `
                <div class="activity-icon ${activity.type}">
                    <i class="fas ${this.getActivityIcon(activity.type)}"></i>
                </div>
                <div class="activity-content">
                    <div class="activity-title">${activity.title}</div>
                    <div class="activity-time">${activity.time}</div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    updateLastUpdated() {
        const now = new Date();
        document.getElementById('lastUpdated').textContent = `Last updated: ${now.toLocaleTimeString()}`;
    }

    async refreshData() {
        const btn = document.getElementById('refreshBtn');
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Refreshing...';

        await this.loadDashboardData();

        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh';
    }

    startAutoRefresh() {
        this.refreshInterval = setInterval(() => {
            this.loadDashboardData();
        }, 60000); // Refresh every minute
    }

    // Helper methods
    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    formatTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = Math.floor((now - date) / 1000);

        if (diff < 60) return 'Just now';
        if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;
        return `${Math.floor(diff / 86400)} days ago`;
    }

    getActivityIcon(type) {
        switch (type) {
            case 'success': return 'fa-check';
            case 'warning': return 'fa-exclamation-triangle';
            case 'error': return 'fa-times';
            default: return 'fa-info';
        }
    }

    getAgentStatus(agentName, statusData) {
        const recentRun = statusData.find(run => run.agent === agentName);
        if (!recentRun) return 'idle';
        if (recentRun.ok === null) return 'running';
        return recentRun.ok ? 'idle' : 'error';
    }

    getLastRunTime(agentName, statusData) {
        const recentRun = statusData.find(run => run.agent === agentName);
        return recentRun ? this.formatTime(recentRun.started_at) : null;
    }

    showError(message) {
        // Create error notification
        const error = document.createElement('div');
        error.className = 'error-notification';
        error.textContent = message;
        document.body.appendChild(error);
        
        setTimeout(() => {
            document.body.removeChild(error);
        }, 5000);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new Dashboard();
});
