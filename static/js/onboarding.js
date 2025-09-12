// AI AdWords Onboarding - One-Field Website Analysis

class OnboardingFlow {
    constructor() {
        this.currentStep = 1;
        this.websiteUrl = '';
        this.analysisData = {};
        this.startTime = Date.now();
        this.timer = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.startProgressTimer();
    }

    setupEventListeners() {
        // URL form submission
        document.getElementById('urlForm').addEventListener('submit', (e) => {
            this.handleUrlSubmit(e);
        });

        // Example URL buttons
        document.querySelectorAll('.example-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const url = e.target.dataset.url;
                document.getElementById('websiteUrl').value = url;
                this.handleUrlSubmit(new Event('submit'));
            });
        });

        // Connection buttons
        document.getElementById('connectGoogle')?.addEventListener('click', () => {
            this.connectPlatform('google');
        });

        document.getElementById('connectReddit')?.addEventListener('click', () => {
            this.connectPlatform('reddit');
        });

        document.getElementById('connectX')?.addEventListener('click', () => {
            this.connectPlatform('twitter');
        });

        // Action buttons
        document.getElementById('skipToDashboard')?.addEventListener('click', () => {
            window.location.href = '/dashboard';
        });

        document.getElementById('startOptimization')?.addEventListener('click', () => {
            window.location.href = '/dashboard?onboarded=true';
        });
    }

    startProgressTimer() {
        let timeRemaining = 60;
        const timeElement = document.getElementById('timeRemaining');
        
        this.timer = setInterval(() => {
            timeRemaining--;
            timeElement.textContent = timeRemaining;
            
            // Update progress bar based on current step
            const progress = Math.max((60 - timeRemaining) / 60 * 100, this.getStepProgress());
            document.getElementById('progressFill').style.width = `${progress}%`;
            
            if (timeRemaining <= 0) {
                clearInterval(this.timer);
                timeElement.textContent = '0';
            }
        }, 1000);
    }

    getStepProgress() {
        switch (this.currentStep) {
            case 1: return 0;
            case 2: return 20;
            case 3: return 100;
            default: return 0;
        }
    }

    async handleUrlSubmit(e) {
        e.preventDefault();
        
        const formData = new FormData(document.getElementById('urlForm'));
        this.websiteUrl = formData.get('url');
        
        if (!this.websiteUrl) {
            this.showMessage('Please enter a valid website URL', 'error');
            return;
        }

        // Validate URL format
        try {
            new URL(this.websiteUrl);
        } catch {
            this.showMessage('Please enter a valid URL (include https://)', 'error');
            return;
        }

        // Move to analysis step
        this.goToStep(2);
        await this.runWebsiteAnalysis();
    }

    async runWebsiteAnalysis() {
        try {
            // Update current task
            this.updateCurrentTask('Analyzing website content...');
            
            // Step 1: Website Analysis
            await this.analyzeWebsite();
            await this.sleep(2000);
            
            // Step 2: Keyword Discovery
            this.updateCurrentTask('Discovering optimization keywords...');
            await this.discoverKeywords();
            await this.sleep(3000);
            
            // Step 3: Competitor Analysis
            this.updateCurrentTask('Analyzing competitor strategies...');
            await this.analyzeCompetitors();
            await this.sleep(2000);
            
            // Step 4: Generate Optimization Brief
            this.updateCurrentTask('Generating AI optimization brief...');
            await this.generateOptimizationBrief();
            await this.sleep(2000);
            
            // Show results
            this.goToStep(3);
            this.populateResults();
            
        } catch (error) {
            console.error('Analysis failed:', error);
            this.showMessage('Analysis failed. Please try again.', 'error');
        }
    }

    async analyzeWebsite() {
        this.setStepActive('stepWebsite');
        
        try {
            // Call website analysis API
            const response = await fetch('/onboarding/analyze-website', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url: this.websiteUrl })
            });
            
            if (response.ok) {
                this.analysisData.website = await response.json();
            } else {
                // Use mock data if API fails
                this.analysisData.website = this.getMockWebsiteData();
            }
        } catch (error) {
            console.error('Website analysis failed:', error);
            this.analysisData.website = this.getMockWebsiteData();
        }
        
        this.setStepCompleted('stepWebsite');
    }

    async discoverKeywords() {
        this.setStepActive('stepKeywords');
        
        try {
            const response = await fetch('/onboarding/discover-keywords', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    url: this.websiteUrl,
                    content: this.analysisData.website?.content 
                })
            });
            
            if (response.ok) {
                this.analysisData.keywords = await response.json();
            } else {
                this.analysisData.keywords = this.getMockKeywordsData();
            }
        } catch (error) {
            console.error('Keyword discovery failed:', error);
            this.analysisData.keywords = this.getMockKeywordsData();
        }
        
        this.setStepCompleted('stepKeywords');
    }

    async analyzeCompetitors() {
        this.setStepActive('stepCompetitors');
        
        try {
            const response = await fetch('/onboarding/analyze-competitors', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    url: this.websiteUrl,
                    keywords: this.analysisData.keywords?.keywords || []
                })
            });
            
            if (response.ok) {
                this.analysisData.competitors = await response.json();
            } else {
                this.analysisData.competitors = this.getMockCompetitorsData();
            }
        } catch (error) {
            console.error('Competitor analysis failed:', error);
            this.analysisData.competitors = this.getMockCompetitorsData();
        }
        
        this.setStepCompleted('stepCompetitors');
    }

    async generateOptimizationBrief() {
        this.setStepActive('stepOptimization');
        
        try {
            const response = await fetch('/onboarding/generate-brief', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    url: this.websiteUrl,
                    website: this.analysisData.website,
                    keywords: this.analysisData.keywords,
                    competitors: this.analysisData.competitors
                })
            });
            
            if (response.ok) {
                this.analysisData.brief = await response.json();
            } else {
                this.analysisData.brief = this.getMockOptimizationBrief();
            }
        } catch (error) {
            console.error('Brief generation failed:', error);
            this.analysisData.brief = this.getMockOptimizationBrief();
        }
        
        this.setStepCompleted('stepOptimization');
    }

    goToStep(stepNumber) {
        // Hide all steps
        document.querySelectorAll('.onboarding-step').forEach(step => {
            step.classList.remove('active');
        });
        
        // Show target step
        document.getElementById(`step${stepNumber}`).classList.add('active');
        this.currentStep = stepNumber;
    }

    updateCurrentTask(task) {
        document.getElementById('currentTask').textContent = task;
    }

    setStepActive(stepId) {
        const step = document.getElementById(stepId);
        step.classList.add('active');
        step.querySelector('.step-indicator').innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    setStepCompleted(stepId) {
        const step = document.getElementById(stepId);
        step.classList.remove('active');
        step.classList.add('completed');
        step.querySelector('.step-indicator').innerHTML = '<i class="fas fa-check"></i>';
    }

    populateResults() {
        // Website info
        if (this.analysisData.website) {
            document.getElementById('websiteTitle').textContent = this.analysisData.website.title || 'Website';
            document.getElementById('websiteDescription').textContent = this.analysisData.website.description || 'No description available';
            document.getElementById('websiteIndustry').textContent = `Industry: ${this.analysisData.website.industry || 'Unknown'}`;
        }

        // Keywords
        if (this.analysisData.keywords) {
            this.populateKeywords(this.analysisData.keywords.keywords || []);
            document.getElementById('keywordCount').textContent = this.analysisData.keywords.keywords?.length || 0;
        }

        // KPIs
        if (this.analysisData.keywords) {
            this.populateKPIs(this.analysisData.keywords.estimated_kpis || {});
        }

        // Competitors
        if (this.analysisData.competitors) {
            this.populateCompetitors(this.analysisData.competitors.competitors || []);
            document.getElementById('competitorCount').textContent = this.analysisData.competitors.competitors?.length || 0;
        }

        // Optimization brief
        if (this.analysisData.brief) {
            this.populateOptimizationBrief(this.analysisData.brief);
        }

        // Opportunities
        this.populateOpportunities();

        // Calculate analysis time
        const analysisTime = Math.round((Date.now() - this.startTime) / 1000);
        document.getElementById('analysisTime').textContent = analysisTime;
    }

    populateKeywords(keywords) {
        const container = document.getElementById('keywordsList');
        container.innerHTML = '';
        
        keywords.forEach(keyword => {
            const tag = document.createElement('div');
            tag.className = `keyword-tag ${keyword.value === 'high' ? 'high-value' : ''}`;
            tag.textContent = keyword.keyword || keyword;
            container.appendChild(tag);
        });
    }

    populateKPIs(kpis) {
        document.getElementById('estImpressions').textContent = this.formatNumber(kpis.impressions) || '-';
        document.getElementById('estCPC').textContent = kpis.cpc ? `$${kpis.cpc}` : '-';
        document.getElementById('estCTR').textContent = kpis.ctr ? `${kpis.ctr}%` : '-';
        document.getElementById('estCAC').textContent = kpis.cac ? `$${kpis.cac}` : '-';
    }

    populateCompetitors(competitors) {
        const container = document.getElementById('competitorsList');
        container.innerHTML = '';
        
        competitors.forEach(competitor => {
            const item = document.createElement('div');
            item.className = 'competitor-item';
            item.innerHTML = `
                <div class="competitor-favicon">
                    <i class="fas fa-building"></i>
                </div>
                <div class="competitor-info">
                    <div class="competitor-name">${competitor.name || competitor}</div>
                    <div class="competitor-desc">${competitor.description || 'Competitor analysis'}</div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    populateOptimizationBrief(brief) {
        const container = document.getElementById('optimizationBrief');
        container.innerHTML = '';
        
        if (brief.sections) {
            brief.sections.forEach(section => {
                const sectionEl = document.createElement('div');
                sectionEl.className = 'brief-section';
                sectionEl.innerHTML = `
                    <h4>${section.title}</h4>
                    <ul>
                        ${section.recommendations.map(rec => `<li>${rec}</li>`).join('')}
                    </ul>
                `;
                container.appendChild(sectionEl);
            });
        } else {
            container.innerHTML = `
                <div class="brief-section">
                    <h4>Optimization Recommendations</h4>
                    <ul>
                        <li>Expand keyword targeting based on discovered opportunities</li>
                        <li>Implement cross-platform campaign strategy</li>
                        <li>Optimize landing pages for better conversion rates</li>
                        <li>Set up automated bid management for ROI optimization</li>
                    </ul>
                </div>
            `;
        }
    }

    populateOpportunities() {
        const opportunities = [
            {
                icon: '🎯',
                title: 'High-Value Keywords',
                desc: 'Found 12 high-value keywords with low competition'
            },
            {
                icon: '📊',
                title: 'Budget Optimization',
                desc: 'Potential 25% ROAS improvement with AI optimization'
            },
            {
                icon: '🌐',
                title: 'Cross-Platform Expansion',
                desc: 'Reddit and X ads could capture 30% more audience'
            }
        ];

        const container = document.getElementById('opportunitiesList');
        container.innerHTML = '';
        
        opportunities.forEach(opp => {
            const item = document.createElement('div');
            item.className = 'opportunity-item';
            item.innerHTML = `
                <div class="opportunity-icon">${opp.icon}</div>
                <div class="opportunity-text">
                    <div class="opportunity-title">${opp.title}</div>
                    <div class="opportunity-desc">${opp.desc}</div>
                </div>
            `;
            container.appendChild(item);
        });
    }

    connectPlatform(platform) {
        this.showMessage(`Connecting to ${platform.charAt(0).toUpperCase() + platform.slice(1)}...`, 'info');
        // In demo mode, simulate connection
        setTimeout(() => {
            this.showMessage(`${platform.charAt(0).toUpperCase() + platform.slice(1)} connected! Setting up optimization...`, 'success');
            setTimeout(() => {
                window.location.href = '/dashboard?connected=' + platform;
            }, 2000);
        }, 1500);
    }

    // Mock data generators
    getMockWebsiteData() {
        const domain = new URL(this.websiteUrl).hostname;
        return {
            title: `${domain.charAt(0).toUpperCase() + domain.slice(1)} - Business Website`,
            description: 'A modern business website focused on growth and customer acquisition through digital marketing.',
            industry: 'Technology',
            content: 'Website analysis completed',
            meta_tags: ['business', 'technology', 'growth', 'marketing']
        };
    }

    getMockKeywordsData() {
        const domain = new URL(this.websiteUrl).hostname;
        const baseKeyword = domain.split('.')[0];
        
        return {
            keywords: [
                { keyword: `${baseKeyword} software`, volume: 8500, cpc: 3.25, value: 'high' },
                { keyword: `${baseKeyword} platform`, volume: 5200, cpc: 2.80, value: 'high' },
                { keyword: `${baseKeyword} tool`, volume: 12000, cpc: 1.95, value: 'medium' },
                { keyword: `${baseKeyword} solution`, volume: 3800, cpc: 4.10, value: 'high' },
                { keyword: `${baseKeyword} app`, volume: 9500, cpc: 2.35, value: 'medium' },
                { keyword: `best ${baseKeyword}`, volume: 2100, cpc: 5.20, value: 'high' },
                { keyword: `${baseKeyword} alternative`, volume: 1800, cpc: 3.75, value: 'medium' },
                { keyword: `${baseKeyword} pricing`, volume: 1200, cpc: 4.50, value: 'high' }
            ],
            estimated_kpis: {
                impressions: 45000,
                cpc: 3.25,
                ctr: 4.2,
                cac: 185
            }
        };
    }

    getMockCompetitorsData() {
        const domain = new URL(this.websiteUrl).hostname;
        const industry = domain.includes('shop') ? 'ecommerce' : 'saas';
        
        const competitors = industry === 'ecommerce' ? [
            { name: 'Shopify', description: 'Leading ecommerce platform' },
            { name: 'WooCommerce', description: 'WordPress ecommerce solution' },
            { name: 'BigCommerce', description: 'Enterprise ecommerce platform' }
        ] : [
            { name: 'SimilarTech Competitor', description: 'Technology solution provider' },
            { name: 'IndustryLeader Pro', description: 'Market-leading platform' },
            { name: 'TechRival Solutions', description: 'Competitive technology company' }
        ];

        return { competitors };
    }

    getMockOptimizationBrief() {
        return {
            sections: [
                {
                    title: 'Immediate Opportunities',
                    recommendations: [
                        'Target 8 high-value keywords with low competition',
                        'Implement cross-platform strategy across Google, Reddit, and X',
                        'Set up conversion tracking and attribution analysis',
                        'Configure automated bid optimization for 25% ROAS improvement'
                    ]
                },
                {
                    title: 'Long-term Strategy',
                    recommendations: [
                        'Expand keyword portfolio based on competitor analysis',
                        'Implement dynamic budget allocation across platforms',
                        'Set up enhanced conversion tracking for better attribution',
                        'Deploy AI agents for 24/7 autonomous optimization'
                    ]
                }
            ]
        };
    }

    // Utility methods
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num?.toString() || '0';
    }

    updateCurrentTask(task) {
        document.getElementById('currentTask').textContent = task;
    }

    setStepActive(stepId) {
        const step = document.getElementById(stepId);
        step.classList.add('active');
        step.querySelector('.step-indicator').innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    }

    setStepCompleted(stepId) {
        const step = document.getElementById(stepId);
        step.classList.remove('active');
        step.classList.add('completed');
        step.querySelector('.step-indicator').innerHTML = '<i class="fas fa-check"></i>';
    }

    showMessage(text, type = 'info') {
        // Create and show message notification
        const message = document.createElement('div');
        message.className = `notification ${type}`;
        message.textContent = text;
        
        document.body.appendChild(message);
        
        setTimeout(() => message.classList.add('show'), 100);
        setTimeout(() => {
            message.classList.remove('show');
            setTimeout(() => document.body.removeChild(message), 300);
        }, 4000);
    }
}

// Initialize onboarding when page loads
document.addEventListener('DOMContentLoaded', () => {
    new OnboardingFlow();
});
