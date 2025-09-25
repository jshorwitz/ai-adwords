// Advanced D3.js Visualizations for AI AdWords Dashboard

class D3Visualizations {
    constructor() {
        // Nike-inspired color palette for platforms
        this.colors = {
            google: '#000000',      // Nike black
            reddit: '#ff6b35',      // Nike orange accent  
            microsoft: '#0078D4',   // Microsoft Blue
            linkedin: '#0077B5'     // LinkedIn Blue
        };
        
        this.colorGradients = {
            google: ['#000000', '#333333'],
            reddit: ['#ff6b35', '#ff8c42'],
            microsoft: ['#0078D4', '#106ebe'],
            linkedin: ['#0077B5', '#005885']
        };
        
        this.tooltip = this.createTooltip();
    }

    createTooltip() {
        return d3.select('body')
            .append('div')
            .attr('class', 'tooltip')
            .style('position', 'absolute')
            .style('visibility', 'hidden');
    }

    // 1. Interactive Donut Chart for Spend Distribution
    createSpendDonutChart(data, containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const width = 350;
        const height = 300;
        const radius = Math.min(width, height) / 2 - 20;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${width} ${height}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${width/2}, ${height/2})`);

        // Create pie generator
        const pie = d3.pie()
            .value(d => d.spend)
            .sort(null)
            .padAngle(0.02);

        // Create arc generator  
        const arc = d3.arc()
            .innerRadius(radius * 0.5)
            .outerRadius(radius);

        const outerArc = d3.arc()
            .innerRadius(radius * 1.1)
            .outerRadius(radius * 1.1);

        // Create arcs
        const arcs = g.selectAll('.arc')
            .data(pie(data))
            .enter()
            .append('g')
            .attr('class', 'arc');

        // Add paths with animation
        arcs.append('path')
            .attr('fill', d => this.colors[d.data.platform])
            .attr('d', arc)
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .style('opacity', 1)
            .attrTween('d', function(d) {
                const i = d3.interpolate({startAngle: 0, endAngle: 0}, d);
                return function(t) { return arc(i(t)); };
            });

        // Add hover effects
        arcs.selectAll('path')
            .on('mouseover', (event, d) => {
                const percentage = ((d.data.spend / d3.sum(data, d => d.spend)) * 100).toFixed(1);
                this.tooltip
                    .style('visibility', 'visible')
                    .html(`
                        <strong>${d.data.name}</strong><br/>
                        Spend: $${this.formatNumber(d.data.spend)}<br/>
                        Share: ${percentage}%<br/>
                        Conversions: ${this.formatNumber(d.data.conversions)}
                    `);
            })
            .on('mousemove', (event) => {
                this.tooltip
                    .style('top', (event.pageY - 10) + 'px')
                    .style('left', (event.pageX + 10) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.style('visibility', 'hidden');
            });

        // Add center text
        g.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '-0.5em')
            .style('font-size', '24px')
            .style('font-weight', '700')
            .style('fill', this.colors.google)
            .text(`$${this.formatNumber(d3.sum(data, d => d.spend))}`);

        g.append('text')
            .attr('text-anchor', 'middle')
            .attr('dy', '1em')
            .style('font-size', '12px')
            .style('fill', '#64748b')
            .text('Total Spend');

        // Add legend
        const legend = svg.append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(20, ${height - 80})`);

        const legendItems = legend.selectAll('.legend-item')
            .data(data)
            .enter()
            .append('g')
            .attr('class', 'legend-item')
            .attr('transform', (d, i) => `translate(0, ${i * 20})`);

        legendItems.append('rect')
            .attr('width', 12)
            .attr('height', 12)
            .attr('fill', d => this.colors[d.platform]);

        legendItems.append('text')
            .attr('x', 18)
            .attr('y', 6)
            .attr('dy', '0.35em')
            .style('font-size', '12px')
            .style('fill', '#64748b')
            .text(d => d.name);
    }

    // 2. ROAS Comparison Bar Chart
    createROASBarChart(data, containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = {top: 20, right: 20, bottom: 60, left: 60};
        const width = 350 - margin.left - margin.right;
        const height = 250 - margin.bottom - margin.top;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${350} ${300}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Scales
        const x = d3.scaleBand()
            .domain(data.map(d => d.name))
            .range([0, width])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.roas) * 1.1])
            .range([height, 0]);

        // Add bars with animation
        g.selectAll('.bar')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.name))
            .attr('width', x.bandwidth())
            .attr('fill', d => this.colors[d.platform])
            .attr('y', height)
            .attr('height', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200)
            .attr('y', d => y(d.roas))
            .attr('height', d => height - y(d.roas));

        // Add value labels on bars
        g.selectAll('.bar-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => x(d.name) + x.bandwidth() / 2)
            .attr('y', d => y(d.roas) - 5)
            .text(d => `${d.roas}x`)
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200 + 500)
            .style('opacity', 1);

        // Add axes
        g.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .style('text-anchor', 'middle')
            .style('font-size', '10px');

        g.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y).ticks(5));

        // Y-axis label
        g.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -40)
            .attr('x', -height / 2)
            .style('text-anchor', 'middle')
            .text('ROAS (Return on Ad Spend)');

        // Add hover effects
        g.selectAll('.bar')
            .on('mouseover', (event, d) => {
                this.tooltip
                    .style('visibility', 'visible')
                    .html(`
                        <strong>${d.name}</strong><br/>
                        ROAS: ${d.roas}x<br/>
                        Spend: $${this.formatNumber(d.spend)}<br/>
                        Conversions: ${this.formatNumber(d.conversions)}
                    `);
            })
            .on('mousemove', (event) => {
                this.tooltip
                    .style('top', (event.pageY - 10) + 'px')
                    .style('left', (event.pageX + 10) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.style('visibility', 'hidden');
            });
    }

    // 3. Performance Bubble Chart (CTR vs ROAS vs Spend)
    createPerformanceBubbleChart(data, containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = {top: 20, right: 20, bottom: 60, left: 60};
        const width = 350 - margin.left - margin.right;
        const height = 250 - margin.bottom - margin.top;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${350} ${300}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Scales
        const x = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.ctr) * 1.1])
            .range([0, width]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.roas) * 1.1])
            .range([height, 0]);

        const size = d3.scaleSqrt()
            .domain([0, d3.max(data, d => d.spend)])
            .range([10, 40]);

        // Add grid lines
        g.selectAll('.grid-line.horizontal')
            .data(y.ticks(5))
            .enter()
            .append('line')
            .attr('class', 'grid-line horizontal')
            .attr('x1', 0)
            .attr('x2', width)
            .attr('y1', d => y(d))
            .attr('y2', d => y(d));

        g.selectAll('.grid-line.vertical')
            .data(x.ticks(5))
            .enter()
            .append('line')
            .attr('class', 'grid-line vertical')
            .attr('x1', d => x(d))
            .attr('x2', d => x(d))
            .attr('y1', 0)
            .attr('y2', height);

        // Add bubbles with animation
        const bubbles = g.selectAll('.bubble')
            .data(data)
            .enter()
            .append('circle')
            .attr('class', 'bubble')
            .attr('cx', d => x(d.ctr))
            .attr('cy', d => y(d.roas))
            .attr('fill', d => this.colors[d.platform])
            .attr('r', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 300)
            .attr('r', d => size(d.spend));

        // Add bubble labels
        g.selectAll('.bubble-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'bubble-label')
            .attr('x', d => x(d.ctr))
            .attr('y', d => y(d.roas) + 4)
            .text(d => d.platform.charAt(0).toUpperCase())
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 300 + 500)
            .style('opacity', 1);

        // Add axes
        g.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x).tickFormat(d => `${d}%`));

        g.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y).tickFormat(d => `${d}x`));

        // Axis labels
        g.append('text')
            .attr('class', 'axis-label')
            .attr('x', width / 2)
            .attr('y', height + 45)
            .style('text-anchor', 'middle')
            .text('Click-Through Rate (CTR)');

        g.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -45)
            .attr('x', -height / 2)
            .style('text-anchor', 'middle')
            .text('Return on Ad Spend (ROAS)');

        // Add hover effects
        g.selectAll('.bubble')
            .on('mouseover', (event, d) => {
                this.tooltip
                    .style('visibility', 'visible')
                    .html(`
                        <strong>${d.name}</strong><br/>
                        CTR: ${d.ctr}%<br/>
                        ROAS: ${d.roas}x<br/>
                        Spend: $${this.formatNumber(d.spend)}<br/>
                        Conversions: ${this.formatNumber(d.conversions)}
                    `);
            })
            .on('mousemove', (event) => {
                this.tooltip
                    .style('top', (event.pageY - 10) + 'px')
                    .style('left', (event.pageX + 10) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.style('visibility', 'hidden');
            });
    }

    // 4. Time Series Performance Chart
    async createTimeSeriesChart(containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = {top: 20, right: 100, bottom: 40, left: 60};
        const width = 800 - margin.left - margin.right;
        const height = 300 - margin.bottom - margin.top;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${800} ${340}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Fetch real time series data
        const timeData = await this.fetchTimeSeriesData();

        // Scales
        const x = d3.scaleTime()
            .domain(d3.extent(timeData, d => d.date))
            .range([0, width]);

        const y = d3.scaleLinear()
            .domain([0, d3.max(timeData, d => Math.max(d.google, d.reddit, d.microsoft, d.linkedin)) * 1.1])
            .range([height, 0]);

        // Line generators
        const lineGoogle = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.google))
            .curve(d3.curveMonotoneX);

        const lineReddit = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.reddit))
            .curve(d3.curveMonotoneX);

        const lineMicrosoft = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.microsoft))
            .curve(d3.curveMonotoneX);

        const lineLinkedIn = d3.line()
            .x(d => x(d.date))
            .y(d => y(d.linkedin))
            .curve(d3.curveMonotoneX);

        // Add grid lines
        g.selectAll('.grid-line.horizontal')
            .data(y.ticks(5))
            .enter()
            .append('line')
            .attr('class', 'grid-line horizontal')
            .attr('x1', 0)
            .attr('x2', width)
            .attr('y1', d => y(d))
            .attr('y2', d => y(d));

        // Add lines with animation
        const pathGoogle = g.append('path')
            .datum(timeData)
            .attr('class', 'line google')
            .attr('d', lineGoogle)
            .style('stroke-dasharray', function() { return this.getTotalLength(); })
            .style('stroke-dashoffset', function() { return this.getTotalLength(); })
            .transition()
            .duration(2000)
            .style('stroke-dashoffset', 0);

        const pathReddit = g.append('path')
            .datum(timeData)
            .attr('class', 'line reddit')
            .attr('d', lineReddit)
            .style('stroke-dasharray', function() { return this.getTotalLength(); })
            .style('stroke-dashoffset', function() { return this.getTotalLength(); })
            .transition()
            .duration(2000)
            .delay(500)
            .style('stroke-dashoffset', 0);

        const pathMicrosoft = g.append('path')
            .datum(timeData)
            .attr('class', 'line microsoft')
            .attr('d', lineMicrosoft)
            .style('stroke-dasharray', function() { return this.getTotalLength(); })
            .style('stroke-dashoffset', function() { return this.getTotalLength(); })
            .transition()
            .duration(2000)
            .delay(1000)
            .style('stroke-dashoffset', 0);

        const pathLinkedIn = g.append('path')
            .datum(timeData)
            .attr('class', 'line linkedin')
            .attr('d', lineLinkedIn)
            .style('stroke-dasharray', function() { return this.getTotalLength(); })
            .style('stroke-dashoffset', function() { return this.getTotalLength(); })
            .transition()
            .duration(2000)
            .delay(1500)
            .style('stroke-dashoffset', 0);

        // Add dots
        ['google', 'reddit', 'microsoft', 'linkedin'].forEach((platform, platformIndex) => {
            g.selectAll(`.dot.${platform}`)
                .data(timeData)
                .enter()
                .append('circle')
                .attr('class', `dot ${platform}`)
                .attr('cx', d => x(d.date))
                .attr('cy', d => y(d[platform]))
                .attr('r', 0)
                .attr('fill', this.colors[platform])
                .transition()
                .duration(500)
                .delay((d, i) => platformIndex * 500 + i * 50 + 2000)
                .attr('r', 4);
        });

        // Add axes
        g.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x).tickFormat(d3.timeFormat('%m/%d')));

        g.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y).tickFormat(d => `$${this.formatNumber(d)}`));

        // Y-axis label
        g.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -45)
            .attr('x', -height / 2)
            .style('text-anchor', 'middle')
            .text('Daily Spend');

        // Add legend
        const legend = svg.append('g')
            .attr('class', 'legend')
            .attr('transform', `translate(${width + margin.left + 10}, ${margin.top + 20})`);

        const platforms = [
            {platform: 'google', name: 'Google Ads'},
            {platform: 'reddit', name: 'Reddit Ads'}, 
            {platform: 'microsoft', name: 'Microsoft Ads'},
            {platform: 'linkedin', name: 'LinkedIn Ads'}
        ];

        const legendItems = legend.selectAll('.legend-item')
            .data(platforms)
            .enter()
            .append('g')
            .attr('class', 'legend-item')
            .attr('transform', (d, i) => `translate(0, ${i * 20})`);

        legendItems.append('line')
            .attr('x1', 0)
            .attr('x2', 15)
            .attr('y1', 6)
            .attr('y2', 6)
            .style('stroke', d => this.colors[d.platform])
            .style('stroke-width', 3);

        legendItems.append('text')
            .attr('x', 20)
            .attr('y', 6)
            .attr('dy', '0.35em')
            .style('font-size', '12px')
            .style('fill', '#64748b')
            .text(d => d.name);
    }

    // Fetch real time series data from API
    async fetchTimeSeriesData() {
        try {
            const response = await fetch('/dashboard/timeseries?days=30');
            if (!response.ok) {
                throw new Error('Failed to fetch time series data');
            }
            
            const data = await response.json();
            console.log('Fetched time series data:', data);
            
            // Convert API response to format expected by D3 chart
            if (data.dates && data.google) {
                return data.dates.map((date, index) => ({
                    date: new Date(date),
                    google: data.google[index]?.spend || 0,
                    reddit: data.reddit[index]?.spend || 0,
                    microsoft: data.microsoft[index]?.spend || 0,
                    linkedin: data.linkedin[index]?.spend || 0
                }));
            } else {
                // Fallback to generated data if API format is unexpected
                return this.generateTimeSeriesData();
            }
        } catch (error) {
            console.error('Error fetching time series data:', error);
            return this.generateTimeSeriesData();
        }
    }

    // Helper method to generate time series data (fallback)
    generateTimeSeriesData() {
        const data = [];
        const endDate = new Date();
        
        for (let i = 29; i >= 0; i--) {
            const date = new Date(endDate);
            date.setDate(date.getDate() - i);
            
            data.push({
                date: date,
                google: 800 + Math.random() * 400 + Math.sin(i * 0.2) * 200,
                reddit: 200 + Math.random() * 150 + Math.cos(i * 0.15) * 75,
                microsoft: 180 + Math.random() * 120 + Math.sin(i * 0.18) * 60,
                linkedin: 120 + Math.random() * 80 + Math.cos(i * 0.22) * 40
            });
        }
        
        return data;
    }

    formatNumber(num) {
        if (num >= 1000000) {
            return (num / 1000000).toFixed(1) + 'M';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return Math.round(num).toString();
    }

    // 5. Conversions Bar Chart
    createConversionsBarChart(data, containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = {top: 20, right: 20, bottom: 60, left: 60};
        const width = 350 - margin.left - margin.right;
        const height = 250 - margin.bottom - margin.top;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${350} ${300}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Scales
        const x = d3.scaleBand()
            .domain(data.map(d => d.name))
            .range([0, width])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.conversions) * 1.1])
            .range([height, 0]);

        // Add bars with animation
        g.selectAll('.bar')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.name))
            .attr('width', x.bandwidth())
            .attr('fill', d => this.colors[d.platform])
            .attr('y', height)
            .attr('height', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200)
            .attr('y', d => y(d.conversions))
            .attr('height', d => height - y(d.conversions));

        // Add value labels on bars
        g.selectAll('.bar-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => x(d.name) + x.bandwidth() / 2)
            .attr('y', d => y(d.conversions) - 5)
            .text(d => this.formatNumber(d.conversions))
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200 + 500)
            .style('opacity', 1);

        // Add axes
        g.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .style('text-anchor', 'middle')
            .style('font-size', '10px');

        g.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y).ticks(5));

        // Y-axis label
        g.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -40)
            .attr('x', -height / 2)
            .style('text-anchor', 'middle')
            .text('Conversions');

        // Add hover effects
        g.selectAll('.bar')
            .on('mouseover', (event, d) => {
                this.tooltip
                    .style('visibility', 'visible')
                    .html(`
                        <strong>${d.name}</strong><br/>
                        Conversions: ${this.formatNumber(d.conversions)}<br/>
                        Spend: $${this.formatNumber(d.spend)}<br/>
                        Conversion Rate: ${(d.conversions / d.clicks * 100).toFixed(2)}%
                    `);
            })
            .on('mousemove', (event) => {
                this.tooltip
                    .style('top', (event.pageY - 10) + 'px')
                    .style('left', (event.pageX + 10) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.style('visibility', 'hidden');
            });
    }

    // 6. Impressions Bar Chart
    createImpressionsBarChart(data, containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = {top: 20, right: 20, bottom: 60, left: 80};
        const width = 350 - margin.left - margin.right;
        const height = 250 - margin.bottom - margin.top;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${350} ${300}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Scales
        const x = d3.scaleBand()
            .domain(data.map(d => d.name))
            .range([0, width])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.impressions) * 1.1])
            .range([height, 0]);

        // Add bars with animation
        g.selectAll('.bar')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.name))
            .attr('width', x.bandwidth())
            .attr('fill', d => this.colors[d.platform])
            .attr('y', height)
            .attr('height', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200)
            .attr('y', d => y(d.impressions))
            .attr('height', d => height - y(d.impressions));

        // Add value labels on bars
        g.selectAll('.bar-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => x(d.name) + x.bandwidth() / 2)
            .attr('y', d => y(d.impressions) - 5)
            .text(d => this.formatNumber(d.impressions))
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200 + 500)
            .style('opacity', 1);

        // Add axes
        g.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .style('text-anchor', 'middle')
            .style('font-size', '10px');

        g.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y).ticks(5).tickFormat(d => this.formatNumber(d)));

        // Y-axis label
        g.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -60)
            .attr('x', -height / 2)
            .style('text-anchor', 'middle')
            .text('Impressions');

        // Add hover effects
        g.selectAll('.bar')
            .on('mouseover', (event, d) => {
                this.tooltip
                    .style('visibility', 'visible')
                    .html(`
                        <strong>${d.name}</strong><br/>
                        Impressions: ${this.formatNumber(d.impressions)}<br/>
                        Clicks: ${this.formatNumber(d.clicks)}<br/>
                        CTR: ${d.ctr}%
                    `);
            })
            .on('mousemove', (event) => {
                this.tooltip
                    .style('top', (event.pageY - 10) + 'px')
                    .style('left', (event.pageX + 10) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.style('visibility', 'hidden');
            });
    }

    // 7. Cost Per Conversion Chart
    createCostPerConversionChart(data, containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = {top: 20, right: 20, bottom: 60, left: 80};
        const width = 350 - margin.left - margin.right;
        const height = 250 - margin.bottom - margin.top;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${350} ${300}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Calculate cost per conversion
        const dataWithCPC = data.map(d => ({
            ...d,
            costPerConversion: d.conversions > 0 ? d.spend / d.conversions : 0
        }));

        // Scales
        const x = d3.scaleBand()
            .domain(dataWithCPC.map(d => d.name))
            .range([0, width])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(dataWithCPC, d => d.costPerConversion) * 1.1])
            .range([height, 0]);

        // Add bars with animation
        g.selectAll('.bar')
            .data(dataWithCPC)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.name))
            .attr('width', x.bandwidth())
            .attr('fill', d => this.colors[d.platform])
            .attr('y', height)
            .attr('height', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200)
            .attr('y', d => y(d.costPerConversion))
            .attr('height', d => height - y(d.costPerConversion));

        // Add value labels on bars
        g.selectAll('.bar-label')
            .data(dataWithCPC)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => x(d.name) + x.bandwidth() / 2)
            .attr('y', d => y(d.costPerConversion) - 5)
            .text(d => `$${d.costPerConversion.toFixed(2)}`)
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200 + 500)
            .style('opacity', 1);

        // Add axes
        g.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .style('text-anchor', 'middle')
            .style('font-size', '10px');

        g.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y).ticks(5).tickFormat(d => `$${d.toFixed(0)}`));

        // Y-axis label
        g.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -60)
            .attr('x', -height / 2)
            .style('text-anchor', 'middle')
            .text('Cost Per Conversion');

        // Add hover effects
        g.selectAll('.bar')
            .on('mouseover', (event, d) => {
                this.tooltip
                    .style('visibility', 'visible')
                    .html(`
                        <strong>${d.name}</strong><br/>
                        Cost/Conversion: $${d.costPerConversion.toFixed(2)}<br/>
                        Total Spend: $${this.formatNumber(d.spend)}<br/>
                        Conversions: ${this.formatNumber(d.conversions)}
                    `);
            })
            .on('mousemove', (event) => {
                this.tooltip
                    .style('top', (event.pageY - 10) + 'px')
                    .style('left', (event.pageX + 10) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.style('visibility', 'hidden');
            });
    }

    // 8. Click-Through Rate Chart
    createCTRChart(data, containerId) {
        const container = d3.select(`#${containerId}`);
        container.selectAll("*").remove();

        const margin = {top: 20, right: 20, bottom: 60, left: 60};
        const width = 350 - margin.left - margin.right;
        const height = 250 - margin.bottom - margin.top;

        const svg = container
            .append('svg')
            .attr('viewBox', `0 0 ${350} ${300}`)
            .style('width', '100%')
            .style('height', '100%');

        const g = svg.append('g')
            .attr('transform', `translate(${margin.left}, ${margin.top})`);

        // Scales
        const x = d3.scaleBand()
            .domain(data.map(d => d.name))
            .range([0, width])
            .padding(0.2);

        const y = d3.scaleLinear()
            .domain([0, d3.max(data, d => d.ctr) * 1.2])
            .range([height, 0]);

        // Add bars with animation
        g.selectAll('.bar')
            .data(data)
            .enter()
            .append('rect')
            .attr('class', 'bar')
            .attr('x', d => x(d.name))
            .attr('width', x.bandwidth())
            .attr('fill', d => this.colors[d.platform])
            .attr('y', height)
            .attr('height', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200)
            .attr('y', d => y(d.ctr))
            .attr('height', d => height - y(d.ctr));

        // Add value labels on bars
        g.selectAll('.bar-label')
            .data(data)
            .enter()
            .append('text')
            .attr('class', 'bar-label')
            .attr('x', d => x(d.name) + x.bandwidth() / 2)
            .attr('y', d => y(d.ctr) - 5)
            .text(d => `${d.ctr}%`)
            .style('opacity', 0)
            .transition()
            .duration(1000)
            .delay((d, i) => i * 200 + 500)
            .style('opacity', 1);

        // Add target line (industry average)
        const targetCTR = 3.5;
        g.append('line')
            .attr('class', 'target-line')
            .attr('x1', 0)
            .attr('x2', width)
            .attr('y1', y(targetCTR))
            .attr('y2', y(targetCTR))
            .style('stroke', '#ff4444')
            .style('stroke-width', 2)
            .style('stroke-dasharray', '5,5');

        g.append('text')
            .attr('x', width - 80)
            .attr('y', y(targetCTR) - 5)
            .text('Industry Avg')
            .style('font-size', '10px')
            .style('fill', '#ff4444');

        // Add axes
        g.append('g')
            .attr('class', 'axis')
            .attr('transform', `translate(0, ${height})`)
            .call(d3.axisBottom(x))
            .selectAll('text')
            .style('text-anchor', 'middle')
            .style('font-size', '10px');

        g.append('g')
            .attr('class', 'axis')
            .call(d3.axisLeft(y).ticks(5).tickFormat(d => `${d}%`));

        // Y-axis label
        g.append('text')
            .attr('class', 'axis-label')
            .attr('transform', 'rotate(-90)')
            .attr('y', -40)
            .attr('x', -height / 2)
            .style('text-anchor', 'middle')
            .text('Click-Through Rate (%)');

        // Add hover effects
        g.selectAll('.bar')
            .on('mouseover', (event, d) => {
                this.tooltip
                    .style('visibility', 'visible')
                    .html(`
                        <strong>${d.name}</strong><br/>
                        CTR: ${d.ctr}%<br/>
                        Clicks: ${this.formatNumber(d.clicks)}<br/>
                        Impressions: ${this.formatNumber(d.impressions)}
                    `);
            })
            .on('mousemove', (event) => {
                this.tooltip
                    .style('top', (event.pageY - 10) + 'px')
                    .style('left', (event.pageX + 10) + 'px');
            })
            .on('mouseout', () => {
                this.tooltip.style('visibility', 'hidden');
            });
    }

    // Update all visualizations
    async updateVisualizations(platformData) {
        console.log('Updating all visualizations with platform data:', platformData);
        
        // Update static charts first
        this.createSpendDonutChart(platformData, 'spendDonutChart');
        this.createROASBarChart(platformData, 'roasBarChart');
        this.createConversionsBarChart(platformData, 'conversionsBarChart');
        this.createImpressionsBarChart(platformData, 'impressionsBarChart');
        this.createCostPerConversionChart(platformData, 'costPerConversionChart');
        this.createCTRChart(platformData, 'ctrChart');
        this.createPerformanceBubbleChart(platformData, 'performanceBubbleChart');
        
        // Update time series chart asynchronously
        await this.createTimeSeriesChart('timeSeriesChart');
    }
}

// Global D3 visualizations instance
window.d3Viz = new D3Visualizations();
