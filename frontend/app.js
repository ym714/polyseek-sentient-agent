// Polyseek Sentient - Frontend Application

// Configuration
const CONFIG = {
    // Use relative URL for local development, absolute URL for production
    API_BASE_URL: window.location.protocol === 'file:' 
        ? 'http://localhost:8000/api' 
        : window.location.origin + '/api',
    MOCK_MODE: false, // Set to false when backend is ready
};

// State Management
const state = {
    currentAnalysis: null,
    trendingMarkets: [],
};

// ============================================
// DOM Elements
// ============================================
const elements = {
    analysisForm: document.getElementById('analysisForm'),
    marketUrl: document.getElementById('marketUrl'),
    depth: document.getElementById('depth'),
    perspective: document.getElementById('perspective'),
    marketsGrid: document.getElementById('marketsGrid'),
    resultsSection: document.getElementById('resultsSection'),
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingStatus: document.getElementById('loadingStatus'),
    markdownContent: document.getElementById('markdownContent'),
    jsonContent: document.getElementById('jsonContent'),
    closeResults: document.getElementById('closeResults'),
    toggleJson: document.getElementById('toggleJson'),
};

// ============================================
// Initialization
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Clear input field on page load
    elements.marketUrl.value = '';
    initEventListeners();
    loadTrendingMarkets();
});

// ============================================
// Event Listeners
// ============================================
function initEventListeners() {
    // Form submission
    elements.analysisForm.addEventListener('submit', handleFormSubmit);

    // Close results
    elements.closeResults.addEventListener('click', hideResults);

    // Toggle JSON
    elements.toggleJson.addEventListener('click', () => {
        elements.jsonContent.classList.toggle('hidden');
        const isHidden = elements.jsonContent.classList.contains('hidden');
        elements.toggleJson.querySelector('span').textContent = isHidden ? 'Show Raw JSON' : 'Hide Raw JSON';
    });
}

// ============================================
// Form Handling
// ============================================
async function handleFormSubmit(e) {
    e.preventDefault();

    const marketUrl = elements.marketUrl.value.trim();
    const depth = elements.depth.value;
    const perspective = elements.perspective.value;

    if (!marketUrl) {
        showError('Please enter a valid market URL');
        return;
    }

    await analyzeMarket(marketUrl, depth, perspective);
}

// ============================================
// API Calls
// ============================================
async function analyzeMarket(marketUrl, depth, perspective) {
    showLoading();
    updateLoadingStatus('Initializing analysis...');

    try {
        if (CONFIG.MOCK_MODE) {
            await simulateAnalysis(marketUrl, depth, perspective);
        } else {
            const response = await fetch(`${CONFIG.API_BASE_URL}/analyze`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    market_url: marketUrl,
                    depth: depth,
                    perspective: perspective,
                }),
            });

            if (!response.ok) {
                throw new Error(`API error: ${response.status}`);
            }

            const data = await response.json();
            displayResults(data);
        }
    } catch (error) {
        console.error('Analysis error:', error);
        showError('Failed to analyze market. Please try again.');
    } finally {
        hideLoading();
    }
}

// Fallback mock markets
const getMockMarkets = () => [
    {
        id: 1,
        title: 'Will Bitcoin hit $100k in 2024?',
        price: '0.65',
        volume: '$12M',
        url: 'https://polymarket.com/event/will-bitcoin-hit-100k-in-2024',
    },
    {
        id: 2,
        title: 'Russia x Ukraine Ceasefire in 2025?',
        price: '0.15',
        volume: '$5M',
        url: 'https://polymarket.com/event/russia-x-ukraine-ceasefire-in-2025',
    },
    {
        id: 3,
        title: 'Will AI surpass human performance in coding by 2026?',
        price: '0.42',
        volume: '$1.8M',
        url: 'https://polymarket.com/event/ai-coding-2026',
    },
];

