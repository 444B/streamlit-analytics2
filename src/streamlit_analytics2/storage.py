# storage.py - Storage operations for streamlit-analytics2
"""
Storage operations for JSON and CSV formats
"""

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, Union
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


def save_to_json(data: Dict[str, Any], filepath: Union[str, Path], verbose: bool = False) -> None:
    """Save data to JSON file."""
    try:
        filepath = Path(filepath)
        # Ensure we're saving in sa2_data directory
        if not str(filepath).startswith('sa2_data'):
            filepath = Path('sa2_data') / filepath.name
        
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
            
        if verbose:
            logger.info(f"Saved data to JSON: {filepath}")
            
    except Exception as e:
        logger.error(f"Failed to save JSON: {str(e)}")
        raise


def save_to_csv(data: Dict[str, Any], filepath: Union[str, Path], verbose: bool = False) -> None:
    """
    Export analytics data to CSV format.
    Creates three CSV files:
    - Main metrics (filepath)
    - Daily metrics (filepath_daily.csv)
    - Widget interactions (filepath_widgets.csv)
    """
    try:
        filepath = Path(filepath)
        # Ensure we're saving in sa2_data directory
        if not str(filepath).startswith('sa2_data'):
            filepath = Path('sa2_data') / filepath.name
            
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Main metrics CSV
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value', 'Timestamp'])
            writer.writerow(['Total Pageviews', data.get('total_pageviews', 0), datetime.now().isoformat()])
            writer.writerow(['Total Script Runs', data.get('total_script_runs', 0), datetime.now().isoformat()])
            writer.writerow(['Total Time (seconds)', data.get('total_time_seconds', 0), datetime.now().isoformat()])
            writer.writerow(['Start Time', data.get('start_time', 'N/A'), datetime.now().isoformat()])
        
        # Daily metrics CSV
        if 'per_day' in data and data['per_day'].get('days'):
            daily_file = filepath.parent / f"{filepath.stem}_daily.csv"
            df_daily = pd.DataFrame(data['per_day'])
            df_daily.to_csv(daily_file, index=False)
            
            if verbose:
                logger.info(f"Saved daily metrics to {daily_file}")
        
        # Widget interactions CSV
        widgets_file = filepath.parent / f"{filepath.stem}_widgets.csv"
        widgets_data = []
        
        for widget_name, interactions in data.get('widgets', {}).items():
            if isinstance(interactions, dict):
                for value, count in interactions.items():
                    widgets_data.append({
                        'widget': widget_name,
                        'value': str(value),
                        'count': count,
                        'timestamp': datetime.now().isoformat()
                    })
            else:
                widgets_data.append({
                    'widget': widget_name,
                    'value': 'Total Interactions',
                    'count': interactions,
                    'timestamp': datetime.now().isoformat()
                })
        
        if widgets_data:
            pd.DataFrame(widgets_data).to_csv(widgets_file, index=False)
            
            if verbose:
                logger.info(f"Saved widget data to {widgets_file}")
        
        if verbose:
            logger.info(f"Successfully saved analytics to CSV: {filepath}")
            
    except Exception as e:
        logger.error(f"Failed to save CSV: {str(e)}")
        raise


def load_from_csv(filepath: Union[str, Path], verbose: bool = False) -> Dict[str, Any]:
    """
    Load analytics data from CSV files.
    """
    try:
        filepath = Path(filepath)
        data = {
            "total_pageviews": 0,
            "total_script_runs": 0,
            "total_time_seconds": 0,
            "start_time": str(datetime.now()),
            "per_day": {"days": [], "pageviews": [], "script_runs": []},
            "widgets": {}
        }
        
        # Load main metrics
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    metric = row.get('Metric', '')
                    value = row.get('Value', '0')
                    
                    if metric == 'Total Pageviews':
                        data['total_pageviews'] = int(value)
                    elif metric == 'Total Script Runs':
                        data['total_script_runs'] = int(value)
                    elif metric == 'Total Time (seconds)':
                        data['total_time_seconds'] = float(value)
                    elif metric == 'Start Time':
                        data['start_time'] = value
        
        # Load daily metrics
        daily_file = filepath.parent / f"{filepath.stem}_daily.csv"
        if daily_file.exists():
            df_daily = pd.read_csv(daily_file)
            data['per_day'] = df_daily.to_dict('list')
        
        # Load widget data
        widgets_file = filepath.parent / f"{filepath.stem}_widgets.csv"
        if widgets_file.exists():
            df_widgets = pd.read_csv(widgets_file)
            
            for _, row in df_widgets.iterrows():
                widget = row['widget']
                value = row['value']
                count = row['count']
                
                if widget not in data['widgets']:
                    data['widgets'][widget] = {}
                
                if value == 'Total Interactions':
                    data['widgets'][widget] = count
                else:
                    if not isinstance(data['widgets'][widget], dict):
                        data['widgets'][widget] = {}
                    data['widgets'][widget][value] = count
        
        if verbose:
            logger.info(f"Successfully loaded analytics from CSV: {filepath}")
            
        return data
        
    except Exception as e:
        logger.error(f"Failed to load CSV: {str(e)}")
        raise