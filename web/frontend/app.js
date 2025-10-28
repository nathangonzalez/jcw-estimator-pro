// JC Welton Construction - AI Cost Estimator
// Main Application JavaScript

const API_URL = 'https://jcw-cost-estimator-196950564738.us-central1.run.app';

// Global state
let currentEstimate = null;
let selectedFile = null;
let chatHistory = [];

// Initialize app
document.addEventListener('DOMContentLoaded', () => {
    checkAPIStatus();
    setupEventListeners();
});

// Check API Status
async function checkAPIStatus() {
    const statusDiv = document.getElementById('apiStatus');
    try {
        const response = await fetch(`${API_URL}/health`);
        if (response.ok) {
            const data = await response.json();
            statusDiv.className = 'api-status online';
            statusDiv.innerHTML = `<i class="fas fa-check-circle"></i> API Online${data.takeoff_available ? ' | AI Takeoff Ready' : ''}`;
        } else {
            throw new Error('API returned error');
        }
    } catch (error) {
        statusDiv.className = 'api-status offline';
        statusDiv.innerHTML = '<i class="fas fa-exclamation-circle"></i> API Offline';
    }
}

// Setup Event Listeners
function setupEventListeners() {
    // File upload
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    uploadArea.addEventListener('click', () => fileInput.click());
    uploadArea.addEventListener('dragover', handleDragOver);
    uploadArea.addEventListener('dragleave', handleDragLeave);
    uploadArea.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    
    // Blueprint analysis
    document.getElementById('analyzeBtn').addEventListener('click', analyzeBlueprint);
    
    // Manual form
    document.getElementById('estimateForm').addEventListener('submit', handleManualSubmit);
    
    // Export Excel
    document.getElementById('exportExcelBtn').addEventListener('click', exportToExcel);
    
    // Chat input
    document.getElementById('chatInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') sendChatMessage();
    });
}

// Tab Switching
function switchTab(tab) {
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');
    
    tabs.forEach(t => t.classList.remove('active'));
    contents.forEach(c => c.classList.remove('active'));
    
    if (tab === 'blueprint') {
        tabs[0].classList.add('active');
        document.getElementById('blueprintTab').classList.add('active');
    } else {
        tabs[1].classList.add('active');
        document.getElementById('manualTab').classList.add('active');
    }
}

// File Upload Handlers
function handleDragOver(e) {
    e.preventDefault();
    e.currentTarget.classList.add('dragover');
}

function handleDragLeave(e) {
    e.currentTarget.classList.remove('dragover');
}

function handleDrop(e) {
    e.preventDefault();
    const uploadArea = document.getElementById('uploadArea');
    uploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0 && files[0].type === 'application/pdf') {
        setSelectedFile(files[0]);
    } else {
        showAlert('uploadAlert', 'Please upload a PDF file', 'error');
    }
}

function handleFileSelect(e) {
    if (e.target.files.length > 0) {
        setSelectedFile(e.target.files[0]);
    }
}

function setSelectedFile(file) {
    selectedFile = file;
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('fileInfo').classList.add('show');
    document.getElementById('analyzeBtn').style.display = 'block';
}

