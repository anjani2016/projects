// VoltShift Ontario - Home Battery ULO Arbitrage Simulator Logic

// Global Constants
const DAYS_WEEKDAY = 251;
const DAYS_WEEKEND = 114;

// Ontario Regulated Price Plan (RPP) Rates (Nov 1, 2025 - Oct 31, 2026) in $/kWh
const RATES = {
    ULO: {
        OVERNIGHT: 0.039,  // 11 PM - 7 AM (daily)
        WEEKEND: 0.098,    // 7 AM - 11 PM (weekends/holidays)
        MID_PEAK: 0.157,   // 7 AM - 4 PM & 9 PM - 11 PM (weekdays)
        ON_PEAK: 0.391     // 4 PM - 9 PM (weekdays)
    },
    TOU: {
        OFF_PEAK: 0.098,   // Weekends all day, weekdays 7 PM - 7 AM
        MID_PEAK: 0.157,   // Weekdays 7 AM - 11 AM & 5 PM - 7 PM
        ON_PEAK: 0.203     // Weekdays 11 AM - 5 PM
    }
};

// Typical Household Load Profile Distribution
// Peak hours (4 PM - 9 PM) represent 5 hours. Residential homes consume about 30% of daily load here.
const PROFILE = {
    TOU: { ON_PEAK: 0.20, MID_PEAK: 0.25, OFF_PEAK: 0.55 },
    ULO_BASE: { ON_PEAK: 0.30, MID_PEAK: 0.30, OVERNIGHT: 0.20, WEEKEND: 0.20 }
};

// Market Battery Catalogue
const MARKET_BATTERIES = [
    {
        id: 'tesla-pw3',
        name: 'Powerwall 3',
        brand: 'Tesla',
        capacity: 13.5,
        efficiency: 90,
        cost: 14500,
        cycles: 10000,
        width: 61,
        depth: 19,
        height: 110,
        url: 'https://www.tesla.com/powerwall'
    },
    {
        id: 'enphase-5p',
        name: 'IQ Battery 5P',
        brand: 'Enphase',
        capacity: 5.0,
        efficiency: 89,
        cost: 6800,
        cycles: 8000,
        width: 55,
        depth: 16,
        height: 98,
        url: 'https://enphase.com/batteries/iq-battery-5p'
    },
    {
        id: 'lg-prime16',
        name: 'LG Energy Prime 16H',
        brand: 'LG',
        capacity: 16.0,
        efficiency: 90,
        cost: 15800,
        cycles: 6000,
        width: 70,
        depth: 21,
        height: 120,
        url: 'https://www.lgessbattery.com/us/home-battery/product-info.lg'
    },
    {
        id: 'ep-cube',
        name: 'EP Cube Lite',
        brand: 'EP Cube',
        capacity: 9.9,
        efficiency: 88,
        cost: 10500,
        cycles: 6000,
        width: 60,
        depth: 22,
        height: 100,
        url: 'https://epcube.com/'
    }
];

let selectedBatteryId = null; // Cleared by default until selected
let chartInstance = null;
let currentStep = 1;

// DOM Elements
const capInput = document.getElementById('battery-capacity');
const effInput = document.getElementById('battery-efficiency');
const degradationInput = document.getElementById('battery-degradation');
const costInput = document.getElementById('installed-cost');
const loadInput = document.getElementById('daily-load');
const evToggle = document.getElementById('shift-ev');

const capVal = document.getElementById('capacity-val');
const effVal = document.getElementById('efficiency-val');
const degradationVal = document.getElementById('degradation-val');
const costVal = document.getElementById('cost-val');

const statAnnualSavings = document.getElementById('stat-annual-savings');
const statComparisonTou = document.getElementById('stat-comparison-tou');
const statPayback = document.getElementById('stat-payback');
const statRoiPct = document.getElementById('stat-roi-pct');
const stat10yrNet = document.getElementById('stat-10yr-net');

// New DOM Elements
const billM1 = document.getElementById('bill-m1');
const billM2 = document.getElementById('bill-m2');
const billM3 = document.getElementById('bill-m3');
const billAvgDisplay = document.getElementById('bill-avg-display');
const billUpload = document.getElementById('bill-upload');
const uploadZone = document.getElementById('upload-zone');
const ocrLoader = document.getElementById('ocr-loader');
const uploadText = document.getElementById('upload-text');

const spaceWidth = document.getElementById('space-width');
const spaceDepth = document.getElementById('space-depth');
const spaceHeight = document.getElementById('space-height');

