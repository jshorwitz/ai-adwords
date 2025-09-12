# Dual-Product Campaign Structure: Code Search + Amp AI

## 🎯 Strategic Overview

Successfully restructured the Google Ads campaign architecture to cleanly separate **Code Search** (Sourcegraph's core product) and **Amp** (the new AI Code Assistant), enabling targeted marketing, budget allocation, and performance tracking for each product line.

## 📊 Campaign Architecture

### **Total Budget**: $1,600/day across 10 campaigns

```
🔍 CODE SEARCH PRODUCT LINE (40.3% - $645/day)
├── Brand: Code Search Brand - Global ($120/day)
├── Enterprise: Enterprise Code Search - NA ($250/day) 
├── Competitor: Code Search Competitors - Global ($150/day)
└── Category: Code Discovery Tools - Global ($125/day)

🤖 AMP AI PRODUCT LINE (40.9% - $655/day)
├── Brand: Amp AI Brand - Global ($130/day)
├── Category: AI Coding Assistant - Global ($200/day)
├── Competitor: Amp AI Competitors - Global ($175/day) 
└── Productivity: AI Developer Productivity - Global ($150/day)

🌍 SHARED/CROSS-PRODUCT (18.8% - $300/day)
├── Performance Max: Dual Product ($200/day)
└── Geographic: Expansion - EMEA ($100/day)
```

## 🔍 Code Search Product Line (4 campaigns)

### 1. **25Q1 - Code Search Brand - Global** ($120/day)
- **Purpose**: Brand awareness for Sourcegraph's core code search product
- **Keywords**: `sourcegraph`, `sourcegraph code search`, `source graph`
- **Match Types**: EXACT, PHRASE
- **Bidding**: MAXIMIZE_CONVERSION_VALUE
- **Landing Page**: Code search focused

### 2. **25Q1 - Enterprise Code Search - NA** ($250/day)
- **Purpose**: Target enterprise customers needing large-scale code search
- **Keywords**: `enterprise code search`, `code search platform`, `large codebase search`
- **Match Types**: PHRASE, BROAD
- **Bidding**: MAXIMIZE_CONVERSION_VALUE
- **Landing Page**: Enterprise code search focused

### 3. **25Q1 - Code Search Competitors - Global** ($150/day)
- **Purpose**: Capture users searching for competing code search solutions
- **Keywords**: `github search`, `gitlab search`, `bitbucket search`, `azure devops search`
- **Match Types**: PHRASE, BROAD
- **Bidding**: MAXIMIZE_CONVERSIONS
- **Landing Page**: Code search vs competitors

### 4. **25Q1 - Code Discovery Tools - Global** ($125/day)
- **Purpose**: Generic code search and discovery tool seekers
- **Keywords**: `code search`, `search codebase`, `find code`, `code navigation`
- **Match Types**: PHRASE, BROAD
- **Bidding**: MAXIMIZE_CONVERSIONS
- **Landing Page**: Code discovery focused

## 🤖 Amp AI Product Line (4 campaigns)

### 1. **25Q1 - Amp AI Brand - Global** ($130/day)
- **Purpose**: Brand awareness for Amp AI coding assistant
- **Keywords**: `amp coding`, `amp ai`, `ampcode`, `sourcegraph amp`
- **Match Types**: EXACT, PHRASE
- **Bidding**: MAXIMIZE_CONVERSION_VALUE
- **Landing Page**: Amp product focused

### 2. **25Q1 - AI Coding Assistant - Global** ($200/day)
- **Purpose**: Generic AI coding assistant market
- **Keywords**: `ai coding assistant`, `autonomous coding`, `ai code generation`, `agentic coding`
- **Match Types**: PHRASE, BROAD
- **Bidding**: MAXIMIZE_CONVERSIONS
- **Landing Page**: AI coding assistant focused

### 3. **25Q1 - Amp AI Competitors - Global** ($175/day)
- **Purpose**: Compete against other AI coding tools
- **Keywords**: `cursor ai`, `github copilot`, `claude dev`, `aider ai`, `windsurf ai`
- **Match Types**: PHRASE, BROAD
- **Bidding**: MAXIMIZE_CONVERSIONS
- **Landing Page**: Amp vs competitors

### 4. **25Q1 - AI Developer Productivity - Global** ($150/day)
- **Purpose**: AI-powered developer productivity tools
- **Keywords**: `ai developer tools`, `coding automation`, `ai pair programming`, `code refactoring ai`
- **Match Types**: PHRASE, BROAD
- **Bidding**: MAXIMIZE_CONVERSIONS
- **Landing Page**: Developer productivity AI focused

## 🌍 Shared/Cross-Product Campaigns (2 campaigns)

### 1. **25Q1 - Performance Max - Dual Product** ($200/day)
- **Purpose**: Display/remarketing for both products using Google's automation
- **Channel**: PERFORMANCE_MAX
- **Bidding**: MAXIMIZE_CONVERSION_VALUE
- **Landing Page**: Multi-product focused

### 2. **25Q1 - Geographic Expansion - EMEA** ($100/day)
- **Purpose**: International expansion for both products
- **Keywords**: `sourcegraph`, `amp coding`, `code search platform`
- **Match Types**: EXACT, PHRASE
- **Bidding**: MAXIMIZE_CONVERSIONS
- **Landing Page**: Regional landing page

## 🎯 Strategic Benefits

### **Clear Product Separation**
- **Independent Tracking**: Measure Code Search vs Amp performance separately
- **Targeted Messaging**: Product-specific ad copy and landing pages
- **Budget Flexibility**: Allocate spend based on each product's ROI

### **Competitive Intelligence**
- **Code Search Competitors**: GitHub, GitLab, Bitbucket search capabilities
- **Amp AI Competitors**: Cursor, Copilot, Claude Dev, Aider, Windsurf
- **Differentiated Positioning**: Unique value props for each product line

### **Balanced Investment**
- **Code Search**: 40.3% budget allocation (mature product, enterprise focus)
- **Amp AI**: 40.9% budget allocation (new product, growth investment)
- **Shared**: 18.8% budget allocation (cross-selling, international)

## 🔄 Intelligent Consolidation Logic

The system now intelligently maps existing campaigns to the appropriate product line:

### **Amp AI Product Detection**
- Campaign names containing: `amp`, `cody`, `ai coding`, `autonomous`, `agentic`
- Competitor terms: `cursor`, `copilot`, `claude dev`, `aider`, `windsurf`
- AI productivity: `ai developer`, `coding automation`, `ai pair`

### **Code Search Product Detection**
- Campaign names containing: `brand`, `sourcegraph` (excluding amp)
- Enterprise search: `enterprise` + `code search`/`search`
- Search competitors: `github search`, `gitlab search`, `bitbucket search`
- Discovery terms: `code search`, `search codebase`, `find code`

### **Smart Fallback Logic**
- AI/ML keywords → Route to Amp AI campaigns
- Traditional search keywords → Route to Code Search campaigns
- Geographic terms → Shared campaigns
- Performance Max → Shared campaigns

## 📈 Expected Outcomes

### **Code Search Product Line**
- **Enterprise Focus**: Higher budgets for enterprise search ($250/day)
- **Brand Protection**: Dedicated brand campaign for Sourcegraph
- **Competitive Defense**: Direct competition against GitHub/GitLab search

### **Amp AI Product Line**  
- **Market Expansion**: Capture growing AI coding assistant market
- **Competitive Position**: Direct competition against Cursor/Copilot
- **Innovation Messaging**: Emphasize agentic/autonomous coding capabilities

### **Performance Tracking**
- **Product-Level Metrics**: Separate conversion tracking for each product
- **Budget Optimization**: Reallocate between products based on performance
- **A/B Testing**: Product-specific landing page and ad copy tests

## 🚀 Implementation Ready

The dual-product campaign structure is now implemented and ready for execution:

```bash
# Test the new structure
ADS_USE_MOCK=1 poetry run python -m src.cli consolidate-campaigns --customer-id 9639990200

# Execute when ready
poetry run python -m src.cli consolidate-campaigns --customer-id 9639990200 --no-dry-run
```

This structure provides clear separation between Code Search and Amp while maintaining strategic shared campaigns for cross-product synergies and international expansion.
