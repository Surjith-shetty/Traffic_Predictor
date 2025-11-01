from ultralytics import YOLO
import cv2
import os

def detect_crowd(source):
    """
    Detect crowd using YOLOv8 model with green bounding boxes
    Args:
        source: Image path, video path, or 0 for webcam
    Returns:
        int: Number of people detected
    """
    try:
        # Check if source file exists
        if isinstance(source, str) and not os.path.exists(source):
            print(f"Error: File {source} does not exist")
            return 0
        
        # Load YOLOv8 model
        model = YOLO('yolov8n.pt')
        
        # Run inference
        results = model(source, verbose=False)
        
        person_count = 0
        
        # Process each frame
        for i, result in enumerate(results):
            # Load original image
            img = cv2.imread(source) if isinstance(source, str) else result.orig_img
            
            boxes = result.boxes
            if boxes is not None:
                # Filter for 'person' class (class 0 in COCO dataset)
                person_detections = boxes[boxes.cls == 0]
                person_count += len(person_detections)
                
                # Draw green bounding boxes around detected people
                for box in person_detections:
                    # Get box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = box.conf[0].cpu().numpy()
                    
                    # Draw green rectangle
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # Add confidence label
                    label = f'Person {confidence:.2f}'
                    cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Save annotated image
            output_path = source.replace('.', '_detected.')
            cv2.imwrite(output_path, img)
            print(f"Annotated image saved: {output_path}")
        
        return person_count
    
    except Exception as e:
        print(f"Error in crowd detection: {e}")
        return 0

def detect_crowd_with_boxes(source):
    """
    Detect crowd and return both count and annotated image path
    Args:
        source: Image path
    Returns:
        tuple: (person_count, annotated_image_path)
    """
    try:
        if isinstance(source, str) and not os.path.exists(source):
            return 0, None
        
        model = YOLO('yolov8n.pt')
        results = model(source, verbose=False)
        
        person_count = 0
        annotated_path = None
        
        for result in results:
            img = cv2.imread(source)
            boxes = result.boxes
            
            if boxes is not None:
                person_detections = boxes[boxes.cls == 0]
                person_count += len(person_detections)
                
                # Draw green boxes
                for box in person_detections:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    confidence = box.conf[0].cpu().numpy()
                    
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 3)
                    label = f'Person {confidence:.2f}'
                    cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Add count text
            cv2.putText(img, f'Total People: {person_count}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 3)
            
            # Save annotated image
            annotated_path = source.replace('.', '_detected.')
            cv2.imwrite(annotated_path, img)
        
        return person_count, annotated_path
    except Exception as e:
        print(f"Error: {e}")
        return 0, None

def get_crowd_status(count):
    """
    Convert person count to crowd status
    Args:
        count: Number of people detected
    Returns:
        str: Crowd status (Low/Medium/High)
    """
    if count <= 10:
        return 'Low'
    elif count <= 30:
        return 'Medium'
    else:
        return 'High'

def detect_queue_zones(source, zones=None):
    """
    Detect people in specific queue zones
    Args:
        source: Image path
        zones: Dictionary of zone definitions {zone_name: [(x1,y1,x2,y2), ...]}
    Returns:
        dict: Zone-wise people counts
    """
    try:
        if isinstance(source, str) and not os.path.exists(source):
            return {}
        
        model = YOLO('yolov8n.pt')
        results = model(source, verbose=False)
        
        img = cv2.imread(source)
        h, w = img.shape[:2]
        
        # Default zones if not provided
        if not zones:
            zones = {
                'entry': [(0, 0, w//3, h)],
                'darshan': [(w//3, 0, 2*w//3, h)],
                'prasad': [(2*w//3, 0, w, h//2)],
                'exit': [(2*w//3, h//2, w, h)]
            }
        
        zone_counts = {zone_name: 0 for zone_name in zones.keys()}
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                person_detections = boxes[boxes.cls == 0]
                
                for box in person_detections:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy().astype(int)
                    center_x, center_y = (x1 + x2) // 2, (y1 + y2) // 2
                    
                    # Check which zone this person is in
                    for zone_name, zone_list in zones.items():
                        for zone in zone_list:
                            zx1, zy1, zx2, zy2 = zone
                            if zx1 <= center_x <= zx2 and zy1 <= center_y <= zy2:
                                zone_counts[zone_name] += 1
                                break
                    
                    # Draw detection box
                    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw zone boundaries
        colors = {'entry': (255, 0, 0), 'darshan': (0, 255, 255), 'prasad': (255, 255, 0), 'exit': (255, 0, 255)}
        for zone_name, zone_list in zones.items():
            color = colors.get(zone_name, (128, 128, 128))
            for zone in zone_list:
                x1, y1, x2, y2 = zone
                cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
                cv2.putText(img, zone_name.upper(), (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        # Add zone counts as text
        y_offset = 30
        for zone_name, count in zone_counts.items():
            color = colors.get(zone_name, (255, 255, 255))
            cv2.putText(img, f'{zone_name.upper()}: {count}', (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
            y_offset += 30
        
        # Save annotated image
        output_path = source.replace('.', '_queue_zones.')
        cv2.imwrite(output_path, img)
        
        return zone_counts, output_path
        
    except Exception as e:
        print(f"Queue zone detection error: {e}")
        return {}, None