const marketGrid = document.getElementById('market-batteries-grid');
const sizingSuggestion = document.getElementById('sizing-suggestion');

const detailChargeCost = document.getElementById('detail-charge-cost');
const detailAvoidanceSavings = document.getElementById('detail-avoidance-savings');
const detailEvYield = document.getElementById('detail-ev-yield');
const detailCycleLimit = document.getElementById('detail-cycle-limit');
const detailCycleDesc = document.getElementById('detail-cycle-desc');

// Step Navigation buttons
const btnFindBatteries = document.getElementById('btn-find-batteries');
const btnBackToStep1 = document.getElementById('btn-back-to-step-1');
const btnBackToStep2 = document.getElementById('btn-back-to-step-2');
const btnGoToStep4 = document.getElementById('btn-go-to-step-4');
const btnBackToStep3 = document.getElementById('btn-back-to-step-3');
const btnRecalculate = document.getElementById('btn-recalculate');

// Format Currency
function formatCurrency(val) {
    return new Intl.NumberFormat('en-CA', { style: 'currency', currency: 'CAD', maximumFractionDigits: 0 }).format(val);
}

// Wizard Step Controller
function goToStep(stepNumber) {
    currentStep = stepNumber;
    
    // Toggle active step in UI
    document.querySelectorAll('.wizard-step').forEach(step => {
        step.classList.remove('active');
    });
    
    const activeStepEl = document.getElementById(`step-${stepNumber}`);
    if (activeStepEl) {
        activeStepEl.classList.add('active');
    }

    // Toggle active navigation tab in UI
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    const activeTabEl = document.getElementById(`nav-tab-${stepNumber}`);
    if (activeTabEl) {
        activeTabEl.classList.add('active');
    }
    
    // Scroll window smoothly to container top
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Conditional calculations
    if (stepNumber === 2) {
        const m1 = parseFloat(billM1.value) || 0;
        const m2 = parseFloat(billM2.value) || 0;
        const m3 = parseFloat(billM3.value) || 0;
        const avgVal = (m1 + m2 + m3) / 3;
        
        let displayMonthly, displayDaily, displayPeak;
        const inputType = document.getElementById('bill-input-type').value;

        if (inputType === 'total') {
            displayMonthly = avgVal;
            displayDaily = avgVal / 30.4;
            displayPeak = displayDaily * PROFILE.ULO_BASE.ON_PEAK;
        } else {
            // They input peak values directly
            displayPeak = avgVal / 30.4; // Average peak consumption per day
            displayDaily = displayPeak / PROFILE.ULO_BASE.ON_PEAK; // Reconstruct total daily consumption
            displayMonthly = displayDaily * 30.4;
        }

        // Update Step 2 Energy Profile Summary Cards
        document.getElementById('summary-monthly-load').innerText = `${Math.round(displayMonthly)} kWh`;
        document.getElementById('summary-daily-load').innerText = `${displayDaily.toFixed(1)} kWh`;
        document.getElementById('summary-peak-load').innerText = `${displayPeak.toFixed(1)} kWh / day`;

        // Update hidden load input for logic calculations
        loadInput.value = Math.max(10, Math.min(100, Math.round(displayDaily)));

        const suggestedCap = Math.max(5, Math.ceil(displayPeak * 1.2 * 2) / 2);
        sizingSuggestion.innerText = `Suggested Size: ${suggestedCap.toFixed(1)} kWh`;
        renderMarketSuggestions(suggestedCap);
    } else if (stepNumber === 3) {
        calculateROI();
    }
}

// Update Daily Avg from Manual Inputs or OCR
function updateAvgFromBills() {
    const m1 = parseFloat(billM1.value) || 0;
    const m2 = parseFloat(billM2.value) || 0;
    const m3 = parseFloat(billM3.value) || 0;
    
    const avgMonthly = (m1 + m2 + m3) / 3;
    const inputType = document.getElementById('bill-input-type').value;
    
    let avgDailyVal;
    if (inputType === 'total') {
        avgDailyVal = avgMonthly / 30.4;
    } else {
        // peak input converted to estimated daily average
        avgDailyVal = (avgMonthly / 30.4) / PROFILE.ULO_BASE.ON_PEAK;
    }
    
    billAvgDisplay.innerText = avgDailyVal.toFixed(1);
    loadInput.value = Math.max(10, Math.min(100, Math.round(avgDailyVal)));
}

