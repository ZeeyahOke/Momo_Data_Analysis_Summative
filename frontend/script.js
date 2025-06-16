// API Configuration
const API_BASE_URL = 'http://127.0.0.1:5000/api'; // Local Flask API URL

// DOM Elements
const transactionTypeFilter = document.getElementById('transactionTypeFilter');
const startDateFilter = document.getElementById('startDateFilter');
const endDateFilter = document.getElementById('endDateFilter');
const searchTextFilter = document.getElementById('searchTextFilter');
const applyFiltersBtn = document.getElementById('applyFiltersBtn');
const clearFiltersBtn = document.getElementById('clearFiltersBtn');
const transactionsTableBody = document.querySelector('#transactionsTable tbody');
const totalTransactionsElem = document.getElementById('totalTransactions');
const totalAmountElem = document.getElementById('totalAmount');
const averageAmountElem = document.getElementById('averageAmount');
const totalFeesElem = document.getElementById('totalFees');
const loadingIndicator = document.getElementById('loadingIndicator');
const errorDisplay = document.getElementById('errorDisplay');
const transactionModal = document.getElementById('transactionModal');
const closeModalBtn = document.querySelector('.close-button');
const modalBodyContent = document.getElementById('modalBodyContent');

// Chart instances
const charts = {
    typeChart: null,
    monthlyChart: null,
    paymentsChart: null
};

let currentTransactions = []; // Store current transactions for modal details

// Helper Functions
function formatCurrency(amount) {
    return `RF ${new Intl.NumberFormat('en-RW').format(amount)}`;
}

function showLoading() {
    if (loadingIndicator) loadingIndicator.style.display = 'block';
    if (errorDisplay) errorDisplay.style.display = 'none';
}

function hideLoading() {
    if (loadingIndicator) loadingIndicator.style.display = 'none';
}

function showError(message) {
    if (errorDisplay) {
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
    }
}

function hideError() {
    if (errorDisplay) errorDisplay.style.display = 'none';
}

