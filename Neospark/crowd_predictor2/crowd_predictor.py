from datetime import datetime, timedelta
import calendar

class CrowdPredictor:
    def __init__(self):
        # Festival dates (approximate - these repeat yearly)
        self.festivals = {
            'shivaratri': [(2, 18), (3, 8)],  # Feb-Mar
            'navratri': [(3, 22), (4, 1), (9, 15), (10, 24)],  # Mar-Apr, Sep-Oct
            'diwali': [(10, 24), (11, 12)],  # Oct-Nov
            'dussehra': [(10, 15), (10, 24)],  # October
            'karnataka_rajyotsava': [(11, 1)],  # Nov 1
            'ugadi': [(3, 22), (4, 13)],  # Mar-Apr
            'ganesha_chaturthi': [(8, 22), (9, 15)],  # Aug-Sep
            'krishna_janmashtami': [(8, 15), (9, 5)],  # Aug-Sep
        }
        
        # Temple-specific high crowd events
        self.temple_events = {
            'Virupaksha Temple': {
                'hampi_utsav': [(1, 15), (2, 15)],  # Jan-Feb
                'vijayanagara_festival': [(11, 1), (11, 7)],
            },
            'Murudeshwara Temple': {
                'shivaratri_special': [(2, 18), (3, 8)],
                'kartik_purnima': [(11, 15), (12, 15)],
            },
            'Sri Krishna Temple, Udupi': {
                'krishna_janmashtami': [(8, 15), (9, 5)],
                'paryaya_festival': [(1, 15), (1, 20)],  # Every 2 years
            },
            'Chennakeshava Temple, Belur': {
                'hoysala_mahotsav': [(3, 1), (3, 7)],
                'vaikuntha_ekadashi': [(12, 15), (1, 15)],
            }
        }
        
        # Historical crowd patterns (synthetic data based on typical temple patterns)
        self.historical_patterns = {
            'weekends': 'high',  # Saturdays, Sundays
            'monday': 'medium',  # Many visit on Mondays for Shiva temples
            'tuesday_thursday': 'low',
            'wednesday_friday': 'medium',
            'full_moon': 'high',  # Purnima days
            'new_moon': 'medium',  # Amavasya days
            'eclipse_days': 'high',
            'school_holidays': 'high',  # Summer: Apr-Jun, Winter: Dec-Jan
        }

    def get_crowd_prediction(self, date_str, temple_name):
        """Get crowd prediction for a specific date and temple"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            month = date_obj.month
            day = date_obj.day
            weekday = date_obj.weekday()  # 0=Monday, 6=Sunday
            
            crowd_level = 'low'  # Default
            
            # Check festivals
            for festival, dates in self.festivals.items():
                for fest_month, fest_day in dates:
                    if abs(month - fest_month) <= 0 and abs(day - fest_day) <= 3:
                        crowd_level = 'high'
                        break
            
            # Check temple-specific events
            if temple_name in self.temple_events:
                for event, dates in self.temple_events[temple_name].items():
                    for event_month, event_day in dates:
                        if abs(month - event_month) <= 0 and abs(day - event_day) <= 2:
                            crowd_level = 'high'
                            break
            
            # Weekend patterns
            if weekday in [5, 6]:  # Saturday, Sunday
                if crowd_level == 'low':
                    crowd_level = 'medium'
                elif crowd_level == 'medium':
                    crowd_level = 'high'
            
            # Monday for Shiva temples
            if weekday == 0 and 'Shiva' in temple_name:
                if crowd_level == 'low':
                    crowd_level = 'medium'
            
            # School holidays (summer and winter)
            if month in [4, 5, 6, 12, 1]:  # Summer and winter holidays
                if crowd_level == 'low':
                    crowd_level = 'medium'
            
            # Full moon days (approximate)
            if 13 <= day <= 16:  # Around full moon
                if crowd_level == 'low':
                    crowd_level = 'medium'
            
            return crowd_level
            
        except Exception as e:
            return 'low'  # Default fallback

    def get_calendar_data(self, year, month, temple_name):
        """Get crowd predictions for entire month"""
        calendar_data = {}
        
        # Get number of days in month
        days_in_month = calendar.monthrange(year, month)[1]
        
        for day in range(1, days_in_month + 1):
            date_str = f"{year}-{month:02d}-{day:02d}"
            crowd_level = self.get_crowd_prediction(date_str, temple_name)
            calendar_data[day] = crowd_level
        
        return calendar_data

    def get_color_for_crowd(self, crowd_level):
        """Get color code for crowd level"""
        colors = {
            'low': '#28a745',    # Green
            'medium': '#ffc107', # Yellow
            'high': '#dc3545'    # Red
        }
        return colors.get(crowd_level, '#6c757d')  # Default gray