// Perform calculation
function calculateROI() {
    const capacity = parseFloat(capInput.value);
    const efficiency = parseFloat(effInput.value) / 100;
    const degradation = parseFloat(degradationInput.value) / 100;
    const cost = parseFloat(costInput.value);
    const dailyLoad = parseFloat(loadInput.value);
    const hasEvShift = evToggle.checked;

    // Update Slider Value Displays
    capVal.innerText = capacity.toFixed(1);
    effVal.innerText = effInput.value;
    degradationVal.innerText = degradationInput.value;
    costVal.innerText = parseFloat(costInput.value).toLocaleString('en-CA');

    // 1. Calculate Standard TOU baseline annual cost (Without Battery)
    const dailyTouCost = dailyLoad * (
        PROFILE.TOU.ON_PEAK * RATES.TOU.ON_PEAK +
        PROFILE.TOU.MID_PEAK * RATES.TOU.MID_PEAK +
        PROFILE.TOU.OFF_PEAK * RATES.TOU.OFF_PEAK
    );
    const annualTouCost = dailyTouCost * 365;

    // 2. Battery Arbitrage Math (ULO Weekdays)
    const peakUsage = dailyLoad * PROFILE.ULO_BASE.ON_PEAK;
    const usableDischarge = Math.min(capacity, peakUsage);
    
    // Day-to-day weekday battery loop
    const dailyChargeCost = (usableDischarge / efficiency) * RATES.ULO.OVERNIGHT;
    const offsetSavings = usableDischarge * RATES.ULO.ON_PEAK;
    const netDailyArbitrageSavings = offsetSavings - dailyChargeCost;
    const annualBatterySavings = netDailyArbitrageSavings * DAYS_WEEKDAY;

    // Detailed metrics for UI display
    const annualChargeCost = dailyChargeCost * DAYS_WEEKDAY;
    const annualAvoidanceSavings = offsetSavings * DAYS_WEEKDAY;

    // 3. EV Shift Math
    const annualEvSavings = hasEvShift ? (3000 * (RATES.TOU.OFF_PEAK - RATES.ULO.OVERNIGHT)) : 0;

    // Total Annual Savings
    const totalAnnualSavings = annualBatterySavings + annualEvSavings;
    
    // Payback & ROI
    const payback = totalAnnualSavings > 0 ? (cost / totalAnnualSavings) : 99;
    const roi = cost > 0 ? (totalAnnualSavings / cost) * 100 : 0;

    // Update UI Stats
    statAnnualSavings.innerText = formatCurrency(totalAnnualSavings);
    statComparisonTou.innerHTML = `<i class="fa-solid fa-arrow-trend-up"></i> ${formatCurrency(totalAnnualSavings)} vs standard TOU`;

    if (payback >= 99) {
        statPayback.innerText = "No Payback";
        statRoiPct.innerText = "0% ROI";
    } else {
        statPayback.innerText = `${payback.toFixed(1)} Years`;
        statRoiPct.innerText = `${roi.toFixed(1)}% ROI`;
    }

    // 30-Year Cumulative Cash Flow Loop (custom annual battery degradation, 2.5% rate inflation)
    const cashFlows = [ -cost ];
    let cumulative = -cost;
    let currentDegradation = 1.0;

    for (let yr = 1; yr <= 30; yr++) {
        const yearSavings = (annualBatterySavings * currentDegradation + annualEvSavings) * Math.pow(1.025, yr - 1);
        cumulative += yearSavings;
        cashFlows.push(cumulative);
        currentDegradation *= (1 - degradation); // Dynamic loss in max capacity each year
    }

    const net30Yr = cashFlows[30];
    stat10yrNet.innerText = formatCurrency(net30Yr);
    if (net30Yr >= 0) {
        stat10yrNet.className = "stat-value text-teal";
    } else {
        stat10yrNet.className = "stat-value text-rose";
    }

    // Update Detailed Payoff breakdown values
    detailChargeCost.innerText = `${formatCurrency(annualChargeCost)} / yr`;
    detailAvoidanceSavings.innerText = `${formatCurrency(annualAvoidanceSavings)} / yr`;
    detailEvYield.innerText = `${formatCurrency(annualEvSavings)} / yr`;

    // Cycles of life calculations
    const selectedBattery = MARKET_BATTERIES.find(b => b.id === selectedBatteryId);
    if (selectedBattery) {
        const cyclesPerYear = DAYS_WEEKDAY; // 1 cycle per weekday
        const yearsLife = selectedBattery.cycles / cyclesPerYear;
        detailCycleLimit.innerText = `${yearsLife.toFixed(1)} Years`;
        detailCycleDesc.innerText = `Lifecycle limit of ${selectedBattery.cycles.toLocaleString()} cycles. Depleted at 1 cycle/weekday.`;
    } else {
        detailCycleLimit.innerText = "Custom Package";
        detailCycleDesc.innerText = "Fine-tuning parameters manually sets a custom package.";
    }

    // Capacity Ratios Output Statement
    const ratioDaily = capacity / dailyLoad;
    const ratioPeak = capacity / peakUsage;
    const selectedName = selectedBattery ? `${selectedBattery.brand} ${selectedBattery.name}` : "Custom Configured";
    
    document.getElementById('ratio-statement-text').innerHTML = `
        You have selected a <strong>${capacity.toFixed(1)} kWh</strong> battery (${selectedName}) which is 
        <strong>${ratioDaily.toFixed(2)}x</strong> your average daily consumption and 
        <strong>${ratioPeak.toFixed(2)}x</strong> your peak period consumption ($4\text{ PM} - 9\text{ PM}$ weekdays).
    `;

    // Update Chart
    updateChart(cashFlows);
}