// Data Fetching Functions
async function fetchTransactionTypes() {
    try {
        const response = await fetch(`${API_BASE_URL}/transaction-types`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const types = await response.json();
        if (transactionTypeFilter) {
            types.forEach(type => {
                const option = document.createElement('option');
                option.value = type.name;
                option.textContent = type.name;
                transactionTypeFilter.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Error fetching transaction types:', error);
        showError('Failed to load transaction types.');
    }
}

async function fetchTransactions(filters = {}) {
    let url = new URL(`${API_BASE_URL}/transactions`);
    for (const key in filters) {
        if (filters[key]) {
            url.searchParams.append(key, filters[key]);
        }
    }
    try {
        const response = await fetch(url, {
            method: 'GET',
            mode: 'cors',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching transactions:', error);
        showError('Failed to load transactions.');
        return [];
    }
}

async function fetchSummary() {
    try {
        const response = await fetch(`${API_BASE_URL}/summary`, {
            method: 'GET',
            mode: 'cors',
            credentials: 'include',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error('Error fetching summary:', error);
        showError('Failed to load summary statistics.');
        return null;
    }
}

// Rendering Functions
function renderTransactionsTable(transactions) {
    if (!transactionsTableBody) return;
    
    transactionsTableBody.innerHTML = ''; // Clear existing rows
    if (transactions.length === 0) {
        transactionsTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center;">No transactions found.</td></tr>';
        return;
    }

    transactions.forEach(transaction => {
        const row = transactionsTableBody.insertRow();
        row.innerHTML = `
            <td>${new Date(transaction.date).toLocaleDateString('en-RW', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</td>
            <td><span class="transaction-type">${transaction.type_name}</span></td>
            <td>${formatCurrency(transaction.amount)}</td>
            <td>${transaction.sender || 'N/A'}</td>
            <td>${transaction.receiver || 'N/A'}</td>
            <td><button class="view-details-btn" data-id="${transaction.id}">View Details</button></td>
        `;
    });

    // Add event listeners for view details buttons
    document.querySelectorAll('.view-details-btn').forEach(button => {
        button.addEventListener('click', (event) => {
            const transactionId = parseInt(event.target.dataset.id);
            const transaction = currentTransactions.find(t => t.id === transactionId);
            if (transaction) {
                showTransactionDetailsModal(transaction);
            }
        });
    });
}

function updateStatistics(summary) {
    if (!summary) return;
    
    if (totalTransactionsElem) totalTransactionsElem.textContent = summary.total_stats.total_transactions;
    if (totalAmountElem) totalAmountElem.textContent = formatCurrency(summary.total_stats.total_amount);
    if (averageAmountElem) averageAmountElem.textContent = formatCurrency(summary.total_stats.avg_amount);
    if (totalFeesElem) totalFeesElem.textContent = formatCurrency(summary.total_stats.total_fees);
}

function renderCharts(summary) {
    if (!summary) return;
    
    renderTransactionsByTypeChart(summary.transactions_by_type);
    renderMonthlyVolumeChart(summary.monthly_volume);
    renderPaymentsDepositsChart(summary.payments_deposits);
}

function renderTransactionsByTypeChart(typeCounts) {
    const ctx = document.getElementById('transactionsByTypeChart');
    if (!ctx) return;
    
    if (charts.typeChart) {
        charts.typeChart.destroy();
    }
    
    // MTN MoMo brand colors
    const colors = [
        '#ffcc00', '#00678f', '#ff6b35', '#4ecdc4', '#45b7d1',
        '#96ceb4', '#feca57', '#ff9ff3', '#54a0ff', '#5f27cd'
    ];
    
    charts.typeChart = new Chart(ctx.getContext('2d'), {
        type: 'doughnut',
        data: {
            labels: typeCounts.map(item => item.name),
            datasets: [{
                data: typeCounts.map(item => item.count),
                backgroundColor: colors.slice(0, typeCounts.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: {
                            size: 11
                        }
                    }
                }
            }
        }
    });
}

function renderMonthlyVolumeChart(monthlyData) {
    const ctx = document.getElementById('monthlyVolumeChart');
    if (!ctx) return;
    
    if (charts.monthlyChart) {
        charts.monthlyChart.destroy();
    }
    
    charts.monthlyChart = new Chart(ctx.getContext('2d'), {
        type: 'bar',
        data: {
            labels: monthlyData.map(item => item.month),
            datasets: [{
                label: 'Total Volume (RWF)',
                data: monthlyData.map(item => item.total_amount),
                backgroundColor: 'rgba(255, 204, 0, 0.8)', // MTN Yellow with transparency
                borderColor: '#ffcc00',
                borderWidth: 1,
                borderRadius: 4
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
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                }
            }
        }
    });
}

function renderPaymentsDepositsChart(paymentsDeposits) {
    const ctx = document.getElementById('paymentsDepositsChart');
    if (!ctx) return;
    
    if (charts.paymentsChart) {
        charts.paymentsChart.destroy();
    }
    
    charts.paymentsChart = new Chart(ctx.getContext('2d'), {
        type: 'pie',
        data: {
            labels: paymentsDeposits.map(item => item.category),
            datasets: [{
                data: paymentsDeposits.map(item => item.total_amount),
                backgroundColor: ['#ffcc00', '#00678f'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: {
                            size: 11
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            return `${context.label}: ${formatCurrency(value)}`;
                        }
                    }
                }
            }
        }
    });
}

// Event handlers
async function applyFilters() {
    showLoading();
    try {
        const filters = {
            type: transactionTypeFilter?.value,
            start_date: startDateFilter?.value,
            end_date: endDateFilter?.value,
            search: searchTextFilter?.value
        };

        const transactions = await fetchTransactions(filters);
        currentTransactions = transactions;
        renderTransactionsTable(transactions);
        hideLoading();
    } catch (error) {
        console.error('Error applying filters:', error);
        showError('Failed to apply filters.');
        hideLoading();
    }
}

function clearFilters() {
    if (transactionTypeFilter) transactionTypeFilter.value = 'all';
    if (startDateFilter) startDateFilter.value = '';
    if (endDateFilter) endDateFilter.value = '';
    if (searchTextFilter) searchTextFilter.value = '';
    applyFilters();
}

function showTransactionDetailsModal(transaction) {
    if (!transactionModal || !modalBodyContent) return;
    
    modalBodyContent.innerHTML = `
        <p><strong>Transaction ID:</strong> ${transaction.transaction_id}</p>
        <p><strong>Type:</strong> ${transaction.type_name}</p>
        <p><strong>Date:</strong> ${new Date(transaction.date).toLocaleString()}</p>
        <p><strong>Amount:</strong> ${formatCurrency(transaction.amount)}</p>
        ${transaction.fee ? `<p><strong>Fee:</strong> ${formatCurrency(transaction.fee)}</p>` : ''}
        ${transaction.balance ? `<p><strong>Balance:</strong> ${formatCurrency(transaction.balance)}</p>` : ''}
        <p><strong>Sender:</strong> ${transaction.sender || 'N/A'}</p>
        <p><strong>Receiver:</strong> ${transaction.receiver || 'N/A'}</p>
        <p><strong>Status:</strong> ${transaction.status || 'N/A'}</p>
        <p><strong>Raw Message:</strong></p>
        <pre>${transaction.raw_body}</pre>
    `;
    
    transactionModal.style.display = 'block';
}

function hideTransactionDetailsModal() {
    if (transactionModal) {
        transactionModal.style.display = 'none';
    }
}

// Initialize the dashboard
async function initializeDashboard() {
    showLoading();
    try {
        // Fetch initial data
        const [transactions, summary] = await Promise.all([
            fetchTransactions(),
            fetchSummary()
        ]);
        
        currentTransactions = transactions;
        
        // Update UI
        renderTransactionsTable(transactions);
        updateStatistics(summary);
        renderCharts(summary);
        
        // Load transaction types for filter
        await fetchTransactionTypes();
        
        hideLoading();
    } catch (error) {
        console.error('Error initializing dashboard:', error);
        showError('Failed to initialize dashboard.');
        hideLoading();
    }
}

// Add event listeners only if elements exist
if (applyFiltersBtn) {
    applyFiltersBtn.addEventListener('click', applyFilters);
}

if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', clearFilters);
}

if (closeModalBtn) {
    closeModalBtn.addEventListener('click', hideTransactionDetailsModal);
}

// Initialize the dashboard when the page loads
document.addEventListener('DOMContentLoaded', initializeDashboard);