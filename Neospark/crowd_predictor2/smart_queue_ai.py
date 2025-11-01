import numpy as np
from datetime import datetime, timedelta
import json
from collections import deque
import threading
import time

class SmartQueueAI:
    """AI-powered queue management system similar to VAC traffic signals"""
    
    def __init__(self):
        self.queue_states = {}
        self.priority_matrix = {}
        self.alert_thresholds = {
            'critical': 40,  # people
            'high': 25,
            'medium': 15
        }
        self.processing_rates = {
            'entry': 0.5,    # people per minute
            'darshan': 0.3,  # people per minute  
            'prasad': 0.8,   # people per minute
            'exit': 1.0      # people per minute
        }
        self.active_alerts = {}
        
    def analyze_queue_priority(self, temple_id, queue_data):
        """Analyze which queue needs immediate attention (VAC-like logic)"""
        
        if temple_id not in self.queue_states:
            self.queue_states[temple_id] = {
                'last_analysis': datetime.now(),
                'queue_history': deque(maxlen=10),
                'bottleneck_count': 0
            }
        
        # Calculate queue pressure scores
        pressure_scores = {}
        for queue_name, queue_info in queue_data['queues'].items():
            count = queue_info['count']
            wait_time = queue_info['wait_time']
            
            # VAC-like pressure calculation
            pressure = (count * 2) + (wait_time * 1.5)
            
            # Add historical trend factor
            if len(self.queue_states[temple_id]['queue_history']) > 0:
                last_count = self.queue_states[temple_id]['queue_history'][-1].get(queue_name, 0)
                growth_rate = (count - last_count) / max(last_count, 1)
                pressure += growth_rate * 10
            
            pressure_scores[queue_name] = pressure
        
        # Store current state for trend analysis
        current_state = {q: queue_data['queues'][q]['count'] for q in queue_data['queues']}
        self.queue_states[temple_id]['queue_history'].append(current_state)
        
        # Determine priority queue (highest pressure)
        priority_queue = max(pressure_scores.items(), key=lambda x: x[1])
        
        return {
            'priority_queue': priority_queue[0],
            'priority_score': priority_queue[1],
            'pressure_scores': pressure_scores,
            'release_recommendation': self._get_release_strategy(pressure_scores, queue_data)
        }
    
    def _get_release_strategy(self, pressure_scores, queue_data):
        """Generate VAC-like release strategy with queue splitting and hazard prevention"""
        
        strategies = []
        
        # Sort queues by pressure (highest first)
        sorted_queues = sorted(pressure_scores.items(), key=lambda x: x[1], reverse=True)
        
        for queue_name, pressure in sorted_queues:
            queue_info = queue_data['queues'][queue_name]
            count = queue_info['count']
            
            if pressure > 50:  # Critical pressure - STAMPEDE RISK
                strategies.append({
                    'queue': queue_name,
                    'action': 'EMERGENCY_SPLIT_QUEUE',
                    'priority': 'CRITICAL',
                    'method': 'SPLIT INTO 3 PARALLEL LANES + Emergency Exit',
                    'duration': 'IMMEDIATE - 5 minutes',
                    'expected_reduction': min(count, 30),
                    'hazard_prevention': [
                        '🚨 STAMPEDE RISK - Split queue into 3 parallel lanes',
                        '🚪 Open emergency exit routes',
                        '👮 Deploy crowd control staff immediately',
                        '📢 Announce queue splitting to pilgrims',
                        '⚠️ Stop new entries until queue reduces'
                    ],
                    'vac_action': 'RED SIGNAL - Stop all new entries, Release existing queue'
                })
            elif pressure > 30:  # High pressure - BOTTLENECK RISK
                strategies.append({
                    'queue': queue_name,
                    'action': 'SPLIT_QUEUE_DUAL_LANE',
                    'priority': 'HIGH', 
                    'method': 'Split into 2 lanes + Fast track for elderly',
                    'duration': '10-15 minutes',
                    'expected_reduction': min(count, 20),
                    'hazard_prevention': [
                        '⚡ BOTTLENECK DETECTED - Create dual processing lanes',
                        '👴 Priority lane for elderly/disabled',
                        '📏 Maintain 2-meter spacing between people',
                        '🔄 Redirect overflow to alternate routes',
                        '📱 Send SMS alerts to reduce new arrivals'
                    ],
                    'vac_action': 'YELLOW SIGNAL - Controlled entry, Dual lane processing'
                })
            elif pressure > 15:  # Medium pressure - PREVENTIVE ACTION
                strategies.append({
                    'queue': queue_name,
                    'action': 'OPTIMIZE_FLOW',
                    'priority': 'MEDIUM',
                    'method': 'Optimize processing + Add staff',
                    'duration': '15-20 minutes', 
                    'expected_reduction': min(count, 15),
                    'hazard_prevention': [
                        '📈 INCREASING CROWD - Add extra processing staff',
                        '⏱️ Reduce processing time per person',
                        '📋 Pre-fill forms to speed up service',
                        '🎯 Focus on efficient crowd movement',
                        '📊 Monitor queue growth rate'
                    ],
                    'vac_action': 'GREEN SIGNAL - Normal flow with optimization'
                })
            else:  # Low pressure - MAINTAIN FLOW
                strategies.append({
                    'queue': queue_name,
                    'action': 'MAINTAIN_NORMAL_FLOW',
                    'priority': 'LOW',
                    'method': 'Continue normal operations',
                    'duration': 'Ongoing monitoring', 
                    'expected_reduction': min(count, 5),
                    'hazard_prevention': [
                        '✅ NORMAL OPERATIONS - Continue current flow',
                        '👀 Monitor for any sudden increases',
                        '📱 Keep communication channels open',
                        '🔄 Ready to implement crowd control if needed'
                    ],
                    'vac_action': 'GREEN SIGNAL - Normal operations'
                })
        
        return strategies
    
    def generate_alerts(self, temple_id, queue_data, priority_analysis):
        """Generate smart alerts for admin"""
        
        alerts = []
        current_time = datetime.now()
        
        # Critical queue alerts
        for queue_name, queue_info in queue_data['queues'].items():
            count = queue_info['count']
            wait_time = queue_info['wait_time']
            
            if count >= self.alert_thresholds['critical']:
                alerts.append({
                    'type': 'CRITICAL',
                    'queue': queue_name,
                    'message': f'{queue_name.upper()} QUEUE CRITICAL: {count} people, {wait_time}min wait',
                    'action': 'IMMEDIATE ACTION REQUIRED',
                    'timestamp': current_time.isoformat(),
                    'sound': True,
                    'color': 'danger'
                })
            elif count >= self.alert_thresholds['high']:
                alerts.append({
                    'type': 'HIGH',
                    'queue': queue_name,
                    'message': f'{queue_name.upper()} queue high: {count} people, {wait_time}min wait',
                    'action': 'Priority attention needed',
                    'timestamp': current_time.isoformat(),
                    'sound': False,
                    'color': 'warning'
                })
        
        # Bottleneck detection alerts
        if priority_analysis['priority_score'] > 40:
            alerts.append({
                'type': 'BOTTLENECK',
                'queue': priority_analysis['priority_queue'],
                'message': f'BOTTLENECK DETECTED in {priority_analysis["priority_queue"]} queue',
                'action': f'Release {priority_analysis["priority_queue"]} queue immediately',
                'timestamp': current_time.isoformat(),
                'sound': True,
                'color': 'danger'
            })
        
        # Flow imbalance alerts
        pressure_scores = priority_analysis['pressure_scores']
        max_pressure = max(pressure_scores.values())
        min_pressure = min(pressure_scores.values())
        
        if max_pressure - min_pressure > 25:
            max_queue = max(pressure_scores.items(), key=lambda x: x[1])[0]
            alerts.append({
                'type': 'IMBALANCE',
                'queue': max_queue,
                'message': f'Queue flow imbalance detected - {max_queue} overloaded',
                'action': f'Redirect flow from {max_queue} to other areas',
                'timestamp': current_time.isoformat(),
                'sound': False,
                'color': 'info'
            })
        
        # Store alerts for tracking
        self.active_alerts[temple_id] = alerts
        
        return alerts
    

    

    
    def get_optimization_score(self, temple_id, queue_data):
        """Calculate overall queue optimization score"""
        
        total_people = queue_data['total_people']
        total_wait_time = sum(q['wait_time'] for q in queue_data['queues'].values())
        
        # Efficiency metrics
        if total_people == 0:
            return 100
        
        avg_wait_time = total_wait_time / len(queue_data['queues'])
        
        # Score calculation (0-100)
        wait_score = max(0, 100 - (avg_wait_time * 2))
        capacity_score = max(0, 100 - (total_people * 1.5))
        
        # Balance score (how evenly distributed are the queues)
        queue_counts = [q['count'] for q in queue_data['queues'].values()]
        if len(queue_counts) > 1:
            balance_score = 100 - (np.std(queue_counts) * 3)
        else:
            balance_score = 100
        
        overall_score = (wait_score + capacity_score + balance_score) / 3
        
        return {
            'overall_score': round(overall_score, 1),
            'wait_score': round(wait_score, 1),
            'capacity_score': round(capacity_score, 1),
            'balance_score': round(balance_score, 1),
            'grade': 'A' if overall_score >= 80 else 'B' if overall_score >= 60 else 'C' if overall_score >= 40 else 'D'
        }

# Global AI instance
smart_queue_ai = SmartQueueAI()