// Render market battery recommendations with physical fits
function renderMarketSuggestions(suggestedCap) {
    const userW = parseFloat(spaceWidth.value) || 0;
    const userD = parseFloat(spaceDepth.value) || 0;
    const userH = parseFloat(spaceHeight.value) || 0;

    marketGrid.innerHTML = '';

    MARKET_BATTERIES.forEach(battery => {
        const fitsSpace = battery.width <= userW && battery.depth <= userD && battery.height <= userH;
        const isIdeal = Math.abs(battery.capacity - suggestedCap) <= 3;
        
        const card = document.createElement('div');
        card.className = `market-card ${battery.id === selectedBatteryId ? 'selected' : ''} ${!fitsSpace ? 'disabled' : ''}`;
        
        card.innerHTML = `
            <div class="market-card-header">
                <span class="market-card-brand">${battery.brand}</span>
                <span class="market-card-title">
                    <a href="${battery.url}" target="_blank" class="market-link" onclick="event.stopPropagation();">
                        ${battery.name} <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:0.7rem; margin-left:0.2rem; opacity:0.7;"></i>
                    </a>
                </span>
            </div>
            <div class="market-card-dimensions">
                <i class="fa-solid fa-ruler-combined"></i>
                <span>${battery.width} x ${battery.depth} x ${battery.height} cm</span>
                <span class="dimension-badge ${fitsSpace ? 'fit' : 'no-fit'}">
                    ${fitsSpace ? '<i class="fa-solid fa-check"></i> Fits' : '<i class="fa-solid fa-xmark"></i> Too Large'}
                </span>
            </div>
            <div class="market-card-specs">
                <div class="market-card-spec-item">
                    <span>Capacity:</span>
                    <span>${battery.capacity} kWh ${isIdeal && fitsSpace ? '<strong class="text-teal">(Ideal Size)</strong>' : ''}</span>
                </div>
                <div class="market-card-spec-item">
                    <span>Efficiency:</span>
                    <span>${battery.efficiency}%</span>
                </div>
                <div class="market-card-spec-item">
                    <span>Rated Cycles:</span>
                    <span>${battery.cycles.toLocaleString()}</span>
                </div>
            </div>
            <div class="market-card-price">${formatCurrency(battery.cost)}</div>
            <button class="action-btn select-btn mt-md" style="padding:0.6rem; font-size:0.9rem; justify-content:center; width:100%;" ${!fitsSpace ? 'disabled' : ''}>
                Select & Analyze ROI
            </button>
        `;

        if (fitsSpace) {
            const triggerSelection = () => {
                selectedBatteryId = battery.id;
                
                // Sync values to manual input sliders
                capInput.value = battery.capacity;
                effInput.value = battery.efficiency;
                costInput.value = battery.cost;
                
                goToStep(3);
            };

            card.addEventListener('click', triggerSelection);
            card.querySelector('.select-btn').addEventListener('click', (e) => {
                e.stopPropagation();
                triggerSelection();
            });
        }

        marketGrid.appendChild(card);
    });
}

