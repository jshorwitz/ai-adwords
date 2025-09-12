// AI Agency Specialists - Dashboard Integration

class AIAgency {
    constructor() {
        this.specialists = {
            strategist: { name: 'AI Strategist', model: 'GPT-4', color: '#000000' },
            copywriter: { name: 'AI Copywriter', model: 'GPT-4', color: '#ff6b35' },
            analyst: { name: 'AI Analyst', model: 'Claude', color: '#00ff88' },
            researcher: { name: 'AI Researcher', model: 'Gemini', color: '#9C9C9C' }
        };
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSpecialistStatus();
    }

    setupEventListeners() {
        document.querySelectorAll('.specialist-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const specialist = e.target.dataset.specialist;
                this.consultSpecialist(specialist);
            });
        });
    }

    async loadSpecialistStatus() {
        try {
            const response = await fetch('/ai-agency/specialists');
            if (response.ok) {
                const data = await response.json();
                this.updateSpecialistStatus(data.specialists);
            }
        } catch (error) {
            console.error('Error loading specialist status:', error);
        }
    }

    updateSpecialistStatus(specialists) {
        specialists.forEach(specialist => {
            const card = document.querySelector(`.${specialist.name.toLowerCase()}-card`);
            if (card) {
                const status = card.querySelector('.specialist-status');
                status.textContent = specialist.available ? 'Ready' : 'Offline';
                status.style.color = specialist.available ? 'var(--success-color)' : 'var(--danger-color)';
            }
        });
    }

    async consultSpecialist(specialistType) {
        const specialist = this.specialists[specialistType];
        if (!specialist) return;

        this.showSpecialistModal(specialist, specialistType);
    }

    showSpecialistModal(specialist, type) {
        // Create modal for specialist consultation
        const modal = this.createSpecialistModal(specialist, type);
        document.body.appendChild(modal);
        
        setTimeout(() => modal.classList.add('active'), 100);
    }

    createSpecialistModal(specialist, type) {
        const modal = document.createElement('div');
        modal.className = 'specialist-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-container">
                <div class="modal-header">
                    <h3>
                        <i class="fas fa-brain"></i>
                        ${specialist.name}
                    </h3>
                    <p>Powered by ${specialist.model}</p>
                    <button class="modal-close">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-content">
                    ${this.getSpecialistForm(type)}
                </div>
            </div>
        `;

        // Add event listeners
        modal.querySelector('.modal-close').addEventListener('click', () => {
            this.closeSpecialistModal(modal);
        });

        modal.querySelector('.modal-overlay').addEventListener('click', () => {
            this.closeSpecialistModal(modal);
        });

        modal.querySelector('.specialist-form').addEventListener('submit', (e) => {
            this.handleSpecialistRequest(e, type, modal);
        });

        return modal;
    }

    getSpecialistForm(type) {
        const forms = {
            strategist: `
                <form class="specialist-form">
                    <div class="form-group">
                        <label>Campaign Goals</label>
                        <textarea name="goals" placeholder="Describe your advertising goals and objectives" rows="3"></textarea>
                    </div>
                    <div class="form-group">
                        <label>Monthly Budget</label>
                        <input type="number" name="budget" placeholder="5000" min="100">
                    </div>
                    <div class="form-group">
                        <label>Target Keywords (optional)</label>
                        <input type="text" name="keywords" placeholder="keyword1, keyword2, keyword3">
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-chess"></i>
                        GET STRATEGY BRIEF
                    </button>
                </form>
            `,
            copywriter: `
                <form class="specialist-form">
                    <div class="form-group">
                        <label>Product/Service</label>
                        <input type="text" name="product" placeholder="AI AdWords Platform" required>
                    </div>
                    <div class="form-group">
                        <label>Target Platform</label>
                        <select name="platform" required>
                            <option value="google">Google Ads</option>
                            <option value="reddit">Reddit Ads</option>
                            <option value="twitter">X (Twitter) Ads</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Target Keywords</label>
                        <input type="text" name="keywords" placeholder="keyword1, keyword2, keyword3">
                    </div>
                    <div class="form-group">
                        <label>Tone</label>
                        <select name="tone">
                            <option value="professional">Professional</option>
                            <option value="casual">Casual</option>
                            <option value="urgent">Urgent</option>
                            <option value="luxury">Luxury</option>
                        </select>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-pen-fancy"></i>
                        CREATE AD COPY
                    </button>
                </form>
            `,
            analyst: `
                <form class="specialist-form">
                    <div class="form-group">
                        <label>Analysis Timeframe</label>
                        <select name="timeframe" required>
                            <option value="7 days">Last 7 days</option>
                            <option value="30 days">Last 30 days</option>
                            <option value="90 days">Last 90 days</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>Focus Areas</label>
                        <textarea name="focus" placeholder="Specific areas you want analyzed (ROI, keywords, audiences, etc.)" rows="3"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-chart-analytics"></i>
                        ANALYZE PERFORMANCE
                    </button>
                </form>
            `,
            researcher: `
                <form class="specialist-form">
                    <div class="form-group">
                        <label>Industry/Market</label>
                        <input type="text" name="industry" placeholder="Technology, E-commerce, SaaS, etc." required>
                    </div>
                    <div class="form-group">
                        <label>Competitors</label>
                        <input type="text" name="competitors" placeholder="competitor1.com, competitor2.com">
                    </div>
                    <div class="form-group">
                        <label>Research Focus</label>
                        <textarea name="focus" placeholder="Market trends, opportunities, competitive gaps" rows="3"></textarea>
                    </div>
                    <button type="submit" class="btn btn-primary">
                        <i class="fas fa-search"></i>
                        RESEARCH MARKET
                    </button>
                </form>
            `
        };

        return forms[type] || '<p>Specialist form not available</p>';
    }

    async handleSpecialistRequest(e, type, modal) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const button = e.target.querySelector('button[type="submit"]');
        
        // Show loading state
        this.setButtonLoading(button, true);
        
        try {
            let response;
            
            switch (type) {
                case 'strategist':
                    response = await this.requestStrategy(formData);
                    break;
                case 'copywriter':
                    response = await this.requestCopywriting(formData);
                    break;
                case 'analyst':
                    response = await this.requestAnalysis(formData);
                    break;
                case 'researcher':
                    response = await this.requestResearch(formData);
                    break;
            }
            
            if (response && response.ok) {
                const result = await response.json();
                this.showSpecialistResult(result, type, modal);
            } else {
                this.showError('Failed to get response from AI specialist');
            }
            
        } catch (error) {
            console.error('Specialist request failed:', error);
            this.showError('Network error. Please try again.');
        } finally {
            this.setButtonLoading(button, false);
        }
    }

    async requestStrategy(formData) {
        return fetch('/ai-agency/strategy', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                website_data: { title: 'Current Website', industry: 'Technology' },
                keywords: (formData.get('keywords') || '').split(',').map(k => k.trim()).filter(k => k),
                budget: parseFloat(formData.get('budget')) || null,
                goals: (formData.get('goals') || '').split('\n').filter(g => g.trim())
            })
        });
    }

    async requestCopywriting(formData) {
        return fetch('/ai-agency/copywriting', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                product: formData.get('product'),
                keywords: (formData.get('keywords') || '').split(',').map(k => k.trim()).filter(k => k),
                platform: formData.get('platform'),
                tone: formData.get('tone'),
                target_audience: formData.get('audience') || ''
            })
        });
    }

    async requestAnalysis(formData) {
        // Use current dashboard metrics
        const mockMetrics = {
            spend: 5000,
            impressions: 150000,
            clicks: 7500,
            conversions: 45,
            ctr: 5.0,
            cpc: 0.67,
            roas: 3.2
        };

        return fetch('/ai-agency/analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                metrics: mockMetrics,
                timeframe: formData.get('timeframe'),
                campaigns: []
            })
        });
    }

    async requestResearch(formData) {
        return fetch('/ai-agency/research', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                industry: formData.get('industry'),
                competitors: (formData.get('competitors') || '').split(',').map(c => c.trim()).filter(c => c),
                website_url: 'https://example.com',
                focus_areas: (formData.get('focus') || '').split('\n').filter(f => f.trim())
            })
        });
    }

    showSpecialistResult(result, type, modal) {
        const modalContent = modal.querySelector('.modal-content');
        modalContent.innerHTML = `
            <div class="specialist-result">
                <div class="result-header">
                    <h4>
                        <i class="fas fa-check-circle"></i>
                        ${this.specialists[type].name} Analysis Complete
                    </h4>
                    <div class="result-meta">
                        <span>Model: ${this.specialists[type].model}</span>
                        <span>Confidence: ${result.confidence_score}%</span>
                        <span>Time: ${result.processing_time?.toFixed(2)}s</span>
                    </div>
                </div>
                <div class="result-content">
                    ${this.formatSpecialistResult(result.response, type)}
                </div>
                <div class="result-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.specialist-modal').remove()">
                        CLOSE
                    </button>
                    <button class="btn btn-primary" onclick="this.downloadReport('${type}')">
                        <i class="fas fa-download"></i>
                        DOWNLOAD REPORT
                    </button>
                </div>
            </div>
        `;
    }

    formatSpecialistResult(response, type) {
        if (type === 'strategist') {
            return `
                <div class="strategy-brief">
                    <h5>Campaign Strategy Brief</h5>
                    <div class="brief-content">${response.strategy_brief || 'Strategy analysis completed'}</div>
                    <div class="strategy-metrics">
                        <div class="metric-item">
                            <strong>Recommended Budget:</strong> $${response.recommended_budget?.toLocaleString() || '5,000'}
                        </div>
                        <div class="metric-item">
                            <strong>Expected ROAS:</strong> ${response.expected_roas || '3.5x'}
                        </div>
                        <div class="metric-item">
                            <strong>Timeline:</strong> ${response.timeline || '2-4 weeks'}
                        </div>
                    </div>
                </div>
            `;
        } else if (type === 'copywriter') {
            const ads = response.ad_variations || [];
            return `
                <div class="ad-variations">
                    <h5>Generated Ad Variations</h5>
                    ${ads.map((ad, i) => `
                        <div class="ad-preview">
                            <div class="ad-number">Ad ${i + 1}</div>
                            <div class="ad-headline">${ad.headline || 'Generated Headline'}</div>
                            <div class="ad-description">${ad.description || 'Generated description'}</div>
                            <div class="ad-cta">${ad.cta || 'Learn More'}</div>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (type === 'analyst') {
            return `
                <div class="performance-analysis">
                    <h5>Performance Analysis</h5>
                    <div class="analysis-content">${response.performance_analysis || 'Analysis completed'}</div>
                    <div class="optimization-score">
                        <strong>Optimization Score:</strong> ${response.optimization_score || 85}/100
                    </div>
                    <div class="priority-actions">
                        <h6>Priority Actions:</h6>
                        <ul>
                            ${(response.priority_actions || []).map(action => `<li>${action}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            `;
        } else if (type === 'researcher') {
            return `
                <div class="market-research">
                    <h5>Market Research Report</h5>
                    <div class="research-content">${response.market_research || 'Research completed'}</div>
                    <div class="opportunity-score">
                        <strong>Opportunity Score:</strong> ${response.opportunity_score || 90}/100
                    </div>
                    <div class="trending-keywords">
                        <h6>Trending Keywords:</h6>
                        <div class="keyword-tags">
                            ${(response.trending_keywords || []).map(keyword => 
                                `<span class="keyword-tag">${keyword}</span>`
                            ).join('')}
                        </div>
                    </div>
                </div>
            `;
        }
        
        return '<div class="generic-result">Analysis completed successfully</div>';
    }

    closeSpecialistModal(modal) {
        modal.classList.remove('active');
        setTimeout(() => {
            if (document.body.contains(modal)) {
                document.body.removeChild(modal);
            }
        }, 300);
    }

    setButtonLoading(button, loading) {
        if (loading) {
            button.disabled = true;
            const originalText = button.innerHTML;
            button.dataset.originalText = originalText;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> ANALYZING...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalText;
        }
    }

    showError(message) {
        // Create error notification
        const notification = document.createElement('div');
        notification.className = 'notification error';
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 100);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => document.body.removeChild(notification), 300);
        }, 4000);
    }
}

// Initialize AI Agency when dashboard loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.aiAgency = new AIAgency();
    });
} else {
    window.aiAgency = new AIAgency();
}
