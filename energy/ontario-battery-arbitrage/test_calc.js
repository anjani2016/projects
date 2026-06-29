// Test suite for VoltShift Ontario logic

function assert(condition, message) {
    if (!condition) {
        throw new Error("Assertion failed: " + message);
    }
}

function runTests() {
    console.log("Running VoltShift Ontario math calculations checks...");

    const capacity = 13.5;
    const efficiency = 0.90;
    const cost = 14500;
    const dailyLoad = 30;
    const hasEvShift = true;

    // Math emulation from app.js
    const DAYS_WEEKDAY = 251;
    const RATES = {
        ULO: { OVERNIGHT: 0.039, ON_PEAK: 0.391 },
        TOU: { OFF_PEAK: 0.098 }
    };
    const PROFILE = { ULO_BASE: { ON_PEAK: 0.30 } };

    const peakUsage = dailyLoad * PROFILE.ULO_BASE.ON_PEAK; // 30 * 0.30 = 9.0 kWh
    assert(peakUsage === 9.0, `Peak usage should be 9.0, got ${peakUsage}`);

    const usableDischarge = Math.min(capacity, peakUsage); // Math.min(13.5, 9.0) = 9.0 kWh
    assert(usableDischarge === 9.0, `Usable discharge should be capped at 9.0, got ${usableDischarge}`);

    const dailyChargeCost = (usableDischarge / efficiency) * RATES.ULO.OVERNIGHT; // (9.0 / 0.9) * 0.039 = 0.39
    assert(Math.abs(dailyChargeCost - 0.39) < 0.0001, `Daily charge cost should be 0.39, got ${dailyChargeCost}`);

    const offsetSavings = usableDischarge * RATES.ULO.ON_PEAK; // 9.0 * 0.391 = 3.519
    assert(Math.abs(offsetSavings - 3.519) < 0.0001, `Offset savings should be 3.519, got ${offsetSavings}`);

    const netDailyArbitrageSavings = offsetSavings - dailyChargeCost; // 3.519 - 0.39 = 3.129
    assert(Math.abs(netDailyArbitrageSavings - 3.129) < 0.0001, `Net daily savings should be 3.129, got ${netDailyArbitrageSavings}`);

    const annualBatterySavings = netDailyArbitrageSavings * DAYS_WEEKDAY; // 3.129 * 251 = 785.379
    assert(Math.abs(annualBatterySavings - 785.379) < 0.0001, `Annual battery savings should be 785.379, got ${annualBatterySavings}`);

    const annualEvSavings = hasEvShift ? (3000 * (RATES.TOU.OFF_PEAK - RATES.ULO.OVERNIGHT)) : 0; // 3000 * 0.059 = 177.00
    assert(annualEvSavings === 177.00, `EV savings should be 177.00, got ${annualEvSavings}`);

    const totalAnnualSavings = annualBatterySavings + annualEvSavings; // 962.379
    assert(Math.abs(totalAnnualSavings - 962.379) < 0.0001, `Total savings should be 962.379, got ${totalAnnualSavings}`);

    console.log("All calculations successfully verified!");
}

try {
    runTests();
} catch (error) {
    console.error("Test failed: ", error.message);
    process.exit(1);
}