// Analyze Blueprint
async function analyzeBlueprint() {
    if (!selectedFile) return;
    
    const loading = document.getElementById('uploadLoading');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const alert = document.getElementById('uploadAlert');
    
    loading.classList.add('show');
    analyzeBtn.disabled = true;
    alert.classList.remove('show');
    
    try {
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        const response = await fetch(`${API_URL}/takeoff`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Failed to analyze blueprint');
        }
        
        const data = await response.json();
        displayBlueprintResults(data);
        showAlert('uploadAlert', 'Blueprint analyzed successfully!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showAlert('uploadAlert', error.message, 'error');
    } finally {
        loading.classList.remove('show');
        analyzeBtn.disabled = false;
    }
}

// Display Blueprint Results
function displayBlueprintResults(data) {
    const resultsCard = document.getElementById('blueprintResults');
    const dataDiv = document.getElementById('blueprintData');
    
    let html = '<div class="result-card">';
    html += '<h3 class="result-title"><i class="fas fa-ruler"></i> Measurement Data</h3>';
    html += '<table class="data-table">';
    html += '<tr><th>Metric</th><th>Value</th></tr>';
    html += `<tr><td>Status</td><td>${data.status}</td></tr>`;
    html += `<tr><td>Scale Units</td><td>${data.scale_units}</td></tr>`;
    html += `<tr><td>Total Lines</td><td>${data.total_lines.toLocaleString()}</td></tr>`;
    html += `<tr><td>Total Polygons</td><td>${data.total_polygons.toLocaleString()}</td></tr>`;
    html += '</table></div>';
    
    dataDiv.innerHTML = html;
    resultsCard.style.display = 'block';
}

// Handle Manual Form Submit
async function handleManualSubmit(e) {
    e.preventDefault();
    
    const form = e.target;
    const loading = document.getElementById('resultsLoading');
    const resultsSection = document.getElementById('resultsSection');
    
    // Gather form data
    const formData = new FormData(form);
    const data = {
        area_sf: parseFloat(formData.get('area_sf')),
        project_type: formData.get('project_type'),
        finish_quality: formData.get('finish_quality'),
        design_complexity: formData.get('design_complexity'),
        bedrooms: parseInt(formData.get('bedrooms')) || 0,
        bathrooms: parseFloat(formData.get('bathrooms')) || 0,
        garage_bays: 0,
        windows: 0,
        doors: 0,
        special_features: []
    };
    
    // Gather special features
    const checkboxes = form.querySelectorAll('input[name="special_features"]:checked');
    checkboxes.forEach(cb => data.special_features.push(cb.value));
    
    loading.classList.add('show');
    resultsSection.classList.remove('show');
    
    try {
        const response = await fetch(`${API_URL}/estimate`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });
        
        if (!response.ok) {
            throw new Error('Failed to calculate estimate');
        }
        
        const result = await response.json();
        currentEstimate = result;
        displayEstimateResults(result);
        
    } catch (error) {
        console.error('Error:', error);
        showAlert('uploadAlert', 'Failed to calculate estimate. Please try again.', 'error');
    } finally {
        loading.classList.remove('show');
    }
}

// Display Estimate Results
function displayEstimateResults(result) {
    const estimate = result.rule_based_estimate;
    
    // Update cost breakdown
    document.getElementById('hardCosts').textContent = formatCurrency(estimate.hard_costs);
    document.getElementById('softCosts').textContent = formatCurrency(estimate.soft_costs);
    document.getElementById('costPerSf').textContent = formatCurrency(estimate.cost_per_sf);
    document.getElementById('totalCost').textContent = formatCurrency(estimate.total_cost);
    document.getElementById('confidence').textContent = result.confidence.toUpperCase();
    
    // Show results
    document.getElementById('resultsSection').classList.add('show');
    document.getElementById('exportExcelBtn').style.display = 'block';
    document.getElementById('aiChatCard').style.display = 'block';
    
    // Scroll to results
    document.getElementById('resultsSection').scrollIntoView({ behavior: 'smooth' });
}

// Format Currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(amount);
}

// Export to Excel
function exportToExcel() {
    if (!currentEstimate) return;
    
    const estimate = currentEstimate.rule_based_estimate;
    const timestamp = new Date().toISOString().split('T')[0];
    
    // Create workbook
    const wb = XLSX.utils.book_new();
    
    // Summary Sheet
    const summaryData = [
        ['JC Welton Construction - Cost Estimate'],
        ['Generated:', new Date().toLocaleString()],
        [],
        ['COST BREAKDOWN'],
        ['Hard Costs', estimate.hard_costs],
        ['Soft Costs (35%)', estimate.soft_costs],
        ['Cost per SF', estimate.cost_per_sf],
        [],
        ['TOTAL PROJECT COST', estimate.total_cost],
        [],
        ['Confidence Level', currentEstimate.confidence.toUpperCase()]
    ];
    
    const ws = XLSX.utils.aoa_to_sheet(summaryData);
    
    // Style the sheet
    ws['!cols'] = [{ width: 25 }, { width: 15 }];
    
    XLSX.utils.book_append_sheet(wb, ws, 'Cost Estimate');
    
    // Generate and download
    XLSX.writeFile(wb, `JCW_Cost_Estimate_${timestamp}.xlsx`);
    
    showAlert('uploadAlert', 'Excel file downloaded successfully!', 'success');
}

