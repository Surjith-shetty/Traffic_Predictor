import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque
import time
import json
from datetime import datetime

class QueueManager:
    def __init__(self):
        self.model = YOLO('yolov8n.pt')
        self.queues = {}  # temple_id -> queue data
        self.queue_zones = {}  # Define queue zones for each temple
        self.max_queue_length = 50  # Maximum people per queue
        self.processing_time_per_person = 2  # minutes
        
    def initialize_temple_queues(self, temple_id, zones):
        """Initialize queue zones for a temple"""
        self.queue_zones[temple_id] = zones
        self.queues[temple_id] = {
            'entry_queue': deque(maxlen=self.max_queue_length),
            'darshan_queue': deque(maxlen=self.max_queue_length),
            'exit_queue': deque(maxlen=self.max_queue_length),
            'prasad_queue': deque(maxlen=self.max_queue_length),
            'total_people': 0,
            'wait_times': {
                'entry': 0,
                'darshan': 0,
                'prasad': 0
            },
            'last_update': datetime.now()
        }
    
    def detect_people_in_zones(self, image_path, temple_id):
        """Detect people in different queue zones"""
        try:
            results = self.model(image_path, verbose=False)
            img = cv2.imread(image_path)
            
            if temple_id not in self.queue_zones:
                # Default zones if not configured
                h, w = img.shape[:2]
                self.initialize_temple_queues(temple_id, {
                    'entry': [(0, 0, w//3, h)],
                    'darshan': [(w//3, 0, 2*w//3, h)],
                    'prasad': [(2*w//3, 0, w, h//2)],
                    'exit': [(2*w//3, h//2, w, h)]
                })
            
            zone_counts = {
                'entry': 0,
                'darshan': 0,
                'prasad': 0,
                'exit': 0
            }
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    person_detections = boxes[boxes.cls == 0]
                    
                    for box in person_detections:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                        center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                        
                        # Check which zone this person is in
                        for zone_name, zones in self.queue_zones[temple_id].items():
                            for zone in zones:
                                zx1, zy1, zx2, zy2 = zone
                                if zx1 <= center_x <= zx2 and zy1 <= center_y <= zy2:
                                    zone_counts[zone_name] += 1
                                    break
                        
                        # Draw bounding box
                        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Draw zone boundaries
            colors = {'entry': (255, 0, 0), 'darshan': (0, 255, 255), 'prasad': (255, 255, 0), 'exit': (255, 0, 255)}
            for zone_name, zones in self.queue_zones[temple_id].items():
                color = colors.get(zone_name, (128, 128, 128))
                for zone in zones:
                    x1, y1, x2, y2 = zone
                    cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                    cv2.putText(img, zone_name.upper(), (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            # Save annotated image
            output_path = image_path.replace('.', '_queue_detected.')
            cv2.imwrite(output_path, img)
            
            return zone_counts, output_path
            
        except Exception as e:
            print(f"Queue detection error: {e}")
            return {'entry': 0, 'darshan': 0, 'prasad': 0, 'exit': 0}, None
    
    def update_queue_status(self, temple_id, zone_counts):
        """Update queue status and calculate wait times"""
        if temple_id not in self.queues:
            self.initialize_temple_queues(temple_id, {})
        
        queue_data = self.queues[temple_id]
        
        # Update queue lengths
        queue_data['entry_queue'] = deque([i for i in range(zone_counts['entry'])], maxlen=self.max_queue_length)
        queue_data['darshan_queue'] = deque([i for i in range(zone_counts['darshan'])], maxlen=self.max_queue_length)
        queue_data['prasad_queue'] = deque([i for i in range(zone_counts['prasad'])], maxlen=self.max_queue_length)
        queue_data['total_people'] = sum(zone_counts.values())
        
        # Calculate estimated wait times
        queue_data['wait_times'] = {
            'entry': len(queue_data['entry_queue']) * self.processing_time_per_person,
            'darshan': len(queue_data['darshan_queue']) * self.processing_time_per_person,
            'prasad': len(queue_data['prasad_queue']) * self.processing_time_per_person
        }
        
        queue_data['last_update'] = datetime.now()
        
        return self.get_queue_status(temple_id)
    
    def get_queue_status(self, temple_id):
        """Get current queue status"""
        if temple_id not in self.queues:
            return None
        
        queue_data = self.queues[temple_id]
        
        # Determine overall crowd level
        total_people = queue_data['total_people']
        if total_people <= 20:
            crowd_level = 'Low'
        elif total_people <= 50:
            crowd_level = 'Medium'
        else:
            crowd_level = 'High'
        
        return {
            'temple_id': temple_id,
            'total_people': total_people,
            'crowd_level': crowd_level,
            'queues': {
                'entry': {
                    'count': len(queue_data['entry_queue']),
                    'wait_time': queue_data['wait_times']['entry'],
                    'status': self.get_queue_level(len(queue_data['entry_queue']))
                },
                'darshan': {
                    'count': len(queue_data['darshan_queue']),
                    'wait_time': queue_data['wait_times']['darshan'],
                    'status': self.get_queue_level(len(queue_data['darshan_queue']))
                },
                'prasad': {
                    'count': len(queue_data['prasad_queue']),
                    'wait_time': queue_data['wait_times']['prasad'],
                    'status': self.get_queue_level(len(queue_data['prasad_queue']))
                }
            },
            'recommendations': self.get_recommendations(queue_data),
            'last_update': queue_data['last_update'].isoformat()
        }
    
    def get_queue_level(self, count):
        """Get queue level based on count"""
        if count <= 10:
            return 'Low'
        elif count <= 25:
            return 'Medium'
        else:
            return 'High'
    
    def get_recommendations(self, queue_data):
        """Generate recommendations based on queue status"""
        recommendations = []
        
        entry_count = len(queue_data['entry_queue'])
        darshan_count = len(queue_data['darshan_queue'])
        prasad_count = len(queue_data['prasad_queue'])
        
        if entry_count > 20:
            recommendations.append("Entry queue is crowded. Consider opening additional entry points.")
        
        if darshan_count > 30:
            recommendations.append("Darshan queue is very long. Implement time-slot management.")
        
        if prasad_count > 15:
            recommendations.append("Prasad counter is busy. Add more service counters.")
        
        if queue_data['total_people'] > 60:
            recommendations.append("Temple is overcrowded. Activate crowd control measures.")
        
        # Traffic flow recommendations
        if entry_count > darshan_count * 2:
            recommendations.append("Entry bottleneck detected. Speed up entry processing.")
        
        if darshan_count > prasad_count * 3:
            recommendations.append("Darshan queue backing up. Optimize darshan flow.")
        
        return recommendations
    
    def optimize_queue_flow(self, temple_id):
        """Suggest queue flow optimizations"""
        if temple_id not in self.queues:
            return []
        
        queue_data = self.queues[temple_id]
        optimizations = []
        
        # Analyze queue imbalances
        entry_wait = queue_data['wait_times']['entry']
        darshan_wait = queue_data['wait_times']['darshan']
        prasad_wait = queue_data['wait_times']['prasad']
        
        if darshan_wait > entry_wait * 2:
            optimizations.append({
                'type': 'bottleneck',
                'location': 'darshan',
                'suggestion': 'Increase darshan processing speed or add parallel darshan lines',
                'priority': 'high'
            })
        
        if prasad_wait > 20:
            optimizations.append({
                'type': 'service_delay',
                'location': 'prasad',
                'suggestion': 'Add more prasad service counters or pre-package items',
                'priority': 'medium'
            })
        
        if entry_wait > 15:
            optimizations.append({
                'type': 'entry_delay',
                'location': 'entry',
                'suggestion': 'Implement digital check-in or QR code scanning',
                'priority': 'high'
            })
        
        return optimizations

# Global queue manager instance
queue_manager = QueueManager()