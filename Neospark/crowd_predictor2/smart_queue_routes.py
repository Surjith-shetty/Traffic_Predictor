from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from smart_queue_ai import smart_queue_ai
from queue_manager import queue_manager
import os
from werkzeug.utils import secure_filename

smart_queue_bp = Blueprint('smart_queue', __name__)

@smart_queue_bp.route('/admin/smart-queue-dashboard')
def smart_queue_dashboard():
    """Smart Queue Management Dashboard"""
    # Mock temples data to avoid database issues
    temples = [
        {'id': 1, 'name': 'Somnath Temple'},
        {'id': 2, 'name': 'Dwarka Temple'},
        {'id': 3, 'name': 'Ambaji Temple'},
        {'id': 4, 'name': 'Pavagadh Temple'}
    ]
    
    return render_template('smart_queue_dashboard.html', temples=temples)

@smart_queue_bp.route('/api/smart-queue-analysis/<int:temple_id>')
def smart_queue_analysis(temple_id):
    """Perform AI analysis on temple queues"""
    try:
        # Get current queue status
        queue_status = queue_manager.get_queue_status(temple_id)
        
        if not queue_status:
            return jsonify({
                'success': False,
                'error': 'No queue data available for this temple'
            })
        
        # Perform AI priority analysis
        priority_analysis = smart_queue_ai.analyze_queue_priority(temple_id, queue_status)
        
        # Generate alerts
        alerts = smart_queue_ai.generate_alerts(temple_id, queue_status, priority_analysis)
        

        
        # Get optimization score
        optimization_score = smart_queue_ai.get_optimization_score(temple_id, queue_status)
        
        return jsonify({
            'success': True,
            'queue_status': queue_status,
            'priority_analysis': priority_analysis,
            'alerts': alerts,

            'optimization_score': optimization_score
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@smart_queue_bp.route('/api/emergency-release/<int:temple_id>', methods=['POST'])
def emergency_release(temple_id):
    """Execute emergency release for all queues"""
    try:
        # Log emergency release action (simplified)
        print(f'Emergency release executed for temple {temple_id}')
        
        # Reset queue manager for this temple (simulate release)
        if temple_id in queue_manager.queues:
            queue_data = queue_manager.queues[temple_id]
            # Reduce all queue counts by 50%
            for queue_name in ['entry_queue', 'darshan_queue', 'prasad_queue']:
                if queue_name in queue_data:
                    current_length = len(queue_data[queue_name])
                    new_length = max(0, current_length // 2)
                    queue_data[queue_name] = queue_data[queue_name][:new_length]
            
            # Update wait times
            queue_data['wait_times'] = {
                'entry': len(queue_data.get('entry_queue', [])) * queue_manager.processing_time_per_person,
                'darshan': len(queue_data.get('darshan_queue', [])) * queue_manager.processing_time_per_person,
                'prasad': len(queue_data.get('prasad_queue', [])) * queue_manager.processing_time_per_person
            }
        
        return jsonify({
            'success': True,
            'message': 'Emergency release executed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@smart_queue_bp.route('/api/optimize-queues/<int:temple_id>', methods=['POST'])
def optimize_queues(temple_id):
    """Apply AI optimization to queues"""
    try:
        # Get current queue status
        queue_status = queue_manager.get_queue_status(temple_id)
        
        if not queue_status:
            return jsonify({
                'success': False,
                'error': 'No queue data available'
            })
        
        # Get optimization recommendations
        optimizations = queue_manager.optimize_queue_flow(temple_id)
        
        # Apply optimizations (simulate)
        if temple_id in queue_manager.queues:
            queue_data = queue_manager.queues[temple_id]
            
            # Apply optimization logic
            for optimization in optimizations:
                if optimization['type'] == 'bottleneck' and optimization['location'] == 'darshan':
                    # Increase darshan processing rate
                    darshan_count = len(queue_data.get('darshan_queue', []))
                    reduction = min(darshan_count, 10)  # Reduce by up to 10 people
                    if darshan_count > 0:
                        queue_data['darshan_queue'] = queue_data['darshan_queue'][reduction:]
                
                elif optimization['type'] == 'service_delay' and optimization['location'] == 'prasad':
                    # Speed up prasad service
                    prasad_count = len(queue_data.get('prasad_queue', []))
                    reduction = min(prasad_count, 5)  # Reduce by up to 5 people
                    if prasad_count > 0:
                        queue_data['prasad_queue'] = queue_data['prasad_queue'][reduction:]
        
        # Log optimization action (simplified)
        print(f'Auto-optimization applied for temple {temple_id}: {len(optimizations)} optimizations')
        
        return jsonify({
            'success': True,
            'message': f'Applied {len(optimizations)} optimizations',
            'optimizations': optimizations
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@smart_queue_bp.route('/api/queue-alerts/<int:temple_id>')
def get_queue_alerts(temple_id):
    """Get active alerts for a temple"""
    try:
        alerts = smart_queue_ai.active_alerts.get(temple_id, [])
        
        return jsonify({
            'success': True,
            'alerts': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@smart_queue_bp.route('/api/queue-performance/<int:temple_id>')
def get_queue_performance(temple_id):
    """Get queue performance metrics"""
    try:
        # Simplified performance tracking
        actions = []
        
        # Get current queue status
        queue_status = queue_manager.get_queue_status(temple_id)
        
        # Calculate performance metrics
        if queue_status:
            total_people = queue_status['total_people']
            avg_wait_time = sum(q['wait_time'] for q in queue_status['queues'].values()) / len(queue_status['queues'])
            
            performance = {
                'total_people': total_people,
                'avg_wait_time': round(avg_wait_time, 1),
                'efficiency_score': max(0, 100 - (avg_wait_time * 2)),
                'recent_actions': [
                    {
                        'action': action[0],
                        'timestamp': action[1].isoformat() if action[1] else None,
                        'details': action[2]
                    } for action in actions
                ]
            }
        else:
            performance = {
                'total_people': 0,
                'avg_wait_time': 0,
                'efficiency_score': 100,
                'recent_actions': []
            }
        
        return jsonify({
            'success': True,
            'performance': performance
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Create queue_actions table if it doesn't exist
# Simplified initialization - no additional tables needed
print('Smart queue routes initialized')