// AI Chat Functions
function sendChatMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    addChatMessage(message, 'user');
    input.value = '';
    
    // Simulate AI response (in production, this would call an AI endpoint)
    setTimeout(() => {
        const response = generateAIResponse(message);
        addChatMessage(response, 'ai');
    }, 1000);
}

function addChatMessage(message, sender) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${sender}`;
    
    if (sender === 'ai') {
        messageDiv.innerHTML = `<strong>AI Assistant:</strong><br>${message}`;
    } else {
        messageDiv.textContent = message;
    }
    
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function generateAIResponse(message) {
    // Simple response generator (in production, use actual AI)
    const lowerMessage = message.toLowerCase();
    
    if (lowerMessage.includes('adjust') || lowerMessage.includes('change')) {
        return 'I can help you adjust the estimate. What specific component would you like to modify? You can adjust:\n• Quality level\n• Special features\n• Square footage\n• Design complexity';
    } else if (lowerMessage.includes('explain') || lowerMessage.includes('breakdown')) {
        return 'The cost breakdown includes:\n• Hard Costs: Direct construction costs\n• Soft Costs (35%): Design, permits, fees, contingency\n• Total Cost: Complete project budget\n\nWould you like me to explain any specific component?';
    } else if (lowerMessage.includes('compare')) {
        return 'I can help you compare different scenarios. Would you like to:\n• Compare quality levels?\n• Compare with/without special features?\n• Compare different sizes?';
    } else {
        return 'I\'m here to help refine your estimate. You can ask me to:\n• Adjust specific costs\n• Explain the breakdown\n• Compare scenarios\n• Add or remove features\n\nWhat would you like to know?';
    }
}

// Feedback Functions
function submitFeedback(rating) {
    // Highlight selected rating
    document.querySelectorAll('.rating-btn').forEach(btn => {
        btn.classList.remove('selected');
    });
    event.target.classList.add('selected');
    
    console.log('Feedback submitted:', rating);
    showAlert('uploadAlert', `Thank you for your feedback! (${rating})`, 'success');
}

function submitDetailedFeedback() {
    const actualCost = document.getElementById('actualCost').value;
    const selectedRating = document.querySelector('.rating-btn.selected');
    
    if (!selectedRating && !actualCost) {
        showAlert('uploadAlert', 'Please provide a rating or actual cost', 'error');
        return;
    }
    
    const feedback = {
        estimate: currentEstimate,
        rating: selectedRating ? selectedRating.textContent.trim() : null,
        actual_cost: actualCost ? parseFloat(actualCost) : null,
        timestamp: new Date().toISOString()
    };
    
    console.log('Detailed feedback:', feedback);
    
    // In production, send to backend for ML training
    showAlert('uploadAlert', 'Feedback submitted! This will help improve our AI model.', 'success');
    
    // Reset form
    document.querySelectorAll('.rating-btn').forEach(btn => btn.classList.remove('selected'));
    document.getElementById('actualCost').value = '';
}

// Alert Helper
function showAlert(elementId, message, type) {
    const alert = document.getElementById(elementId);
    alert.className = `alert alert-${type} show`;
    alert.innerHTML = `<i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i> ${message}`;
    
    setTimeout(() => {
        alert.classList.remove('show');
    }, 5000);
}

// Make functions globally available
window.switchTab = switchTab;
window.sendChatMessage = sendChatMessage;
window.submitFeedback = submitFeedback;
window.submitDetailedFeedback = submitDetailedFeedback;
