import requests
import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime

class IESOHarvester:
    BASE_URL = "http://reports.ieso.ca/public/"
    
    # Mapping IESO Fuel types to Project Categories
    CATEGORY_MAP = {
        "Nuclear": "Nuclear",
        "Hydro": "Hydro",
        "Gas": "Fossil",
        "Wind": "Renewable",
        "Solar": "Renewable",
        "Biofuel": "Renewable",
        "Other": "Fossil",
        "Storage": "Storage"
    }
    
    @staticmethod
    def fetch_xml(report_name):
        url = f"{IESOHarvester.BASE_URL}{report_name}/PUB_{report_name}.xml"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                return response.content
        except Exception as e:
            print(f"Error fetching {report_name}: {e}")
        return None

    @staticmethod
    def get_latest_gen_by_fuel():
        """
        Fetches hourly generation output by fuel type and returns the most recent hour's data.
        """
        xml_data = IESOHarvester.fetch_xml("GenOutputbyFuelHourly")
        if not xml_data:
            return None
        
        try:
            root = ET.fromstring(xml_data)
            # Namespace handling
            ns = {'ns': 'http://www.ieso.ca/schema'}
            
            # Find the last DailyData and last HourlyData
            daily_data = root.findall('.//ns:DailyData', ns)
            if not daily_data: return None
            
            latest_day = daily_data[-1]
            hourly_data = latest_day.findall('ns:HourlyData', ns)
            if not hourly_data: return None
            
            latest_hour = hourly_data[-1]
            hour_num = latest_hour.find('ns:Hour', ns).text
            
            results = {}
            for fuel_total in latest_hour.findall('ns:FuelTotal', ns):
                fuel = fuel_total.find('ns:Fuel', ns).text
                output = fuel_total.find('.//ns:Output', ns).text
                results[fuel.capitalize()] = float(output)
            
            return {
                "hour": hour_num,
                "data": results,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"Error parsing GenOutput: {e}")
            return None

    @staticmethod
    def get_mapped_gen_data():
        """
        Aggregates live fuel data into the 5 standard project categories.
        """
        raw = IESOHarvester.get_latest_gen_by_fuel()
        if not raw: return None
        
        mapped = {cat: 0.0 for cat in ["Nuclear", "Hydro", "Fossil", "Renewable", "Storage"]}
        for fuel, val in raw['data'].items():
            cat = IESOHarvester.CATEGORY_MAP.get(fuel, "Fossil")
            if cat in mapped:
                mapped[cat] += val
        
        return {
            "hour": raw['hour'],
            "mapped_data": mapped,
            "timestamp": raw['timestamp']
        }

    @staticmethod
    def get_latest_demand():
        """
        Fetches the latest total demand for Ontario.
        """
        xml_data = IESOHarvester.fetch_xml("Demand")
        if not xml_data:
            return None
        
        try:
            root = ET.fromstring(xml_data)
            ns = {'ns': 'http://www.ieso.ca/schema'}
            
            # In PUB_Demand.xml, the structure is similar
            daily_data = root.findall('.//ns:DailyData', ns)
            if not daily_data: return None
            
            latest_day = daily_data[-1]
            hourly_data = latest_day.findall('ns:HourlyData', ns)
            if not hourly_data: return None
            
            latest_hour = hourly_data[-1]
            # Demand report has MarketDemand and OntarioDemand
            ontario_demand = latest_hour.find('.//ns:OntarioDemand', ns).text
            
            return {
                "demand_mw": float(ontario_demand),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"Error parsing Demand: {e}")
            return None