async function loadTrendingMarkets() {
    // Always try to use mock markets first if MOCK_MODE is enabled
    if (CONFIG.MOCK_MODE) {
        const mockMarkets = getMockMarkets();
        renderTrendingMarkets(mockMarkets);
        return;
    }

    // Try to fetch from API with fallback to mock data
    try {
        // Create timeout promise
        const timeoutPromise = new Promise((_, reject) => {
            setTimeout(() => reject(new Error('Request timeout')), 5000);
        });

        const fetchPromise = fetch(`${CONFIG.API_BASE_URL}/trending`, {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
        });

        const response = await Promise.race([fetchPromise, timeoutPromise]);

        if (!response.ok) {
            throw new Error(`API returned ${response.status}: ${response.statusText}`);
        }

        const markets = await response.json();
        console.log('API response:', markets);

        // Validate response
        if (Array.isArray(markets) && markets.length > 0) {
            renderTrendingMarkets(markets);
        } else {
            throw new Error('Invalid API response format');
        }
    } catch (error) {
        console.warn('Failed to load trending markets from API, using fallback:', error);
        // Fallback to mock markets on error
        const mockMarkets = getMockMarkets();
        renderTrendingMarkets(mockMarkets);
    }
}

// ============================================
// UI Rendering
// ============================================
function renderTrendingMarkets(markets) {
    if (!markets || markets.length === 0) {
        // Fallback to mock markets if empty
        const mockMarkets = getMockMarkets();
        console.warn('No markets provided, using fallback');
        renderTrendingMarkets(mockMarkets);
        return;
    }

    // Show only first 3 markets
    const displayMarkets = markets.slice(0, 3);
    console.log('Displaying markets:', displayMarkets.length, displayMarkets);

    elements.marketsGrid.innerHTML = displayMarkets.map(market => `
    <div class="group relative bg-white/5 backdrop-blur-sm border border-white/10 rounded-xl p-5 hover:bg-white/10 transition-all duration-300 cursor-pointer hover:scale-[1.02] hover:shadow-xl hover:shadow-purple-500/10" onclick="selectMarket('${market.url}')">
      <div class="flex justify-between items-start mb-4">
        <h3 class="text-lg font-medium text-white/90 group-hover:text-white line-clamp-2 min-h-[3.5rem]">${market.title}</h3>
      </div>
      <div class="flex items-center justify-between pt-4 border-t border-white/5">
        <div class="flex flex-col">
          <span class="text-xs text-neutral-500 uppercase tracking-wider">Price</span>
          <span class="text-xl font-bold text-white bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">${market.price}</span>
        </div>
        <div class="flex flex-col items-end">
          <span class="text-xs text-neutral-500 uppercase tracking-wider">Volume</span>
          <span class="text-sm font-medium text-neutral-300">${market.volume}</span>
        </div>
      </div>
    </div>
  `).join('');
}

function displayResults(data) {
    state.currentAnalysis = data;

    // Render Markdown
    if (data.markdown) {
        elements.markdownContent.innerHTML = marked.parse(data.markdown);
    }

    // Render JSON
    if (data.json) {
        elements.jsonContent.textContent = JSON.stringify(data.json, null, 2);
    }

    // Show results section
    showResults();

    // Scroll to results
    setTimeout(() => {
        elements.resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

function showResults() {
    elements.resultsSection.classList.remove('hidden');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function hideResults() {
    elements.resultsSection.classList.add('hidden');
    document.body.style.overflow = '';
}

function showLoading() {
    elements.loadingOverlay.classList.remove('hidden');
}

function hideLoading() {
    elements.loadingOverlay.classList.add('hidden');
}

function updateLoadingStatus(message) {
    elements.loadingStatus.textContent = message;
}

function showError(message) {
    alert(message);
}

function selectMarket(url) {
    // Clear any existing value and set the new URL
    elements.marketUrl.value = '';
    setTimeout(() => {
        elements.marketUrl.value = url;
        elements.marketUrl.focus();
    }, 10);
    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// ============================================
// Utilities
// ============================================
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Mock Simulation (kept for fallback)
async function simulateAnalysis(marketUrl, depth, perspective) {
    const stages = ['Fetching market...', 'Reading news...', 'Analyzing signals...', 'Finalizing report...'];
    for (const stage of stages) {
        updateLoadingStatus(stage);
        await sleep(800);
    }

    displayResults({
        markdown: `# Analysis for ${marketUrl}\n\nThis is a mock analysis result.`,
        json: {
            analysis: {
                base_rate: 0.5,
                probability_trace: [
                    { title: "News Positive", posterior_prob: 0.6 },
                    { title: "Expert Doubt", posterior_prob: 0.55 }
                ]
            }
        }
    });
}
