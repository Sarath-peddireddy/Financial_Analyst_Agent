class FinancialAIApp {
    constructor() {
        this.apiBaseUrl = 'http://127.0.0.1:8000';
        this.chart = null;
        this.initializeElements();
        this.attachEventListeners();
        this.loadHistory();
    }

    initializeElements() {
        this.tickerInput = document.getElementById('ticker');
        this.questionInput = document.getElementById('question');
        this.askBtn = document.getElementById('askBtn');
        this.reportBtn = document.getElementById('reportBtn');
        this.fetchDataBtn = document.getElementById('fetchDataBtn');
        this.loadingSpinner = document.getElementById('loadingSpinner');
        this.answerContainer = document.getElementById('answerContainer');
        this.answerContent = document.getElementById('answerContent');
        this.sourcesInfo = document.getElementById('sourcesInfo');
        this.errorContainer = document.getElementById('errorContainer');
        this.errorMessage = document.getElementById('errorMessage');
        this.historyContainer = document.getElementById('historyContainer');
        
        // Stock widget elements
        this.stockQuoteContainer = document.getElementById('stockQuoteContainer');
        this.stockName = document.getElementById('stockName');
        this.stockPrice = document.getElementById('stockPrice');
        this.stockChange = document.getElementById('stockChange');
        this.stockSector = document.getElementById('stockSector');
        this.stockMarketCap = document.getElementById('stockMarketCap');
        this.stockPE = document.getElementById('stockPE');
        this.marketStatus = document.getElementById('marketStatus');
        this.priceChart = document.getElementById('priceChart');
    }

    attachEventListeners() {
        this.askBtn.addEventListener('click', () => this.handleAskQuestion());
        this.reportBtn.addEventListener('click', () => this.handleGenerateReport());
        this.fetchDataBtn.addEventListener('click', () => this.handleFetchLiveData());
        
        // Allow Enter key to submit
        this.questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleAskQuestion();
            }
        });

        // Auto-uppercase ticker input
        this.tickerInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
            
            // Auto-fetch data when ticker is entered (debounced)
            clearTimeout(this.fetchTimeout);
            this.fetchTimeout = setTimeout(() => {
                if (e.target.value.trim().length >= 2) {
                    this.handleFetchLiveData();
                }
            }, 1000);
        });
    }

    async handleFetchLiveData() {
        const ticker = this.tickerInput.value.trim();
        if (!ticker) return;

        try {
            // Fetch stock quote and company info
            const quoteResponse = await fetch(`${this.apiBaseUrl}/data/quote/${ticker}`);
            if (quoteResponse.ok) {
                const quoteData = await quoteResponse.json();
                this.updateStockWidget(quoteData);
            }

            // Fetch historical data for chart
            const historyResponse = await fetch(`${this.apiBaseUrl}/data/history/${ticker}?days=30`);
            if (historyResponse.ok) {
                const historyData = await historyResponse.json();
                this.updatePriceChart(historyData.history, ticker);
            }

        } catch (error) {
            console.error('Error fetching live data:', error);
        }
    }

    updateStockWidget(data) {
        const { quote, company_info, market_status } = data;
        
        if (quote.error) {
            this.stockQuoteContainer.classList.add('hidden');
            return;
        }

        // Update stock name and price
        this.stockName.textContent = company_info.name || data.ticker;
        this.stockPrice.textContent = `$${quote.price.toFixed(2)}`;
        
        // Update change with color coding
        const change = quote.change || 0;
        const changePercent = quote.change_percent || 0;
        const changeText = `${change >= 0 ? '+' : ''}$${change.toFixed(2)} (${changePercent.toFixed(2)}%)`;
        
        this.stockChange.textContent = changeText;
        this.stockChange.className = `stock-change ${change >= 0 ? 'positive' : 'negative'}`;
        
        // Update market status
        this.marketStatus.textContent = market_status.is_open ? 'Market Open' : 'Market Closed';
        this.marketStatus.className = `market-status ${market_status.is_open ? 'open' : 'closed'}`;
        
        // Update company details
        this.stockSector.textContent = company_info.sector || 'N/A';
        this.stockMarketCap.textContent = this.formatMarketCap(company_info.market_cap);
        this.stockPE.textContent = company_info.pe_ratio || 'N/A';
        
        this.stockQuoteContainer.classList.remove('hidden');
    }

    updatePriceChart(historyData, ticker) {
        if (!historyData || historyData.length === 0) return;

        const ctx = this.priceChart.getContext('2d');
        
        // Destroy existing chart
        if (this.chart) {
            this.chart.destroy();
        }

        const labels = historyData.map(item => {
            const date = new Date(item.date);
            return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        });
        
        const prices = historyData.map(item => item.close);
        
        // Determine line color based on overall trend
        const firstPrice = prices[0];
        const lastPrice = prices[prices.length - 1];
        const lineColor = lastPrice >= firstPrice ? '#10b981' : '#ef4444';

        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: `${ticker} Price`,
                    data: prices,
                    borderColor: lineColor,
                    backgroundColor: lineColor + '20',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: lineColor,
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        grid: {
                            color: '#e5e7eb'
                        },
                        ticks: {
                            callback: function(value) {
                                return '$' + value.toFixed(2);
                            }
                        }
                    },
                    x: {
                        grid: {
                            color: '#e5e7eb'
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });
    }

    validateInputs() {
        const ticker = this.tickerInput.value.trim();
        const question = this.questionInput.value.trim();

        if (!ticker) {
            this.showError('Please enter a stock ticker symbol');
            return false;
        }

        if (!question) {
            this.showError('Please enter your investment question');
            return false;
        }

        if (ticker.length > 10) {
            this.showError('Ticker symbol should be 10 characters or less');
            return false;
        }

        return true;
    }

    async handleAskQuestion() {
        if (!this.validateInputs()) return;

        const ticker = this.tickerInput.value.trim();
        const question = this.questionInput.value.trim();

        this.showLoading();
        this.disableButtons();

        try {
            const response = await fetch(`${this.apiBaseUrl}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ticker, question })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to get analysis');
            }

            const data = await response.json();
            this.showAnswer(data);
            
            // Update stock widget with fresh data
            if (data.stock_data && !data.stock_data.error) {
                this.updateStockWidget({
                    ticker: data.ticker,
                    quote: data.stock_data,
                    company_info: data.company_info || {},
                    market_status: { is_open: true } // Default assumption
                });
            }
            
            this.loadHistory(); // Refresh history

        } catch (error) {
            this.showError(`Error: ${error.message}`);
        } finally {
            this.hideLoading();
            this.enableButtons();
        }
    }

    async handleGenerateReport() {
        if (!this.validateInputs()) return;

        const ticker = this.tickerInput.value.trim();
        const question = this.questionInput.value.trim();

        this.showLoading();
        this.disableButtons();

        try {
            const response = await fetch(`${this.apiBaseUrl}/reports/stock`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ticker, question })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to generate report');
            }

            // Handle PDF download
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `investment_report_${ticker}_${new Date().getTime()}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);

            this.showSuccess('PDF report generated and downloaded successfully!');
            this.loadHistory(); // Refresh history

        } catch (error) {
            this.showError(`Error generating report: ${error.message}`);
        } finally {
            this.hideLoading();
            this.enableButtons();
        }
    }

    async loadHistory() {
        try {
            const response = await fetch(`${this.apiBaseUrl}/history?limit=5`);
            if (!response.ok) return;

            const data = await response.json();
            this.displayHistory(data.queries);

        } catch (error) {
            console.error('Failed to load history:', error);
        }
    }

    displayHistory(queries) {
        if (!queries || queries.length === 0) {
            this.historyContainer.innerHTML = '<p class="no-history">No queries yet. Ask your first investment question!</p>';
            return;
        }

        const historyHTML = queries.map(query => `
            <div class="history-item">
                <div class="history-ticker">${query.ticker}</div>
                <div class="history-question">${query.question}</div>
                <div class="history-answer">${this.truncateText(query.answer, 200)}</div>
                <div class="history-timestamp">${this.formatTimestamp(query.timestamp)}</div>
            </div>
        `).join('');

        this.historyContainer.innerHTML = historyHTML;
    }

    showAnswer(data) {
        this.hideError();
        this.answerContent.textContent = data.answer;
        
        const sourcesCount = data.context_sources ? data.context_sources.length : 0;
        const hasRealTimeData = data.stock_data && !data.stock_data.error;
        const dataSource = hasRealTimeData ? "real-time market data and" : "";
        this.sourcesInfo.textContent = `Analysis based on ${dataSource} ${sourcesCount} relevant sources`;
        
        this.answerContainer.classList.remove('hidden');
    }

    showError(message) {
        this.hideAnswer();
        this.errorMessage.textContent = message;
        this.errorContainer.classList.remove('hidden');
    }

    showSuccess(message) {
        this.hideError();
        this.answerContent.textContent = message;
        this.sourcesInfo.textContent = '';
        this.answerContainer.classList.remove('hidden');
    }

    showLoading() {
        this.hideAnswer();
        this.hideError();
        this.loadingSpinner.classList.remove('hidden');
    }

    hideLoading() {
        this.loadingSpinner.classList.add('hidden');
    }

    hideAnswer() {
        this.answerContainer.classList.add('hidden');
    }

    hideError() {
        this.errorContainer.classList.add('hidden');
    }

    disableButtons() {
        this.askBtn.disabled = true;
        this.reportBtn.disabled = true;
        this.fetchDataBtn.disabled = true;
    }

    enableButtons() {
        this.askBtn.disabled = false;
        this.reportBtn.disabled = false;
        this.fetchDataBtn.disabled = false;
    }

    formatMarketCap(marketCap) {
        if (!marketCap || marketCap === 'N/A') return 'N/A';
        
        const num = parseFloat(marketCap);
        if (isNaN(num)) return marketCap;
        
        if (num >= 1e12) return `$${(num / 1e12).toFixed(1)}T`;
        if (num >= 1e9) return `$${(num / 1e9).toFixed(1)}B`;
        if (num >= 1e6) return `$${(num / 1e6).toFixed(1)}M`;
        return `$${num.toFixed(0)}`;
    }

    truncateText(text, maxLength) {
        if (text.length <= maxLength) return text;
        return text.substring(0, maxLength) + '...';
    }

    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new FinancialAIApp();
});