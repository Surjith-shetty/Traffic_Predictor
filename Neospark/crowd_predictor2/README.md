# Temple Pilgrimage Crowd Management System

Advanced Flask web application for managing temple visits with AI-powered crowd control and queue management.

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. MySQL Database Setup
```sql
CREATE DATABASE temple_db;
```

### 3. Configure Database
Update `config.py` with your MySQL credentials:
- MYSQL_HOST (default: localhost)
- MYSQL_USER (default: root)
- MYSQL_PASSWORD (default: password)
- MYSQL_DB (default: temple_db)

### 4. Download YOLO Model
Ensure `yolov8n.pt` is in the project root directory for AI detection.

### 5. Run Application
```bash
python app.py
```

## Features

### Pilgrim Features
- Register/Login with role-based access
- Book temple visit slots with time predictions
- View personal bookings with QR codes
- Check live crowd status and queue information
- Receive email confirmations with QR codes
- Interactive calendar booking system

### Admin Features
- Comprehensive dashboard with analytics
- Real-time crowd detection using YOLO AI
- **Advanced Queue Management System**
  - AI-powered queue zone detection
  - Real-time queue monitoring (Entry, Darshan, Prasad, Exit)
  - Queue flow optimization recommendations
  - Bottleneck identification and resolution
  - Wait time predictions and management
- Temple management (add/edit/delete)
- Booking management and QR verification
- Revenue tracking and reporting
- Email alert system for crowd control

## Queue Management System

### Key Features
- **Zone-based Detection**: Treats humans as vehicles and temple areas as roads/queues
- **Real-time Monitoring**: Live queue status with people counts and wait times
- **Flow Optimization**: AI recommendations for reducing bottlenecks
- **Visual Analytics**: Heatmaps, flow diagrams, and performance charts
- **Automated Alerts**: Notifications when queues exceed capacity
- **Predictive Analytics**: Wait time estimation and crowd flow prediction

### Queue Zones
1. **Entry Queue**: Temple entrance and security check area
2. **Darshan Queue**: Main worship area queue
3. **Prasad Queue**: Offering collection area
4. **Exit Queue**: Temple exit flow management

### Admin Queue Management URLs
- `/admin/queue-management` - Main queue monitoring dashboard
- `/admin/queue-analytics` - Advanced analytics and optimization
- `/detect-crowd` - AI-powered crowd detection interface

## Default Admin Account
- Email: admin@temple.com
- Password: admin123

## API Endpoints

### Crowd Management
- `/crowd-status` - Returns current crowd status as JSON
- `/update-crowd` - Admin endpoint to update crowd status
- `/api/temple/<id>/crowd` - Get specific temple crowd data

### Queue Management
- `/api/queue-detection` - POST endpoint for queue analysis
- `/api/queue-status/<temple_id>` - Get real-time queue status
- `/api/queue-analytics/<temple_id>` - Get comprehensive queue analytics
- `/api/queue-optimization/<temple_id>` - Apply AI optimization
- `/api/queue-config` - Configure queue zones

### Booking System
- `/api/book` - Create new booking with services
- `/api/verify-qr` - Verify QR codes for entry
- `/api/available-slots` - Get available time slots

## Database Tables
- `user` - User accounts (pilgrims and admins)
- `temple` - Temple information and settings
- `booking` - Temple visit bookings with confirmation IDs
- `crowd` - Real-time crowd status per temple
- `prasad` - Available prasad items per temple
- `pooja` - Available pooja services per temple
- `order` - QR-coded orders for services
- `order_item` - Individual items in orders

## AI/ML Components

### YOLO Object Detection
- Real-time person detection in temple areas
- Queue zone analysis and people counting
- Crowd density estimation with accuracy metrics

### Queue Management AI
- Flow pattern analysis
- Bottleneck prediction and prevention
- Optimization recommendations
- Wait time prediction algorithms

## Technology Stack
- **Backend**: Flask, SQLAlchemy, Flask-SocketIO
- **AI/ML**: YOLOv8, OpenCV, NumPy
- **Frontend**: Bootstrap 5, Chart.js, Socket.IO
- **Database**: MySQL with real-time updates
- **Email**: Flask-Mail with SMTP integration
- **Real-time**: WebSocket connections for live updates

## Queue Management Logic

The system treats temple crowd management like traffic flow:
- **Humans = Vehicles**: People moving through temple areas
- **Temple Areas = Roads**: Different zones with capacity limits
- **Queues = Traffic Lanes**: Organized flow paths with monitoring
- **Bottlenecks = Traffic Jams**: Areas requiring immediate attention
- **Optimization = Traffic Management**: AI-driven flow improvements

This approach enables:
- Predictive crowd control
- Efficient resource allocation
- Reduced waiting times
- Enhanced visitor experience
- Data-driven decision making