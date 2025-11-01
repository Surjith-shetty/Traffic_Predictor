from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit
from flask_mail import Mail, Message
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta, timezone
import os, random, string, json
try:
    from detect import detect_crowd, get_crowd_status, detect_crowd_with_boxes
except ImportError:
    def detect_crowd(source): return 0
    def get_crowd_status(count): return 'Low'
    def detect_crowd_with_boxes(source): return 0, None
from crowd_predictor import CrowdPredictor
try:
    from queue_manager import queue_manager
except ImportError:
    queue_manager = None
try:
    from visitor_journey import journey_optimizer
except ImportError:
    journey_optimizer = None
try:
    from smart_queue_routes import smart_queue_bp
except ImportError:
    smart_queue_bp = None
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object('config.Config')

db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
mail = Mail(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Initialize crowd predictor
crwd_predictor = CrowdPredictor()

# Register blueprints
if smart_queue_bp:
    app.register_blueprint(smart_queue_bp)

# Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='pilgrim')
    bookings = db.relationship('Booking', backref='user', lazy=True)

class Temple(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    capacity = db.Column(db.Integer, default=100)
    opening_time = db.Column(db.String(10), default='06:00')
    closing_time = db.Column(db.String(10), default='20:00')
    description = db.Column(db.Text)
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)

class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    temple_id = db.Column(db.Integer, db.ForeignKey('temple.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)
    persons = db.Column(db.Integer, nullable=False)
    confirmation_id = db.Column(db.String(20), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_status = db.Column(db.String(20), default='pending')
    transaction_id = db.Column(db.String(50))
    total_amount = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    temple = db.relationship('Temple', backref='bookings')

class Crowd(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    temple_id = db.Column(db.Integer, db.ForeignKey('temple.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Low')
    count = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float, default=0.0)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    temple = db.relationship('Temple', backref='crowd_data')

class Prasad(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    temple_id = db.Column(db.Integer, db.ForeignKey('temple.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    temple = db.relationship('Temple', backref='prasads')

class Pooja(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, default=30)  # minutes
    temple_id = db.Column(db.Integer, db.ForeignKey('temple.id'), nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    temple = db.relationship('Temple', backref='poojas')

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('booking.id'), nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    qr_code = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, collected
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    booking = db.relationship('Booking', backref='orders')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)  # prasad, pooja
    item_id = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, default=1)
    price = db.Column(db.Float, nullable=False)
    order = db.relationship('Order', backref='items')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_confirmation_id():
    """Generate unique confirmation ID"""
    return 'TMP' + ''.join(random.choices(string.digits, k=8))

def generate_qr_code():
    """Generate unique QR code for orders"""
    return 'QR' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def get_crowd_prediction(temple_id, date_str):
    """Dummy crowd prediction API"""
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    day_of_week = date_obj.weekday()
    
    if day_of_week in [0, 5, 6]:  # Monday, Saturday, Sunday
        crowd_levels = ['Medium', 'High', 'High', 'Medium', 'Low']
    else:
        crowd_levels = ['Low', 'Medium', 'Low', 'Low', 'Medium']
    
    return {
        'morning': crowd_levels[0],
        'afternoon': crowd_levels[1],
        'evening': crowd_levels[2]
    }

def generate_time_slots(temple, crowd_prediction):
    """Generate available time slots based on crowd prediction"""
    base_slots = [
        {'time': '06:00-08:00', 'period': 'morning', 'label': '6:00 AM - 8:00 AM'},
        {'time': '08:00-10:00', 'period': 'morning', 'label': '8:00 AM - 10:00 AM'},
        {'time': '10:00-12:00', 'period': 'morning', 'label': '10:00 AM - 12:00 PM'},
        {'time': '12:00-14:00', 'period': 'afternoon', 'label': '12:00 PM - 2:00 PM'},
        {'time': '14:00-16:00', 'period': 'afternoon', 'label': '2:00 PM - 4:00 PM'},
        {'time': '16:00-18:00', 'period': 'afternoon', 'label': '4:00 PM - 6:00 PM'},
        {'time': '18:00-20:00', 'period': 'evening', 'label': '6:00 PM - 8:00 PM'}
    ]
    
    for slot in base_slots:
        period = slot['period']
        crowd_level = crowd_prediction.get(period, 'Low')
        
        if crowd_level == 'Low':
            slot['available'] = True
            slot['capacity'] = temple.capacity
            slot['crowd_status'] = 'Low'
        elif crowd_level == 'Medium':
            slot['available'] = True
            slot['capacity'] = temple.capacity // 2
            slot['crowd_status'] = 'Medium'
        else:  # High
            slot['available'] = False
            slot['capacity'] = 0
            slot['crowd_status'] = 'High'
    
    return base_slots

def enhanced_detect_crowd(filepath):
    """Enhanced crowd detection with better accuracy"""
    try:
        count = detect_crowd(filepath)
        # Simulate accuracy based on detection confidence
        if count > 0:
            accuracy = min(0.95, 0.7 + (count / 100) * 0.2)  # Higher accuracy for more people
        else:
            accuracy = 0.8  # Base accuracy for empty detection
        return count, round(accuracy, 2)
    except:
        return 0, 0.0

def get_enhanced_crowd_status(count, temple_id):
    """Get crowd status based on temple capacity"""
    temple = Temple.query.get(temple_id)
    if not temple:
        return get_crowd_status(count)
    
    capacity_ratio = count / temple.capacity
    if capacity_ratio < 0.3:
        return 'Low'
    elif capacity_ratio < 0.7:
        return 'Medium'
    else:
        return 'High'

def send_crowd_alert(temple_id=None):
    """Send email alert to pilgrims when crowd status is High"""
    try:
        temple_name = 'the temple'
        if temple_id:
            temple = Temple.query.get(temple_id)
            temple_name = temple.name if temple else 'the temple'
        
        pilgrims = User.query.filter_by(role='pilgrim').all()
        for pilgrim in pilgrims:
            msg = Message(
                subject=f'Temple Alert - High Crowd at {temple_name}',
                recipients=[pilgrim.email],
                body=f'Dear {pilgrim.name}, please note {temple_name} is currently overcrowded. Consider visiting at a different time.'
            )
            mail.send(msg)
    except Exception as e:
        print(f'Email sending failed: {e}')

def send_booking_confirmation_email(booking, qr_code, order_amount):
    """Send booking confirmation email with QR code"""
    try:
        print(f"Attempting to send email to: {booking.user.email}")
        temple = booking.temple
        user = booking.user
        
        # Get order items if any
        prasad_items = []
        pooja_items = []
        
        if qr_code:
            order = Order.query.filter_by(qr_code=qr_code).first()
            if order:
                for item in order.items:
                    if item.item_type == 'prasad':
                        prasad = Prasad.query.get(item.item_id)
                        if prasad:
                            prasad_items.append(f'{prasad.name} x{item.quantity} - ₹{item.price}')
                    elif item.item_type == 'pooja':
                        pooja = Pooja.query.get(item.item_id)
                        if pooja:
                            pooja_items.append(f'{pooja.name} ({pooja.duration}min) - ₹{item.price}')
        
        # Create email content
        email_body = f"""Dear {user.name},

Your temple booking has been confirmed! 🙏

📍 Temple: {temple.name}
📅 Date: {booking.date.strftime('%d %B %Y')}
⏰ Time Slot: {booking.time_slot}
👥 Number of People: {booking.persons}
🎫 Booking ID: {booking.id}
🔖 Confirmation ID: {booking.confirmation_id}

💰 Darshan Fee: ₹{booking.persons * 50}"""
        
        # Always include QR code section with image URL
        qr_image_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={qr_code}"
        email_body += f"\n\n📱 Your QR Code: {qr_code}"
        email_body += f"\n\n🖼️ QR Code Image: {qr_image_url}"
        email_body += "\n\n⚡ IMPORTANT: Show this QR code at temple entrance for verification!"
        email_body += "\n(You can scan the QR code image above or show this email to temple staff)"
        
        if prasad_items or pooja_items:
            email_body += f"\n\n🛍️ Pre-booked Services (₹{order_amount}):"
            if prasad_items:
                email_body += "\n\n📦 Prasad Items:"
                for item in prasad_items:
                    email_body += f"\n• {item}"
            if pooja_items:
                email_body += "\n\n🕯️ Pooja Services:"
                for item in pooja_items:
                    email_body += f"\n• {item}"
            email_body += "\n\n⚡ Show QR code at Pre-booked Collection counter for services!"
        else:
            email_body += "\n\n🙏 This QR code is for darshan entry verification."
        
        email_body += f"""\n\n📋 Instructions:
1. Arrive at {temple.name} on {booking.date.strftime('%d %B %Y')}
2. Report to the temple between {booking.time_slot}
3. Show this email and QR code (if applicable) for verification
4. Enjoy your divine darshan! 🙏

🏛️ Temple Timings: {temple.opening_time or '6:00 AM'} - {temple.closing_time or '8:00 PM'}
📍 Location: {temple.location}

Thank you for choosing Divine Darshan!

Blessings,
Temple Management Team"""
        
        # Create HTML version with embedded QR code image
        html_body = email_body.replace('\n', '<br>').replace(f'QR Code Image: {qr_image_url}', f'<br><img src="{qr_image_url}" alt="QR Code" style="width:200px;height:200px;"><br>')
        
        msg = Message(
            subject=f'🕉️ Booking Confirmed - {temple.name} | {booking.confirmation_id}',
            recipients=[user.email],
            body=email_body,
            html=html_body
        )
        mail.send(msg)
        print(f"✅ Email sent successfully to {booking.user.email}")
        
    except Exception as e:
        print(f'❌ Booking confirmation email failed: {e}')
        print(f'Email config: {app.config["MAIL_USERNAME"]}, Server: {app.config["MAIL_SERVER"]}')
        # Try to send a simple test email
        try:
            test_msg = Message(
                subject='Test Email',
                recipients=[booking.user.email],
                body='This is a test email from Divine Darshan'
            )
            mail.send(test_msg)
            print("✅ Test email sent successfully")
        except Exception as test_error:
            print(f'❌ Test email also failed: {test_error}')

# Routes
@app.route('/')
def index():
    temples = Temple.query.filter_by(is_active=True).all()
    # Ensure all temples have crowd data
    for temple in temples:
        existing_crowd = Crowd.query.filter_by(temple_id=temple.id).first()
        if not existing_crowd:
            crowd = Crowd(temple_id=temple.id, status='Low', count=0, accuracy=1.0)
            db.session.add(crowd)
    db.session.commit()
    return render_template('index.html', temples=temples)

@app.route('/index')
def old_index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'pilgrim')
        
        if User.query.filter_by(email=email).first():
            flash('Email already exists')
            return redirect(url_for('register'))
        
        user = User(
            name=name,
            email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.commit()
        
        flash('Registration successful')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        user = User.query.filter_by(email=email).first()
        
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            if user.role == 'admin':
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('temples'))
        else:
            flash('Invalid credentials')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/temples')
def temples():
    temples = Temple.query.filter_by(is_active=True).all()
    return render_template('temples.html', temples=temples)

@app.route('/temple/<int:temple_id>')
def temple_detail(temple_id):
    temple = Temple.query.get_or_404(temple_id)
    crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
    prasads = Prasad.query.filter_by(temple_id=temple_id, is_available=True).all()
    poojas = Pooja.query.filter_by(temple_id=temple_id, is_available=True).all()
    today = datetime.now().strftime('%Y-%m-%d')
    
    # Check if user wants calendar view
    if request.args.get('calendar') == 'true':
        return render_template('calendar_booking.html', temple=temple)
    
    return render_template('temple_detail.html', temple=temple, crowd=crowd, prasads=prasads, poojas=poojas, today=today)

@app.route('/temple/<int:temple_id>/guide')
def temple_guide(temple_id):
    temple = Temple.query.get_or_404(temple_id)
    prasads = Prasad.query.filter_by(temple_id=temple_id, is_available=True).all()
    poojas = Pooja.query.filter_by(temple_id=temple_id, is_available=True).all()
    return render_template('temple_guide.html', temple=temple, prasads=prasads, poojas=poojas)



@app.route('/booking-confirmation/<int:booking_id>')
@login_required
def booking_confirmation(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        flash('Unauthorized access')
        return redirect(url_for('my_bookings'))
    return render_template('booking_confirmation.html', booking=booking)

@app.route('/my-bookings')
@login_required
def my_bookings():
    if current_user.role != 'pilgrim':
        return redirect(url_for('admin'))
    
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.created_at.desc()).all()
    return render_template('my_bookings.html', bookings=bookings)

@app.route('/admin')
@login_required
def admin():
    if current_user.role != 'admin':
        return redirect(url_for('book'))
    
    bookings = Booking.query.join(User).join(Temple).order_by(Booking.created_at.desc()).limit(20).all()
    temples = Temple.query.all()
    total_bookings = Booking.query.count()
    crowd = Crowd.query.order_by(Crowd.updated_at.desc()).first()
    if not crowd and temples:
        crowd = Crowd(temple_id=temples[0].id, status='Low', count=0, accuracy=1.0)
        db.session.add(crowd)
        db.session.commit()
    
    return render_template('admin.html', bookings=bookings, temples=temples, 
                         total_bookings=total_bookings, 
                         crowd_status=crowd.status if crowd else 'Low', 
                         crowd_count=crowd.count if crowd else 0)

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    # Analytics data
    today = datetime.now().date()
    temples = Temple.query.all()
    total_users = User.query.count()
    total_bookings = Booking.query.count()
    total_revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
        Booking.payment_status == 'completed'
    ).scalar() or 0
    
    # Daily visitors for last 7 days
    daily_visitors = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = Booking.query.filter(
            db.func.date(Booking.created_at) == date,
            Booking.payment_status == 'completed'
        ).count()
        daily_visitors.append({'date': date.strftime('%Y-%m-%d'), 'count': count})
    
    # Temple-wise bookings
    temple_bookings = []
    for temple in temples:
        count = Booking.query.filter_by(temple_id=temple.id).count()
        revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
            Booking.temple_id == temple.id,
            Booking.payment_status == 'completed'
        ).scalar() or 0
        temple_bookings.append({
            'name': temple.name,
            'bookings': count,
            'revenue': revenue
        })
    
    return render_template('admin_dashboard.html',
                         temples=temples,
                         total_users=total_users,
                         total_bookings=total_bookings,
                         total_revenue=total_revenue,
                         daily_visitors=daily_visitors,
                         temple_bookings=temple_bookings)

@app.route('/admin/temples')
@login_required
def admin_temples():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temples = Temple.query.all()
    return render_template('admin_temples.html', temples=temples)

@app.route('/admin/temple/add', methods=['GET', 'POST'])
@login_required
def add_temple():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        temple = Temple(
            name=request.form['name'],
            location=request.form['location'],
            latitude=float(request.form['latitude']) if request.form['latitude'] else None,
            longitude=float(request.form['longitude']) if request.form['longitude'] else None,
            capacity=int(request.form['capacity']),
            opening_time=request.form['opening_time'],
            closing_time=request.form['closing_time'],
            description=request.form['description'],
            image_url=request.form['image_url']
        )
        db.session.add(temple)
        db.session.flush()  # Get temple ID
        
        # Create initial crowd data for new temple
        crowd = Crowd(
            temple_id=temple.id,
            status='Low',
            count=0,
            accuracy=1.0
        )
        db.session.add(crowd)
        db.session.commit()
        flash('Temple added successfully')
        return redirect(url_for('admin_temples'))
    
    return render_template('add_temple.html')

@app.route('/admin/temple/edit/<int:temple_id>', methods=['GET', 'POST'])
@login_required
def edit_temple(temple_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temple = Temple.query.get_or_404(temple_id)
    
    if request.method == 'POST':
        temple.name = request.form['name']
        temple.location = request.form['location']
        temple.latitude = float(request.form['latitude']) if request.form['latitude'] else None
        temple.longitude = float(request.form['longitude']) if request.form['longitude'] else None
        temple.capacity = int(request.form['capacity'])
        temple.opening_time = request.form['opening_time']
        temple.closing_time = request.form['closing_time']
        temple.description = request.form['description']
        temple.image_url = request.form['image_url']
        temple.is_active = 'is_active' in request.form
        
        db.session.commit()
        flash('Temple updated successfully')
        return redirect(url_for('admin_temples'))
    
    return render_template('edit_temple.html', temple=temple)

@app.route('/admin/temple/delete/<int:temple_id>', methods=['POST'])
@login_required
def delete_temple(temple_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temple = Temple.query.get_or_404(temple_id)
    temple.is_active = False
    db.session.commit()
    flash('Temple deactivated successfully')
    return redirect(url_for('admin_temples'))

@app.route('/admin/bookings')
@login_required
def admin_bookings():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    temple_id = request.args.get('temple_id', type=int)
    
    query = Booking.query.join(User).join(Temple)
    
    if temple_id:
        query = query.filter(Booking.temple_id == temple_id)
    
    bookings = query.order_by(Booking.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    temples = Temple.query.all()
    
    return render_template('admin_bookings.html', 
                         bookings=bookings, 
                         temples=temples, 
                         selected_temple=temple_id)

@app.route('/admin/init-crowd-data')
@login_required
def init_crowd_data():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    # Initialize crowd data for temples that don't have it
    temples = Temple.query.filter_by(is_active=True).all()
    initialized = 0
    
    for temple in temples:
        existing_crowd = Crowd.query.filter_by(temple_id=temple.id).first()
        if not existing_crowd:
            crowd = Crowd(
                temple_id=temple.id,
                status='Low',
                count=0,
                accuracy=1.0
            )
            db.session.add(crowd)
            initialized += 1
    
    db.session.commit()
    flash(f'Initialized crowd data for {initialized} temples')
    return redirect(url_for('admin_temples'))

@app.route('/api/admin/analytics')
@login_required
def admin_analytics_api():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Daily visitors for last 30 days
    today = datetime.now().date()
    daily_data = []
    
    for i in range(30):
        date = today - timedelta(days=i)
        visitors = db.session.query(db.func.sum(Booking.persons)).filter(
            db.func.date(Booking.created_at) == date,
            Booking.payment_status == 'completed'
        ).scalar() or 0
        
        revenue = db.session.query(db.func.sum(Booking.total_amount)).filter(
            db.func.date(Booking.created_at) == date,
            Booking.payment_status == 'completed'
        ).scalar() or 0
        
        daily_data.append({
            'date': date.strftime('%Y-%m-%d'),
            'visitors': visitors,
            'revenue': float(revenue)
        })
    
    # Temple-wise statistics
    temple_stats = []
    temples = Temple.query.filter_by(is_active=True).all()
    
    for temple in temples:
        bookings = Booking.query.filter_by(temple_id=temple.id).count()
        visitors = db.session.query(db.func.sum(Booking.persons)).filter(
            Booking.temple_id == temple.id,
            Booking.payment_status == 'completed'
        ).scalar() or 0
        
        temple_stats.append({
            'name': temple.name,
            'bookings': bookings,
            'visitors': visitors
        })
    
    return jsonify({
        'daily_data': daily_data,
        'temple_stats': temple_stats
    })

@app.route('/update-crowd', methods=['POST'])
@login_required
def update_crowd():
    if current_user.role != 'admin':
        if request.is_json:
            return jsonify({'error': 'Unauthorized'}), 403
        return redirect(url_for('book'))
    
    if request.is_json:
        temple_id = request.json.get('temple_id')
        status = request.json.get('status', 'Low')
        count = int(request.json.get('count', 0))
    else:
        temple_id = request.form.get('temple_id')
        status = request.form.get('status', 'Low')
        count = int(request.form.get('count', 0))
    
    if not temple_id:
        first_temple = Temple.query.first()
        if first_temple:
            temple_id = first_temple.id
        else:
            return jsonify({'error': 'No temples found'}), 400
    
    temple_id = int(temple_id)
    
    crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
    if crowd:
        crowd.status = status
        crowd.count = count
        crowd.updated_at = datetime.now(timezone.utc)
    else:
        crowd = Crowd(temple_id=temple_id, status=status, count=count, accuracy=1.0)
        db.session.add(crowd)
    
    db.session.commit()
    socketio.emit('crowd_update', {
        'temple_id': temple_id,
        'status': status,
        'count': count,
        'accuracy': crowd.accuracy
    })
    
    # Send crowd alert when status is High
    if status == 'High':
        send_crowd_alert(temple_id)
    
    if request.is_json:
        return jsonify({'success': True})
    
    flash(f'Crowd status updated to {status}')
    return redirect(url_for('admin'))

# API Routes
@app.route('/api/temples')
def api_temples():
    temples = Temple.query.filter_by(is_active=True).all()
    return jsonify([{
        'id': t.id, 'name': t.name, 'location': t.location,
        'latitude': t.latitude, 'longitude': t.longitude,
        'capacity': t.capacity, 'image_url': t.image_url
    } for t in temples])

@app.route('/api/book', methods=['POST'])
@login_required
def api_book():
    try:
        data = request.json
        confirmation_id = generate_confirmation_id()
        
        # Calculate total amount
        darshan_fee = data['persons'] * 50
        services_amount = 0
        
        # Calculate services amount
        if 'prasads' in data and data['prasads']:
            for prasad_data in data['prasads']:
                prasad = Prasad.query.get(prasad_data['id'])
                if prasad:
                    services_amount += prasad.price * prasad_data['quantity']
        
        if 'poojas' in data and data['poojas']:
            for pooja_data in data['poojas']:
                pooja = Pooja.query.get(pooja_data['id'])
                if pooja:
                    services_amount += pooja.price
        
        total_amount = darshan_fee + services_amount
        
        booking = Booking(
            user_id=current_user.id,
            temple_id=data.get('temple_id'),
            date=datetime.strptime(data['date'], '%Y-%m-%d').date(),
            time_slot=data['time_slot'],
            persons=data['persons'],
            confirmation_id=confirmation_id,
            total_amount=total_amount,
            status='pending',
            payment_status='pending'
        )
        db.session.add(booking)
        db.session.flush()  # Get booking ID
        
        # Process prasad and pooja orders if any
        total_order_amount = 0
        order_items = []
        
        if 'prasads' in data and data['prasads']:
            for prasad_data in data['prasads']:
                prasad = Prasad.query.get(prasad_data['id'])
                if prasad:
                    quantity = prasad_data['quantity']
                    total_order_amount += prasad.price * quantity
                    order_items.append({
                        'type': 'prasad',
                        'id': prasad.id,
                        'quantity': quantity,
                        'price': prasad.price * quantity
                    })
        
        if 'poojas' in data and data['poojas']:
            for pooja_data in data['poojas']:
                pooja = Pooja.query.get(pooja_data['id'])
                if pooja:
                    total_order_amount += pooja.price
                    order_items.append({
                        'type': 'pooja',
                        'id': pooja.id,
                        'quantity': 1,
                        'price': pooja.price
                    })
        
        # Always create order with QR code for every booking
        qr_code = generate_qr_code()
        order = Order(
            booking_id=booking.id,
            total_amount=total_order_amount,
            qr_code=qr_code
        )
        db.session.add(order)
        db.session.flush()
        
        # Add order items if any
        for item in order_items:
            order_item = OrderItem(
                order_id=order.id,
                item_type=item['type'],
                item_id=item['id'],
                quantity=item['quantity'],
                price=item['price']
            )
            db.session.add(order_item)
        
        db.session.commit()
        
        # Email will be sent after payment completion
        
        # Emit real-time update
        socketio.emit('new_booking', {
            'id': booking.id,
            'user': current_user.name,
            'date': data['date'],
            'time_slot': data['time_slot'],
            'persons': data['persons'],
            'confirmation_id': confirmation_id,
            'order_amount': total_order_amount,
            'qr_code': qr_code
        })
        
        return jsonify({
            'success': True,
            'booking_id': booking.id,
            'confirmation_id': confirmation_id,
            'total_amount': total_amount,
            'qr_code': qr_code,
            'order_amount': total_order_amount if total_order_amount > 0 else 0
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/temple/<int:temple_id>/crowd')
def api_temple_crowd(temple_id):
    crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
    if crowd:
        return jsonify({'status': crowd.status, 'count': crowd.count, 'accuracy': crowd.accuracy})
    return jsonify({'status': 'Low', 'count': 0, 'accuracy': 0.0})

@app.route('/api/available-slots')
def available_slots():
    temple_id = request.args.get('temple_id')
    date_str = request.args.get('date')
    
    if not temple_id or not date_str:
        return jsonify({'error': 'Missing parameters'}), 400
    
    temple = Temple.query.get(temple_id)
    if not temple:
        return jsonify({'error': 'Temple not found'}), 404
    
    # Get AI-based crowd prediction
    crowd_level = crwd_predictor.get_crowd_prediction(date_str, temple.name)
    crowd_prediction = {
        'morning': crowd_level,
        'afternoon': crowd_level, 
        'evening': crowd_level
    }
    
    slots = generate_time_slots(temple, crowd_prediction)
    return jsonify({'slots': slots, 'crowd_prediction': crowd_prediction, 'predicted_crowd': crowd_level})

@app.route('/api/chatbot', methods=['POST'])
def chatbot():
    try:
        from chatbot import temple_chatbot
        from indian_states_guide import indian_states_guide
        
        data = request.json
        message = data.get('message', '')
        chat_type = data.get('type', 'booking')  # 'booking' or 'guide'
        user_id = current_user.id if current_user.is_authenticated else 'guest_' + str(hash(request.remote_addr))
        
        # Indian states temple guide (no login required)
        if chat_type == 'guide' or any(word in message.lower() for word in ['guide', 'indian', 'state', 'navigation', 'direction', 'temple']):
            response = indian_states_guide.process_message(message, user_id)
            
            # Quick replies for Indian guide
            quick_replies = []
            if user_id in indian_states_guide.conversation_state:
                state = indian_states_guide.conversation_state[user_id]['step']
                if state == 'temple_selection':
                    quick_replies = ['Tirupati Balaji', 'Meenakshi Temple', 'Siddhivinayak', 'Shirdi Sai Baba', 'Somnath', 'Golden Temple']
                elif state == 'guide_type':
                    quick_replies = ['Step-by-step Navigation', 'Complete Guide', 'Cultural Info', 'Booking Help']
                else:
                    quick_replies = ['Navigation Guide', 'Another temple', 'Start over']
            
            return jsonify({
                'response': response,
                'quick_replies': quick_replies,
                'type': 'guide'
            })
        
        # Booking chatbot (requires login)
        if not current_user.is_authenticated:
            return jsonify({
                'response': 'For booking assistance, please login first. 🙏\n\nFor temple navigation guidance, try our **Temple Navigation Guide** - no login required!\n\nJust say "Tirupati Balaji" or select any temple name for directions.',
                'quick_replies': ['Login', 'Register', 'Tirupati Balaji', 'Meenakshi Temple']
            })
        
        response = temple_chatbot.process_message(message, user_id)
        
        # Add quick replies based on conversation state
        quick_replies = []
        if user_id in temple_chatbot.conversation_state:
            state = temple_chatbot.conversation_state[user_id]['step']
            if state == 'greeting':
                quick_replies = ['Book Somnath Temple', 'Book Dwarka Temple', 'Book Ambaji Temple']
            elif state == 'date':
                quick_replies = ['Tomorrow', 'Next Sunday', 'Next Week']
            elif state == 'time':
                quick_replies = ['Morning (6-8 AM)', 'Afternoon (12-2 PM)', 'Evening (6-8 PM)']
            elif state == 'persons':
                quick_replies = ['1 person', '2 people', '4 people']
            elif state == 'extras':
                quick_replies = ['Add Laddu', 'Add Aarti', 'No extras']
            elif state == 'confirm':
                quick_replies = ['Yes, Confirm', 'No, Cancel']
        
        return jsonify({
            'response': response,
            'quick_replies': quick_replies,
            'type': 'booking'
        })
        
    except Exception as e:
        return jsonify({
            'response': f'Sorry, I encountered an error: {str(e)}. Please try again.',
            'quick_replies': ['Help', 'Start Over']
        })

@app.route('/crowd-status')
def crowd_status():
    temple_id = request.args.get('temple_id')
    if temple_id:
        crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
        if not crowd:
            # Create crowd data if it doesn't exist
            temple = Temple.query.get(temple_id)
            if temple and temple.is_active:
                crowd = Crowd(temple_id=temple_id, status='Low', count=0, accuracy=1.0)
                db.session.add(crowd)
                db.session.commit()
    else:
        crowd = Crowd.query.order_by(Crowd.updated_at.desc()).first()
    
    if crowd:
        return jsonify({'status': crowd.status, 'count': crowd.count, 'accuracy': crowd.accuracy})
    return jsonify({'status': 'Low', 'count': 0, 'accuracy': 0.0})

@app.route('/crowd')
def crowd_page():
    temples = Temple.query.filter_by(is_active=True).all()
    # Ensure all temples have crowd data
    for temple in temples:
        existing_crowd = Crowd.query.filter_by(temple_id=temple.id).first()
        if not existing_crowd:
            crowd = Crowd(temple_id=temple.id, status='Low', count=0, accuracy=1.0)
            db.session.add(crowd)
    db.session.commit()
    return render_template('crowd.html', temples=temples)

@app.route('/live-detection/<int:temple_id>')
@login_required
def live_detection(temple_id):
    """Simulate live crowd detection for real-time monitoring"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Simulate real-time detection with random but realistic data
    import random
    temple = Temple.query.get_or_404(temple_id)
    
    # Generate realistic crowd data based on time of day
    hour = datetime.now().hour
    if 6 <= hour <= 10:  # Morning rush
        base_count = random.randint(20, 60)
    elif 11 <= hour <= 14:  # Afternoon
        base_count = random.randint(40, 80)
    elif 17 <= hour <= 20:  # Evening rush
        base_count = random.randint(50, 100)
    else:  # Off hours
        base_count = random.randint(5, 25)
    
    count = min(base_count, temple.capacity)
    accuracy = random.uniform(0.85, 0.98)
    status = get_enhanced_crowd_status(count, temple_id)
    
    # Update database
    existing_crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
    if existing_crowd:
        existing_crowd.status = status
        existing_crowd.count = count
        existing_crowd.accuracy = accuracy
        existing_crowd.updated_at = datetime.now(timezone.utc)
    else:
        crowd = Crowd(
            temple_id=temple_id,
            status=status,
            count=count,
            accuracy=accuracy,
            updated_at=datetime.now(timezone.utc)
        )
        db.session.add(crowd)
    db.session.commit()
    
    # Emit real-time update
    socketio.emit('crowd_update', {
        'temple_id': temple_id,
        'status': status,
        'count': count,
        'accuracy': accuracy
    })
    
    return jsonify({
        'count': count,
        'status': status,
        'accuracy': accuracy,
        'temple_id': temple_id,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/detect-crowd', methods=['GET', 'POST'])
@login_required
def detect_crowd_route():
    if current_user.role != 'admin':
        return redirect(url_for('book'))
    
    temples = Temple.query.filter_by(is_active=True).all()
    
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        temple_id = request.form.get('temple_id')
        
        if file.filename == '' or not temple_id:
            return jsonify({'error': 'File and temple selection required'}), 400
        
        filename = secure_filename(file.filename)
        filepath = os.path.join('uploads', filename)
        os.makedirs('uploads', exist_ok=True)
        
        try:
            file.save(filepath)
            count, annotated_path = detect_crowd_with_boxes(filepath)
            accuracy = min(0.95, 0.7 + (count / 100) * 0.2) if count > 0 else 0.8
            status = get_enhanced_crowd_status(count, int(temple_id))
            
            existing_crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
            if existing_crowd:
                existing_crowd.status = status
                existing_crowd.count = count
                existing_crowd.accuracy = accuracy
                existing_crowd.updated_at = datetime.now(timezone.utc)
            else:
                crowd = Crowd(
                    temple_id=temple_id,
                    status=status,
                    count=count,
                    accuracy=accuracy,
                    updated_at=datetime.now(timezone.utc)
                )
                db.session.add(crowd)
            db.session.commit()
            
            socketio.emit('crowd_update', {
                'temple_id': temple_id,
                'status': status,
                'count': count,
                'accuracy': accuracy
            })
            
            # Send crowd alert when status is High
            if status == 'High':
                send_crowd_alert(temple_id)
            
            # Copy annotated image to static folder for web display
            annotated_filename = None
            if annotated_path and os.path.exists(annotated_path):
                import shutil
                annotated_filename = f'detected_{filename}'
                static_path = os.path.join('static', annotated_filename)
                os.makedirs('static', exist_ok=True)
                shutil.copy2(annotated_path, static_path)
            
            return jsonify({
                'count': count,
                'status': status,
                'accuracy': accuracy,
                'temple_id': temple_id,
                'annotated_image': annotated_filename
            })
            
        except Exception as e:
            return jsonify({'error': f'Detection failed: {str(e)}'}), 500
        
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
    
    return render_template('detect_crowd.html', temples=temples)

@app.route('/crowd')
def crowd():
    return render_template('crowd.html')

@app.route('/qr-scan')
@login_required
def qr_scan():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return render_template('qr_scan.html')

@app.route('/api/verify-qr', methods=['POST'])
@login_required
def verify_qr():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    qr_code = request.json.get('qr_code')
    if not qr_code:
        return jsonify({'error': 'QR code is required'}), 400
    
    print(f'Verifying QR code: {qr_code}')  # Debug log
    
    order = Order.query.filter_by(qr_code=qr_code).first()
    
    if not order:
        print(f'QR code not found: {qr_code}')  # Debug log
        return jsonify({'error': 'Invalid QR code'}), 404
    
    if order.status == 'collected':
        return jsonify({'error': 'Order already collected'}), 400
    
    # Get order details
    prasads = []
    poojas = []
    
    for item in order.items:
        if item.item_type == 'prasad':
            prasad = Prasad.query.get(item.item_id)
            if prasad:
                prasads.append({
                    'name': prasad.name,
                    'quantity': item.quantity,
                    'price': item.price
                })
        elif item.item_type == 'pooja':
            pooja = Pooja.query.get(item.item_id)
            if pooja:
                poojas.append({
                    'name': pooja.name,
                    'duration': pooja.duration,
                    'price': item.price
                })
    
    print(f'QR verification successful for order: {order.id}')  # Debug log
    
    # Calculate total including darshan fee
    darshan_fee = order.booking.persons * 50
    services_amount = order.total_amount
    grand_total = darshan_fee + services_amount
    
    return jsonify({
        'success': True,
        'order_id': order.id,
        'booking_id': order.booking_id,
        'user_name': order.booking.user.name,
        'temple_name': order.booking.temple.name,
        'booking_date': order.booking.date.strftime('%d %B %Y'),
        'time_slot': order.booking.time_slot,
        'persons': order.booking.persons,
        'total_amount': grand_total,
        'darshan_fee': darshan_fee,
        'services_amount': services_amount,
        'prasads': prasads,
        'poojas': poojas,
        'status': order.status
    })

@app.route('/api/collect-order', methods=['POST'])
@login_required
def collect_order():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    order_id = request.json.get('order_id')
    order = Order.query.get(order_id)
    
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    order.status = 'collected'
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Order marked as collected'})

@app.route('/pilgrim-dashboard')
@login_required
def pilgrim_dashboard():
    if current_user.role != 'pilgrim':
        return redirect(url_for('admin'))
    return render_template('pilgrim_dashboard.html')

@app.route('/temple-dashboard')
@login_required
def temple_dashboard():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temples = Temple.query.filter_by(is_active=True).all()
    today = datetime.now().date()
    
    # Today's bookings
    today_bookings = Booking.query.filter(
        db.func.date(Booking.created_at) == today
    ).join(Temple).join(User).all()
    
    # Today's orders with QR codes
    today_orders = Order.query.join(Booking).filter(
        db.func.date(Booking.created_at) == today
    ).all()
    
    # Revenue stats
    today_revenue = db.session.query(db.func.sum(Order.total_amount)).join(Booking).filter(
        db.func.date(Booking.created_at) == today
    ).scalar() or 0
    
    pending_orders = Order.query.filter_by(status='pending').count()
    collected_orders = Order.query.filter_by(status='collected').count()
    
    return render_template('temple_dashboard.html', 
                         temples=temples, today_bookings=today_bookings, 
                         today_orders=today_orders, today_revenue=today_revenue,
                         pending_orders=pending_orders, collected_orders=collected_orders)

@app.route('/camera-scanner')
@login_required
def camera_scanner():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    return render_template('camera_scanner.html')

@app.route('/payment/<int:booking_id>')
@login_required
def payment_page(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return redirect(url_for('my_bookings'))
    
    if booking.payment_status == 'completed':
        return redirect(url_for('payment_receipt', booking_id=booking_id))
    
    return render_template('payment.html', booking=booking)

@app.route('/api/process-payment', methods=['POST'])
@login_required
def process_payment():
    data = request.json
    booking_id = data.get('booking_id')
    
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Dummy payment gateway simulation
    import random
    payment_success = random.choice([True, True, True, True, True, False])  # 83% success rate
    
    if payment_success:
        # Generate transaction ID
        transaction_id = f'TXN{random.randint(100000, 999999)}'
        
        # Update booking status
        booking.payment_status = 'completed'
        booking.status = 'confirmed'
        booking.transaction_id = transaction_id
        db.session.commit()
        
        # Send confirmation email only after successful payment
        try:
            qr_code = None
            order_amount = 0
            for order in booking.orders:
                qr_code = order.qr_code
                order_amount = order.total_amount
                break
            send_booking_confirmation_email(booking, qr_code, order_amount)
        except Exception as e:
            print(f'Email sending failed: {e}')
            # Continue without email - booking still successful
            pass
        
        return jsonify({
            'success': True,
            'transaction_id': transaction_id,
            'message': 'Payment successful'
        })
    else:
        return jsonify({
            'success': False,
            'message': 'Payment failed. Please try again.'
        })

@app.route('/payment-receipt/<int:booking_id>')
@login_required
def payment_receipt(booking_id):
    booking = Booking.query.get_or_404(booking_id)
    if booking.user_id != current_user.id:
        return redirect(url_for('my_bookings'))
    
    if booking.payment_status != 'completed':
        return redirect(url_for('payment_page', booking_id=booking_id))
    
    return render_template('payment_receipt.html', booking=booking)

@app.route('/admin/prasad-pooja')
@login_required
def manage_prasad_pooja():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temples = Temple.query.filter_by(is_active=True).all()
    prasads = Prasad.query.join(Temple).all()
    poojas = Pooja.query.join(Temple).all()
    
    # Revenue statistics
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    prasad_revenue = db.session.query(db.func.sum(OrderItem.price)).filter(OrderItem.item_type == 'prasad').scalar() or 0
    pooja_revenue = db.session.query(db.func.sum(OrderItem.price)).filter(OrderItem.item_type == 'pooja').scalar() or 0
    
    return render_template('manage_prasad_pooja.html', 
                         temples=temples, prasads=prasads, poojas=poojas,
                         total_revenue=total_revenue, prasad_revenue=prasad_revenue, pooja_revenue=pooja_revenue)

@app.route('/api/prasad', methods=['POST', 'PUT', 'DELETE'])
@login_required
def manage_prasad_api():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.json
        prasad = Prasad(
            name=data['name'],
            price=float(data['price']),
            temple_id=int(data['temple_id'])
        )
        db.session.add(prasad)
        db.session.commit()
        return jsonify({'success': True, 'id': prasad.id})
    
    elif request.method == 'PUT':
        data = request.json
        prasad = Prasad.query.get(data['id'])
        if prasad:
            prasad.name = data['name']
            prasad.price = float(data['price'])
            prasad.is_available = data.get('is_available', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Prasad not found'}), 404
    
    elif request.method == 'DELETE':
        prasad_id = request.json.get('id')
        prasad = Prasad.query.get(prasad_id)
        if prasad:
            db.session.delete(prasad)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Prasad not found'}), 404

@app.route('/api/pooja', methods=['POST', 'PUT', 'DELETE'])
@login_required
def manage_pooja_api():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if request.method == 'POST':
        data = request.json
        pooja = Pooja(
            name=data['name'],
            price=float(data['price']),
            duration=int(data['duration']),
            temple_id=int(data['temple_id'])
        )
        db.session.add(pooja)
        db.session.commit()
        return jsonify({'success': True, 'id': pooja.id})
    
    elif request.method == 'PUT':
        data = request.json
        pooja = Pooja.query.get(data['id'])
        if pooja:
            pooja.name = data['name']
            pooja.price = float(data['price'])
            pooja.duration = int(data['duration'])
            pooja.is_available = data.get('is_available', True)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Pooja not found'}), 404
    
    elif request.method == 'DELETE':
        pooja_id = request.json.get('id')
        pooja = Pooja.query.get(pooja_id)
        if pooja:
            db.session.delete(pooja)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'error': 'Pooja not found'}), 404

@app.route('/api/revenue-stats')
@login_required
def revenue_stats():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Daily revenue
    today = datetime.now().date()
    daily_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        db.func.date(Order.created_at) == today
    ).scalar() or 0
    
    # Monthly revenue
    month_start = today.replace(day=1)
    monthly_revenue = db.session.query(db.func.sum(Order.total_amount)).filter(
        Order.created_at >= month_start
    ).scalar() or 0
    
    # Total bookings today
    daily_bookings = Booking.query.filter(
        db.func.date(Booking.created_at) == today
    ).count()
    
    return jsonify({
        'daily_revenue': daily_revenue,
        'monthly_revenue': monthly_revenue,
        'daily_bookings': daily_bookings
    })

@app.route('/api/calendar-predictions')
def calendar_predictions():
    temple_id = request.args.get('temple_id')
    year = int(request.args.get('year', datetime.now().year))
    month = int(request.args.get('month', datetime.now().month))
    
    temple = Temple.query.get(temple_id)
    if not temple:
        return jsonify({'error': 'Temple not found'}), 404
    
    calendar_data = crwd_predictor.get_calendar_data(year, month, temple.name)
    return jsonify(calendar_data)

@app.route('/api/temple-guide/<int:temple_id>')
def temple_guide_api(temple_id):
    temple = Temple.query.get_or_404(temple_id)
    crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
    
    # Generate quick guide data
    guide_data = {
        'temple': {
            'name': temple.name,
            'location': temple.location,
            'opening_time': temple.opening_time or '6:00 AM',
            'closing_time': temple.closing_time or '8:00 PM',
            'capacity': temple.capacity
        },
        'crowd_status': {
            'status': crowd.status if crowd else 'Low',
            'count': crowd.count if crowd else 0,
            'last_updated': crowd.updated_at.isoformat() if crowd else None
        },
        'best_times': {
            'least_crowded': ['6:00 AM - 9:00 AM', '7:00 PM - 8:00 PM'],
            'moderate': ['9:00 AM - 11:00 AM', '4:00 PM - 6:00 PM'],
            'most_crowded': ['11:00 AM - 2:00 PM']
        },
        'estimated_time': {
            'quick_visit': '30-45 minutes',
            'regular_visit': '1-2 hours',
            'complete_visit': '2-3 hours'
        },
        'tips': [
            'Book slots in advance to avoid waiting',
            'Arrive 15 minutes before your slot time',
            'Dress modestly and appropriately',
            'Keep mobile phones on silent mode',
            'Follow queue discipline'
        ]
    }
    
    return jsonify(guide_data)

@app.route('/api/visitor-journey/<int:temple_id>')
def visitor_journey_api(temple_id):
    temple = Temple.query.get_or_404(temple_id)
    crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
    
    if not journey_optimizer:
        return jsonify({'error': 'Journey optimizer not available'}), 500
    
    # Get user preferences from request
    visit_type = request.args.get('visit_type', 'regular')
    first_time = request.args.get('first_time', 'false').lower() == 'true'
    group_size = int(request.args.get('group_size', 1))
    
    # Build user profile and preferences
    user_profile = {
        'visit_count': 0 if first_time else 1
    }
    
    visit_preferences = {
        'visit_type': visit_type,
        'first_time': first_time,
        'group_size': group_size
    }
    
    # Build temple data
    temple_data = {
        'capacity': temple.capacity,
        'crowd_status': crowd.status if crowd else 'Low',
        'services': ['prasad_shop', 'special_pooja']  # Default services
    }
    
    # Generate personalized journey
    journey = journey_optimizer.get_personalized_journey(user_profile, temple_data, visit_preferences)
    
    # Generate step-by-step guide
    steps = journey_optimizer.generate_step_by_step_guide(journey, temple_data)
    
    return jsonify({
        'success': True,
        'journey': journey,
        'steps': steps,
        'temple': {
            'name': temple.name,
            'location': temple.location,
            'timings': f"{temple.opening_time or '6:00 AM'} - {temple.closing_time or '8:00 PM'}"
        }
    })

@app.route('/api/real-time-guide/<int:temple_id>')
def real_time_guide_api(temple_id):
    if not journey_optimizer:
        return jsonify({'error': 'Journey optimizer not available'}), 500
    
    location = request.args.get('location', 'entrance')
    recommendations = journey_optimizer.get_real_time_recommendations(temple_id, location)
    
    return jsonify({
        'success': True,
        'location': location,
        'recommendations': recommendations
    })

@app.route('/chatbot')
def chatbot_widget():
    return render_template('chatbot_widget.html')

@app.route('/indian-guide')
def indian_guide():
    return render_template('indian_states_guide.html')

@app.route('/admin/queue-management')
@login_required
def queue_management():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temples = Temple.query.filter_by(is_active=True).all()
    return render_template('queue_management.html', temples=temples)

@app.route('/api/queue-detection', methods=['POST'])
@login_required
def queue_detection_api():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not queue_manager:
        return jsonify({'error': 'Queue manager not available'}), 500
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    temple_id = request.form.get('temple_id')
    
    if file.filename == '' or not temple_id:
        return jsonify({'error': 'File and temple selection required'}), 400
    
    filename = secure_filename(file.filename)
    filepath = os.path.join('uploads', filename)
    os.makedirs('uploads', exist_ok=True)
    
    try:
        file.save(filepath)
        temple_id = int(temple_id)
        
        # Detect people in queue zones
        zone_counts, annotated_path = queue_manager.detect_people_in_zones(filepath, temple_id)
        
        # Update queue status
        queue_status = queue_manager.update_queue_status(temple_id, zone_counts)
        
        # Update crowd data in database
        total_people = sum(zone_counts.values())
        crowd_level = 'Low' if total_people <= 20 else 'Medium' if total_people <= 50 else 'High'
        
        existing_crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
        if existing_crowd:
            existing_crowd.status = crowd_level
            existing_crowd.count = total_people
            existing_crowd.accuracy = 0.9
            existing_crowd.updated_at = datetime.now(timezone.utc)
        else:
            crowd = Crowd(
                temple_id=temple_id,
                status=crowd_level,
                count=total_people,
                accuracy=0.9,
                updated_at=datetime.now(timezone.utc)
            )
            db.session.add(crowd)
        db.session.commit()
        
        # Copy annotated image to static folder
        annotated_filename = None
        if annotated_path and os.path.exists(annotated_path):
            import shutil
            annotated_filename = f'queue_detected_{filename}'
            static_path = os.path.join('static', annotated_filename)
            os.makedirs('static', exist_ok=True)
            shutil.copy2(annotated_path, static_path)
        
        # Emit real-time update
        socketio.emit('queue_update', {
            'temple_id': temple_id,
            'zone_counts': zone_counts,
            'queue_status': queue_status,
            'total_people': total_people,
            'crowd_level': crowd_level
        })
        
        return jsonify({
            'success': True,
            'zone_counts': zone_counts,
            'queue_status': queue_status,
            'annotated_image': annotated_filename,
            'total_people': total_people,
            'crowd_level': crowd_level
        })
        
    except Exception as e:
        return jsonify({'error': f'Queue detection failed: {str(e)}'}), 500
    
    finally:
        if os.path.exists(filepath):
            os.remove(filepath)

@app.route('/api/queue-status/<int:temple_id>')
@login_required
def queue_status_api(temple_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not queue_manager:
        return jsonify({'error': 'Queue manager not available'}), 500
    
    queue_status = queue_manager.get_queue_status(temple_id)
    
    if queue_status:
        return jsonify({'success': True, 'queue_status': queue_status})
    else:
        return jsonify({'success': False, 'error': 'No queue data available'})

@app.route('/api/queue-config', methods=['POST'])
@login_required
def queue_config_api():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not queue_manager:
        return jsonify({'error': 'Queue manager not available'}), 500
    
    data = request.json
    temple_id = data.get('temple_id')
    zones = data.get('zones')
    
    if not temple_id or not zones:
        return jsonify({'error': 'Temple ID and zones required'}), 400
    
    try:
        # Convert zone format
        formatted_zones = {}
        for zone_name, coords in zones.items():
            if len(coords) == 4:
                formatted_zones[zone_name] = [coords]
        
        queue_manager.initialize_temple_queues(int(temple_id), formatted_zones)
        
        return jsonify({'success': True, 'message': 'Queue configuration saved'})
    
    except Exception as e:
        return jsonify({'error': f'Configuration failed: {str(e)}'}), 500

@app.route('/admin/queue-analytics')
@login_required
def queue_analytics():
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temples = Temple.query.filter_by(is_active=True).all()
    return render_template('queue_analytics.html', temples=temples)

@app.route('/api/queue-analytics/<int:temple_id>')
@login_required
def queue_analytics_api(temple_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not queue_manager:
        return jsonify({'error': 'Queue manager not available'}), 500
    
    try:
        queue_status = queue_manager.get_queue_status(temple_id)
        
        if not queue_status:
            return jsonify({'success': False, 'error': 'No queue data available'})
        
        # Generate analytics data
        analytics = {
            'metrics': {
                'total_people': queue_status['total_people'],
                'avg_wait_time': sum(q['wait_time'] for q in queue_status['queues'].values()) / len(queue_status['queues']),
                'bottlenecks': sum(1 for q in queue_status['queues'].values() if q['status'] == 'High'),
                'throughput': queue_status['total_people'] * 6,  # Estimated people per hour
                'efficiency': {
                    'entry': max(0, 100 - queue_status['queues']['entry']['wait_time'] * 2),
                    'darshan': max(0, 100 - queue_status['queues']['darshan']['wait_time'] * 2),
                    'prasad': max(0, 100 - queue_status['queues']['prasad']['wait_time'] * 2)
                }
            },
            'queue_data': queue_status['queues'],
            'trends': [
                {
                    'timestamp': datetime.now().isoformat(),
                    'entry': queue_status['queues']['entry']['count'],
                    'darshan': queue_status['queues']['darshan']['count'],
                    'prasad': queue_status['queues']['prasad']['count']
                }
            ],
            'recommendations': queue_manager.optimize_queue_flow(temple_id)
        }
        
        return jsonify({'success': True, 'analytics': analytics})
        
    except Exception as e:
        return jsonify({'error': f'Analytics generation failed: {str(e)}'}), 500

@app.route('/api/queue-optimization/<int:temple_id>', methods=['POST'])
@login_required
def queue_optimization_post(temple_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    if not queue_manager:
        return jsonify({'error': 'Queue manager not available'}), 500
    
    try:
        # Apply optimization logic
        queue_status = queue_manager.get_queue_status(temple_id)
        
        if not queue_status:
            return jsonify({'success': False, 'error': 'No queue data to optimize'})
        
        # Simulate optimization by reducing wait times
        optimizations_applied = []
        
        for queue_name, queue_info in queue_status['queues'].items():
            if queue_info['status'] == 'High':
                # Simulate reducing queue by 20%
                new_count = max(1, int(queue_info['count'] * 0.8))
                optimizations_applied.append(f'Reduced {queue_name} queue from {queue_info["count"]} to {new_count} people')
        
        return jsonify({
            'success': True,
            'message': 'Optimization applied successfully',
            'optimizations': optimizations_applied
        })
        
    except Exception as e:
        return jsonify({'error': f'Optimization failed: {str(e)}'}), 500

@app.route('/api/queue-report/<int:temple_id>')
@login_required
def queue_report(temple_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    
    temple = Temple.query.get_or_404(temple_id)
    
    # Generate simple HTML report
    report_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Queue Report - {temple.name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .header {{ background: #007bff; color: white; padding: 20px; text-align: center; }}
            .section {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; }}
            .metric {{ display: inline-block; margin: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Queue Management Report</h1>
            <h2>{temple.name}</h2>
            <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        <div class="section">
            <h3>Current Queue Status</h3>
            <div class="metric">
                <strong>Total People:</strong> {queue_manager.get_queue_status(temple_id)['total_people'] if queue_manager and queue_manager.get_queue_status(temple_id) else 'N/A'}
            </div>
            <div class="metric">
                <strong>Crowd Level:</strong> {queue_manager.get_queue_status(temple_id)['crowd_level'] if queue_manager and queue_manager.get_queue_status(temple_id) else 'N/A'}
            </div>
        </div>
        
        <div class="section">
            <h3>Recommendations</h3>
            <ul>
                <li>Implement digital queue management system</li>
                <li>Add more service counters during peak hours</li>
                <li>Use mobile app for queue status updates</li>
                <li>Optimize entry and exit flow patterns</li>
            </ul>
        </div>
    </body>
    </html>
    """
    
    return report_html

# Smart Queue AI Routes
@app.route('/api/smart-queue-analysis/<int:temple_id>')
@login_required
def smart_queue_analysis(temple_id):
    """Perform AI analysis on temple queues"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    try:
        from smart_queue_ai import smart_queue_ai
        
        # Get current queue status
        queue_status = queue_manager.get_queue_status(temple_id) if queue_manager else None
        
        if not queue_status:
            # Generate dummy queue status for demo
            import random
            queue_status = {
                'temple_id': temple_id,
                'total_people': random.randint(10, 80),
                'crowd_level': random.choice(['Low', 'Medium', 'High']),
                'queues': {
                    'entry': {
                        'count': random.randint(5, 25),
                        'wait_time': random.randint(2, 15),
                        'status': random.choice(['Low', 'Medium', 'High'])
                    },
                    'darshan': {
                        'count': random.randint(10, 40),
                        'wait_time': random.randint(5, 25),
                        'status': random.choice(['Low', 'Medium', 'High'])
                    },
                    'prasad': {
                        'count': random.randint(3, 15),
                        'wait_time': random.randint(1, 10),
                        'status': random.choice(['Low', 'Medium', 'High'])
                    }
                },
                'last_update': datetime.now().isoformat()
            }
        
        # Perform AI priority analysis
        priority_analysis = smart_queue_ai.analyze_queue_priority(temple_id, queue_status)
        
        # Generate alerts
        alerts = smart_queue_ai.generate_alerts(temple_id, queue_status, priority_analysis)
        
        # Get release instructions with enhanced VAC data
        release_instructions = smart_queue_ai.get_release_instructions(temple_id, priority_analysis)
        
        # Enhance instructions with strategy data
        for i, instruction in enumerate(release_instructions):
            if i < len(priority_analysis['release_recommendation']):
                instruction['strategy'] = priority_analysis['release_recommendation'][i]
        
        # Get predictions
        predictions = smart_queue_ai.predict_queue_evolution(temple_id, queue_status)
        
        # Get optimization score
        optimization_score = smart_queue_ai.get_optimization_score(temple_id, queue_status)
        
        return jsonify({
            'success': True,
            'queue_status': queue_status,
            'priority_analysis': priority_analysis,
            'alerts': alerts,
            'release_instructions': release_instructions,
            'predictions': predictions,
            'optimization_score': optimization_score
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/emergency-release/<int:temple_id>', methods=['POST'])
@login_required
def emergency_release(temple_id):
    """Execute emergency release for all queues"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'})
    
    try:
        # Simulate emergency release by updating crowd status
        existing_crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
        if existing_crowd:
            # Reduce crowd by 50%
            existing_crowd.count = max(0, existing_crowd.count // 2)
            existing_crowd.status = 'Low' if existing_crowd.count < 20 else 'Medium'
            existing_crowd.updated_at = datetime.now(timezone.utc)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Emergency release executed successfully'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/optimize-queues/<int:temple_id>', methods=['POST'])
def optimize_queues(temple_id):
    """Apply AI optimization to queues"""
    try:
        # Simulate optimization by improving crowd status
        existing_crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
        if existing_crowd:
            # Optimize crowd by 30%
            existing_crowd.count = max(0, int(existing_crowd.count * 0.7))
            existing_crowd.status = get_enhanced_crowd_status(existing_crowd.count, temple_id)
            existing_crowd.updated_at = datetime.now(timezone.utc)
            db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Auto-optimization applied successfully',
            'optimizations': ['Reduced entry queue by 30%', 'Optimized darshan flow', 'Added express prasad counter']
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/api/execute-queue-action/<int:temple_id>', methods=['POST'])
def execute_queue_action(temple_id):
    """Execute specific VAC queue action"""
    try:
        data = request.json
        queue_name = data.get('queue')
        action_type = data.get('action')
        
        # Simulate action execution
        existing_crowd = Crowd.query.filter_by(temple_id=temple_id).order_by(Crowd.updated_at.desc()).first()
        if existing_crowd:
            if action_type == 'EMERGENCY_SPLIT_QUEUE':
                existing_crowd.count = max(0, existing_crowd.count // 3)  # Split into 3 lanes
                message = f'Emergency queue split executed for {queue_name} - 3 parallel lanes activated'
            elif action_type == 'SPLIT_QUEUE_DUAL_LANE':
                existing_crowd.count = max(0, int(existing_crowd.count * 0.6))  # Dual lane processing
                message = f'Dual lane processing activated for {queue_name}'
            elif action_type == 'OPTIMIZE_FLOW':
                existing_crowd.count = max(0, int(existing_crowd.count * 0.8))  # Flow optimization
                message = f'Flow optimization applied to {queue_name}'
            else:
                message = f'Action {action_type} executed for {queue_name}'
            
            existing_crowd.status = get_enhanced_crowd_status(existing_crowd.count, temple_id)
            existing_crowd.updated_at = datetime.now(timezone.utc)
            db.session.commit()
        else:
            message = f'Action {action_type} logged for {queue_name}'
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/visitor-journey/<int:temple_id>')
def visitor_journey_page(temple_id):
    temple = Temple.query.get_or_404(temple_id)
    return render_template('visitor_journey.html', temple=temple)

@app.route('/admin/smart-queue-dashboard')
def smart_queue_dashboard():
    """Smart Queue Management Dashboard"""
    temples = Temple.query.filter_by(is_active=True).all()
    return render_template('smart_queue_dashboard.html', temples=temples)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Database migrations
        try:
            result = db.session.execute(text("SHOW COLUMNS FROM crowd LIKE 'temple_id'"))
            if not result.fetchone():
                db.session.execute(text("ALTER TABLE crowd ADD COLUMN temple_id INT"))
                db.session.execute(text("ALTER TABLE crowd ADD COLUMN accuracy FLOAT DEFAULT 0.0"))
                db.session.commit()
                print("Added temple-specific crowd columns")
            
            result = db.session.execute(text("SHOW COLUMNS FROM booking LIKE 'temple_id'"))
            if not result.fetchone():
                db.session.execute(text("ALTER TABLE booking ADD COLUMN temple_id INT"))
                db.session.execute(text("ALTER TABLE booking ADD COLUMN confirmation_id VARCHAR(20)"))
                db.session.execute(text("ALTER TABLE booking ADD COLUMN status VARCHAR(20) DEFAULT 'confirmed'"))
                db.session.commit()
                print("Added temple booking columns")
            
            result = db.session.execute(text("SHOW COLUMNS FROM temple LIKE 'image_url'"))
            if not result.fetchone():
                db.session.execute(text("ALTER TABLE temple ADD COLUMN image_url VARCHAR(500)"))
                db.session.execute(text("ALTER TABLE temple ADD COLUMN latitude FLOAT"))
                db.session.execute(text("ALTER TABLE temple ADD COLUMN longitude FLOAT"))
                db.session.execute(text("ALTER TABLE temple ADD COLUMN description TEXT"))
                db.session.commit()
                print("Added enhanced temple columns")
            
            # Add payment columns to booking table
            result = db.session.execute(text("SHOW COLUMNS FROM booking LIKE 'payment_status'"))
            if not result.fetchone():
                db.session.execute(text("ALTER TABLE booking ADD COLUMN payment_status VARCHAR(20) DEFAULT 'pending'"))
                db.session.execute(text("ALTER TABLE booking ADD COLUMN transaction_id VARCHAR(50)"))
                db.session.execute(text("ALTER TABLE booking ADD COLUMN total_amount FLOAT NOT NULL DEFAULT 0"))
                db.session.commit()
                print("Added payment columns to booking table")
            
            # Add prasad and pooja tables
            try:
                db.session.execute(text("SELECT 1 FROM prasad LIMIT 1"))
            except:
                db.session.execute(text("""
                    CREATE TABLE prasad (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        price FLOAT NOT NULL,
                        temple_id INT NOT NULL,
                        is_available BOOLEAN DEFAULT TRUE
                    )
                """))
                db.session.execute(text("""
                    CREATE TABLE pooja (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        price FLOAT NOT NULL,
                        duration INT DEFAULT 30,
                        temple_id INT NOT NULL,
                        is_available BOOLEAN DEFAULT TRUE
                    )
                """))
                db.session.execute(text("""
                    CREATE TABLE `order` (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        booking_id INT NOT NULL,
                        total_amount FLOAT NOT NULL,
                        qr_code VARCHAR(100) UNIQUE NOT NULL,
                        status VARCHAR(20) DEFAULT 'pending',
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                db.session.execute(text("""
                    CREATE TABLE order_item (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_id INT NOT NULL,
                        item_type VARCHAR(20) NOT NULL,
                        item_id INT NOT NULL,
                        quantity INT DEFAULT 1,
                        price FLOAT NOT NULL
                    )
                """))
                db.session.commit()
                print("Added prasad and pooja tables")
        except Exception as e:
            print(f"Migration handled: {e}")
        
        # Create admin user if not exists
        if not User.query.filter_by(email='admin@temple.com').first():
            admin = User(
                name='Admin',
                email='admin@temple.com',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
        
        # Create sample temples if not exists
        if not Temple.query.first():
            temples = [
                Temple(name='Somnath Temple', location='Somnath, Gujarat', latitude=20.8880, longitude=70.4017,
                      capacity=150, description='First among the twelve Jyotirlinga shrines of Shiva. Located on the western coast of Gujarat.',
                      image_url='https://media.newindianexpress.com/TNIE%2Fimport%2Fuploads%2Fuser%2Fckeditor_images%2Farticle%2F2018%2F3%2F1%2FSoulfula.jpg'),
                Temple(name='Dwarka Temple', location='Dwarka, Gujarat', latitude=22.2394, longitude=68.9678,
                      capacity=200, description='Sacred city of Lord Krishna, one of the Char Dham pilgrimage sites.',
                      image_url='https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/Dwarakadheesh_Temple%2C_2014.jpg/500px-Dwarakadheesh_Temple%2C_2014.jpg'),
                Temple(name='Ambaji Temple', location='Ambaji, Gujarat', latitude=24.2167, longitude=72.8667,
                      capacity=100, description='One of the 51 Shakti Peethas, dedicated to Goddess Amba.',
                      image_url='https://rajmandirhotel.com/wp-content/uploads/2024/02/Ambaji-Temple.webp'),
                Temple(name='Pavagadh Temple', location='Pavagadh, Gujarat', latitude=22.4833, longitude=73.5333,
                      capacity=120, description='Kalika Mata temple atop Pavagadh hill, a UNESCO World Heritage site.',
                      image_url='https://www.pavagadhtemple.in/frontend/img/newtemple.jpg')
            ]
            for temple in temples:
                db.session.add(temple)
            db.session.commit()
            
            # Add sample prasads and poojas for all temples
            prasads = [
                # Somnath Temple (ID: 1)
                Prasad(name='Laddu', price=25, temple_id=1),
                Prasad(name='Coconut', price=15, temple_id=1),
                Prasad(name='Flowers Garland', price=20, temple_id=1),
                # Dwarka Temple (ID: 2)
                Prasad(name='Modak', price=30, temple_id=2),
                Prasad(name='Tulsi Leaves', price=10, temple_id=2),
                Prasad(name='Butter', price=35, temple_id=2),
                # Ambaji Temple (ID: 3)
                Prasad(name='Chunri', price=50, temple_id=3),
                Prasad(name='Sindoor', price=25, temple_id=3),
                Prasad(name='Coconut', price=15, temple_id=3),
                # Pavagadh Temple (ID: 4)
                Prasad(name='Prasad Box', price=40, temple_id=4),
                Prasad(name='Flowers', price=20, temple_id=4),
                Prasad(name='Incense', price=15, temple_id=4)
            ]
            
            poojas = [
                # Somnath Temple (ID: 1)
                Pooja(name='Abhishek', price=101, duration=30, temple_id=1),
                Pooja(name='Aarti', price=51, duration=15, temple_id=1),
                Pooja(name='Rudrabhishek', price=251, duration=45, temple_id=1),
                # Dwarka Temple (ID: 2)
                Pooja(name='Mangal Aarti', price=75, duration=20, temple_id=2),
                Pooja(name='Bhog Offering', price=151, duration=25, temple_id=2),
                Pooja(name='Krishna Aarti', price=101, duration=30, temple_id=2),
                # Ambaji Temple (ID: 3)
                Pooja(name='Mata ki Aarti', price=101, duration=30, temple_id=3),
                Pooja(name='Durga Path', price=201, duration=45, temple_id=3),
                Pooja(name='Devi Aarti', price=75, duration=20, temple_id=3),
                # Pavagadh Temple (ID: 4)
                Pooja(name='Kalika Aarti', price=101, duration=25, temple_id=4),
                Pooja(name='Special Pooja', price=151, duration=35, temple_id=4)
            ]
            
            for prasad in prasads:
                db.session.add(prasad)
            for pooja in poojas:
                db.session.add(pooja)
            
            db.session.commit()
            print('Sample temples, prasads, and poojas created')
        else:
            # Add prasad and pooja data if not exists
            if not Prasad.query.first():
                # Get actual temple IDs
                temples = Temple.query.all()
                if len(temples) >= 4:
                    temple_ids = [t.id for t in temples[:4]]
                    
                    prasads = [
                        # First Temple
                        Prasad(name='Laddu', price=25, temple_id=temple_ids[0]),
                        Prasad(name='Coconut', price=15, temple_id=temple_ids[0]),
                        Prasad(name='Flowers Garland', price=20, temple_id=temple_ids[0]),
                        # Second Temple
                        Prasad(name='Modak', price=30, temple_id=temple_ids[1]),
                        Prasad(name='Tulsi Leaves', price=10, temple_id=temple_ids[1]),
                        Prasad(name='Butter', price=35, temple_id=temple_ids[1]),
                        # Third Temple
                        Prasad(name='Chunri', price=50, temple_id=temple_ids[2]),
                        Prasad(name='Sindoor', price=25, temple_id=temple_ids[2]),
                        Prasad(name='Coconut', price=15, temple_id=temple_ids[2]),
                        # Fourth Temple
                        Prasad(name='Prasad Box', price=40, temple_id=temple_ids[3]),
                        Prasad(name='Flowers', price=20, temple_id=temple_ids[3]),
                        Prasad(name='Incense', price=15, temple_id=temple_ids[3])
                    ]
                    
                    poojas = [
                        # First Temple
                        Pooja(name='Abhishek', price=101, duration=30, temple_id=temple_ids[0]),
                        Pooja(name='Aarti', price=51, duration=15, temple_id=temple_ids[0]),
                        Pooja(name='Rudrabhishek', price=251, duration=45, temple_id=temple_ids[0]),
                        # Second Temple
                        Pooja(name='Mangal Aarti', price=75, duration=20, temple_id=temple_ids[1]),
                        Pooja(name='Bhog Offering', price=151, duration=25, temple_id=temple_ids[1]),
                        Pooja(name='Krishna Aarti', price=101, duration=30, temple_id=temple_ids[1]),
                        # Third Temple
                        Pooja(name='Mata ki Aarti', price=101, duration=30, temple_id=temple_ids[2]),
                        Pooja(name='Durga Path', price=201, duration=45, temple_id=temple_ids[2]),
                        Pooja(name='Devi Aarti', price=75, duration=20, temple_id=temple_ids[2]),
                        # Fourth Temple
                        Pooja(name='Kalika Aarti', price=101, duration=25, temple_id=temple_ids[3]),
                        Pooja(name='Special Pooja', price=151, duration=35, temple_id=temple_ids[3])
                    ]
                    
                    for prasad in prasads:
                        db.session.add(prasad)
                    for pooja in poojas:
                        db.session.add(pooja)
                    
                    db.session.commit()
                    print('Prasad and Pooja data added')
                else:
                    print('Not enough temples found to add prasad/pooja data')
        
        os.makedirs('uploads', exist_ok=True)
    
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)