// Render/Update Chart.js instance
function updateChart(cashFlowData) {
    const ctx = document.getElementById('roi-chart').getContext('2d');
    const labels = Array.from({length: 31}, (_, i) => 'Yr ' + i);

    if (chartInstance) {
        chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Cumulative Net ROI (CAD)',
                data: cashFlowData,
                borderColor: '#06b6d4',
                backgroundColor: 'rgba(6, 182, 212, 0.1)',
                borderWidth: 3,
                fill: true,
                tension: 0.4,
                pointBackgroundColor: '#8b5cf6',
                pointBorderColor: '#fff',
                pointRadius: 3,
                pointHoverRadius: 5
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return 'Net Cash Flow: ' + formatCurrency(context.parsed.y);
                        }
                    }
                }
            },
            scales: {
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#94a3b8',
                        callback: function(value) {
                            return formatCurrency(value);
                        }
                    }
                },
                x: {
                    grid: {
                        display: false
                    },
                    ticks: {
                        color: '#94a3b8'
                    }
                }
            }
        }
    });
}

// OCR Bill Upload simulation
billUpload.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
        uploadZone.style.display = 'none';
        ocrLoader.style.display = 'flex';
        
        setTimeout(() => {
            ocrLoader.style.display = 'none';
            uploadZone.style.display = 'flex';
            uploadText.innerText = 'Upload Another Bill';
            
            // Generate mock OCR readings for past 3 months
            const m1 = Math.round(750 + Math.random() * 400);
            const m2 = Math.round(750 + Math.random() * 400);
            const m3 = Math.round(750 + Math.random() * 400);
            
            billM1.value = m1;
            billM2.value = m2;
            billM3.value = m3;
            
            updateAvgFromBills();
        }, 2000);
    }
});

// Reset Wizard helper
function resetWizard() {
    selectedBatteryId = null;
    document.getElementById('bill-input-type').value = 'total';
    document.getElementById('bill-inputs-title').innerText = 'Input Manual Past Months (kWh)';
    billM1.value = 930;
    billM2.value = 880;
    billM3.value = 890;
    spaceWidth.value = 100;
    spaceDepth.value = 30;
    spaceHeight.value = 120;
    evToggle.checked = true;
    degradationInput.value = 2.0;
    updateAvgFromBills();
    goToStep(1);
}

// Add Event Listeners
[capInput, effInput, degradationInput, costInput].forEach(elem => {
    elem.addEventListener('input', () => {
        // Deselect market battery card if modified manually to custom levels
        const selectedBattery = MARKET_BATTERIES.find(b => b.id === selectedBatteryId);
        if (selectedBattery) {
            if (parseFloat(capInput.value) !== selectedBattery.capacity || 
                parseFloat(effInput.value) !== selectedBattery.efficiency || 
                parseFloat(costInput.value) !== selectedBattery.cost) {
                selectedBatteryId = null;
            }
        }
        calculateROI();
    });
});

evToggle.addEventListener('change', () => {
    if (currentStep === 3) {
        calculateROI();
    }
});

document.getElementById('bill-input-type').addEventListener('change', (e) => {
    const titleEl = document.getElementById('bill-inputs-title');
    if (e.target.value === 'total') {
        titleEl.innerText = 'Input Manual Past Months (kWh)';
    } else {
        titleEl.innerText = 'Input Manual Peak Past Months (4 PM - 9 PM weekdays) (kWh)';
    }
    updateAvgFromBills();
});

[billM1, billM2, billM3].forEach(elem => {
    elem.addEventListener('input', updateAvgFromBills);
});

btnFindBatteries.addEventListener('click', () => {
    goToStep(2);
});

btnBackToStep1.addEventListener('click', () => {
    goToStep(1);
});

btnBackToStep2.addEventListener('click', () => {
    goToStep(2);
});

btnGoToStep4.addEventListener('click', () => {
    goToStep(4);
});

btnBackToStep3.addEventListener('click', () => {
    goToStep(3);
});

btnRecalculate.addEventListener('click', resetWizard);

// Tab click navigation triggers
document.querySelectorAll('.nav-tab').forEach(tab => {
    tab.addEventListener('click', () => {
        const targetStep = parseInt(tab.getAttribute('data-step'));
        
        // Prevent going to Step 3 or 4 if no battery has been selected yet
        if (targetStep > 2 && !selectedBatteryId) {
            alert("Please select a battery from the catalog in Step 2 first to view ROI analysis.");
            return;
        }
        
        goToStep(targetStep);
    });
});

// Initial Calculation on Page load
document.addEventListener('DOMContentLoaded', () => {
    updateAvgFromBills();
});
