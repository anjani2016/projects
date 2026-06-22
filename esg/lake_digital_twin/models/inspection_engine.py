import numpy as np
import requests
import json

def generate_ai_brief(api_key, risk_score, alerts, coordinates):
    """
    Generates a natural-language dispatch brief for field teams using the Gemini API.
    Falls back to a structured template if no API key is provided or the API request fails.
    """
    prompt = f"""
    You are AquaLens, an AI environmental expert. 
    A water quality anomaly has been detected and an inspection is triggered.
    
    Location Coordinates: {coordinates}
    Risk Score: {risk_score}/100
    Triggered Alert Flags: {', '.join(alerts)}
    
    Write a concise, professional dispatch brief (max 150 words) for a field sampling technician.
    Explain the primary concern, what they should prioritize sampling (e.g., surface chlorophyll, dissolved oxygen profiling, benthic grab samples), and any safety notes (e.g., potential toxic cyanobacteria bloom).
    """

    if not api_key:
        return get_template_fallback(risk_score, alerts, coordinates)

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response_json = response.json()
        
        if "candidates" in response_json and len(response_json["candidates"]) > 0:
            text = response_json["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip()
        else:
            return get_template_fallback(risk_score, alerts, coordinates) + "\n\n*(Note: Gemini API returned unexpected format. Showing template fallback).* "
    except Exception as e:
        return get_template_fallback(risk_score, alerts, coordinates) + f"\n\n*(Note: Gemini API error: {e}. Showing template fallback).* "

def get_template_fallback(risk_score, alerts, coordinates):
    """Fallback generator when Gemini is offline or unconfigured."""
    brief_parts = [
        f"**Field Dispatch Brief (System Auto-Generated)**",
        f"Target Coordinates: {coordinates[0]:.5f}, {coordinates[1]:.5f}",
        f"Trigger Flags: {', '.join(alerts)}"
    ]
    
    recommendations = []
    if "Precipitation Runoff Risk" in alerts:
        recommendations.append("- Conduct influent stream sampling for total phosphorus and suspended solids.")
    if "Thermal Stratification Risk" in alerts:
        recommendations.append("- Perform vertical profiles of dissolved oxygen and water temperature down to the lake bed.")
    if "Satellite Anomaly Spike" in alerts:
        recommendations.append("- Take immediate grab samples in the target bay to confirm Chlorophyll-a concentration.")
        recommendations.append("- Look for visual evidence of surface cyanobacteria scum. Wear gloves.")

    brief_parts.append("\n**Sampling Priorities:**\n" + "\n".join(recommendations))
    return "\n".join(brief_parts)

def evaluate_inspection_triggers(weather_rain, weather_forecast_temp, volunteer_gradient, volunteer_secchi, sat_anomaly_detected, lat=44.00, lon=-79.47):
    """
    Evaluates raw parameters against predefined rules to trigger human inspection alert.
    Returns:
        is_triggered (bool): True if inspection is required.
        risk_score (int): Composite Risk Index (0-100).
        active_alerts (list): Strings detailing which rules triggered.
    """
    risk_score = 0
    active_alerts = []
    
    # Rule 1: Heavy Precipitation Runoff
    if weather_rain > 45:
        risk_score += 40
        active_alerts.append("Precipitation Runoff Risk")
        
    # Rule 2: Hypoxia & Stratification Risk
    # Temperature gradient > 1.5°C + forecasted air temp > 28°C
    if volunteer_gradient > 1.5 and weather_forecast_temp > 28:
        risk_score += 30
        active_alerts.append("Thermal Stratification Risk")
    elif volunteer_secchi < 1.2:
        risk_score += 15
        active_alerts.append("Low Water Clarity Anomaly")
        
    # Rule 3: Satellite Spectral Anomaly
    if sat_anomaly_detected:
        risk_score += 35
        active_alerts.append("Satellite Anomaly Spike")
        
    # Cap score at 100
    risk_score = min(risk_score, 100)
    
    # Trigger threshold
    is_triggered = risk_score >= 60
    
    return is_triggered, risk_score, active_alerts
