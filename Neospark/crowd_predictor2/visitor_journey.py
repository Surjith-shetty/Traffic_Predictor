from datetime import datetime, timedelta
import json

class VisitorJourneyOptimizer:
    def __init__(self):
        self.journey_templates = {
            'first_time': {
                'recommended_duration': 180,  # 3 hours
                'must_do': ['complete_guide', 'darshan', 'prasad_collection'],
                'optional': ['special_pooja', 'temple_tour'],
                'tips': [
                    'Read the complete temple guide before visiting',
                    'Book your slot 2-3 days in advance',
                    'Arrive 30 minutes early for orientation',
                    'Download offline maps and temple layout'
                ]
            },
            'regular': {
                'recommended_duration': 90,  # 1.5 hours
                'must_do': ['darshan'],
                'optional': ['prasad_collection', 'special_pooja'],
                'tips': [
                    'Check crowd status before leaving',
                    'Use express darshan if available',
                    'Pre-book prasad to save time'
                ]
            },
            'quick': {
                'recommended_duration': 45,  # 45 minutes
                'must_do': ['darshan'],
                'optional': [],
                'tips': [
                    'Visit during off-peak hours (6-8 AM)',
                    'Use mobile check-in',
                    'Skip additional services for faster visit'
                ]
            }
        }
    
    def get_personalized_journey(self, user_profile, temple_data, visit_preferences):
        """Generate personalized journey recommendations"""
        
        # Determine visitor type
        visitor_type = self._determine_visitor_type(user_profile, visit_preferences)
        
        # Get base journey template
        base_journey = self.journey_templates.get(visitor_type, self.journey_templates['regular'])
        
        # Customize based on temple and preferences
        journey = self._customize_journey(base_journey, temple_data, visit_preferences)
        
        # Add time-based recommendations
        journey = self._add_time_recommendations(journey, temple_data)
        
        # Add crowd-based optimizations
        journey = self._add_crowd_optimizations(journey, temple_data)
        
        return journey
    
    def _determine_visitor_type(self, user_profile, preferences):
        """Determine if visitor is first-time, regular, or wants quick visit"""
        
        if preferences.get('visit_type') == 'quick':
            return 'quick'
        
        # Check if first-time visitor
        if user_profile.get('visit_count', 0) == 0 or preferences.get('first_time', False):
            return 'first_time'
        
        return 'regular'
    
    def _customize_journey(self, base_journey, temple_data, preferences):
        """Customize journey based on temple and user preferences"""
        
        journey = base_journey.copy()
        
        # Adjust duration based on temple size and services
        temple_capacity = temple_data.get('capacity', 100)
        if temple_capacity > 200:
            journey['recommended_duration'] += 30
        
        # Add temple-specific activities
        available_services = temple_data.get('services', [])
        if 'guided_tour' in available_services and preferences.get('interested_in_history', False):
            journey['optional'].append('guided_tour')
        
        if 'meditation_hall' in available_services and preferences.get('meditation', False):
            journey['optional'].append('meditation_session')
        
        # Adjust based on group size
        group_size = preferences.get('group_size', 1)
        if group_size > 4:
            journey['recommended_duration'] += 20
            journey['tips'].append('Large groups may need extra time for coordination')
        
        return journey
    
    def _add_time_recommendations(self, journey, temple_data):
        """Add time-based recommendations"""
        
        current_hour = datetime.now().hour
        
        # Morning recommendations
        if 6 <= current_hour <= 9:
            journey['time_benefits'] = [
                'Less crowded - peaceful atmosphere',
                'Cooler weather for comfortable visit',
                'Morning prayers and aarti available'
            ]
        # Afternoon recommendations
        elif 10 <= current_hour <= 14:
            journey['time_benefits'] = [
                'All services fully operational',
                'Good lighting for photography'
            ]
            journey['time_warnings'] = [
                'Peak crowd hours - expect longer waits',
                'Hot weather - carry water'
            ]
        # Evening recommendations
        elif 17 <= current_hour <= 20:
            journey['time_benefits'] = [
                'Evening aarti ceremony',
                'Beautiful lighting and ambiance'
            ]
        
        return journey
    
    def _add_crowd_optimizations(self, journey, temple_data):
        """Add crowd-based optimizations"""
        
        crowd_status = temple_data.get('crowd_status', 'Low')
        
        if crowd_status == 'High':
            journey['crowd_tips'] = [
                'Consider rescheduling to off-peak hours',
                'Use express services if available',
                'Be patient and maintain queue discipline',
                'Consider visiting nearby temples first'
            ]
            journey['recommended_duration'] += 45
        elif crowd_status == 'Medium':
            journey['crowd_tips'] = [
                'Moderate wait times expected',
                'Pre-book services to save time',
                'Stay hydrated while waiting'
            ]
            journey['recommended_duration'] += 20
        else:
            journey['crowd_tips'] = [
                'Perfect time to visit - minimal waiting',
                'Take your time to enjoy the peaceful atmosphere'
            ]
        
        return journey
    
    def generate_step_by_step_guide(self, journey, temple_data):
        """Generate detailed step-by-step visit guide"""
        
        steps = []
        current_time = 0
        
        # Pre-visit preparation
        steps.append({
            'step': 1,
            'title': 'Pre-Visit Preparation',
            'duration': 0,
            'actions': [
                'Check temple timings and crowd status',
                'Dress appropriately (modest clothing)',
                'Carry valid ID and booking confirmation',
                'Download temple map and guide'
            ]
        })
        
        # Arrival and entry
        steps.append({
            'step': 2,
            'title': 'Arrival & Entry',
            'duration': 15,
            'actions': [
                'Arrive at temple premises',
                'Park vehicle in designated area',
                'Remove footwear at entrance',
                'Security check and ID verification',
                'Collect entry token/wristband'
            ]
        })
        
        # Main darshan
        steps.append({
            'step': 3,
            'title': 'Main Darshan',
            'duration': 30,
            'actions': [
                'Join darshan queue',
                'Maintain queue discipline',
                'Offer prayers at main deity',
                'Receive temple blessings'
            ]
        })
        
        # Optional activities based on journey
        step_num = 4
        if 'prasad_collection' in journey.get('must_do', []) + journey.get('optional', []):
            steps.append({
                'step': step_num,
                'title': 'Prasad Collection',
                'duration': 10,
                'actions': [
                    'Visit prasad counter',
                    'Show QR code if pre-booked',
                    'Collect blessed offerings',
                    'Make additional donations if desired'
                ]
            })
            step_num += 1
        
        if 'special_pooja' in journey.get('optional', []):
            steps.append({
                'step': step_num,
                'title': 'Special Pooja (Optional)',
                'duration': 20,
                'actions': [
                    'Register for special pooja',
                    'Wait for your turn',
                    'Participate in ceremony',
                    'Receive special blessings'
                ]
            })
            step_num += 1
        
        # Exit
        steps.append({
            'step': step_num,
            'title': 'Temple Exit',
            'duration': 10,
            'actions': [
                'Visit temple shop if interested',
                'Collect footwear',
                'Exit through designated gate',
                'Share feedback if requested'
            ]
        })
        
        return steps
    
    def get_real_time_recommendations(self, temple_id, current_location='entrance'):
        """Get real-time recommendations based on current location in temple"""
        
        recommendations = {
            'entrance': [
                'Remove footwear and store safely',
                'Turn off mobile phone or keep on silent',
                'Proceed to security check counter'
            ],
            'security': [
                'Have ID ready for verification',
                'Open bags for inspection if required',
                'Collect entry token'
            ],
            'main_hall': [
                'Join the darshan queue on the right',
                'Maintain 6 feet distance',
                'No photography in sanctum area'
            ],
            'darshan_queue': [
                'Expected wait time: 15-20 minutes',
                'Use this time for meditation',
                'Keep offerings ready'
            ],
            'sanctum': [
                'Offer prayers silently',
                'Do not touch the deity',
                'Move quickly to allow others'
            ],
            'prasad_counter': [
                'Show QR code for pre-booked items',
                'Cash payments accepted',
                'Check items before leaving counter'
            ],
            'exit': [
                'Collect footwear',
                'Check for personal belongings',
                'Rate your experience if prompted'
            ]
        }
        
        return recommendations.get(current_location, [])

# Global instance
journey_optimizer = VisitorJourneyOptimizer()