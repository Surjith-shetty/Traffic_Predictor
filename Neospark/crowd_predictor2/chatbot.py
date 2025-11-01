import re
from datetime import datetime, timedelta
import json

class TempleBookingChatbot:
    def __init__(self):
        self.conversation_state = {}
        self.temples = {
            'virupaksha': {'id': 1, 'keywords': ['virupaksha', 'hampi']},
            'murudeshwara': {'id': 2, 'keywords': ['murudeshwara', 'murdeshwar']},
            'udupi': {'id': 3, 'keywords': ['udupi', 'krishna', 'sri krishna']},
            'belur': {'id': 4, 'keywords': ['belur', 'chennakeshava', 'chennakesava']}
        }
        
        self.time_slots = [
            '06:00-08:00', '08:00-10:00', '10:00-12:00',
            '12:00-14:00', '14:00-16:00', '16:00-18:00', '18:00-20:00'
        ]

    def process_message(self, message, user_id=None):
        message = message.lower().strip()
        
        # Initialize conversation state for user
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {
                'step': 'greeting',
                'booking_data': {}
            }
        
        state = self.conversation_state[user_id]
        
        # Greeting and temple selection
        if state['step'] == 'greeting':
            if any(word in message for word in ['book', 'ticket', 'darshan', 'visit']):
                temple_id = self.extract_temple(message)
                if temple_id:
                    state['booking_data']['temple_id'] = temple_id
                    temple = Temple.query.get(temple_id)
                    state['step'] = 'date'
                    return f"Great! I'll help you book darshan at {temple.name}. 📅 What date would you like to visit? (Please provide in DD/MM/YYYY format or say 'tomorrow', 'next week', etc.)"
                else:
                    return "I can help you book temple darshan! 🏛️ Which temple would you like to visit?\n\n🕉️ Available temples:\n• Virupaksha Temple, Hampi\n• Murudeshwara Temple\n• Sri Krishna Temple, Udupi\n• Chennakeshava Temple, Belur"
            else:
                return "🙏 Namaste! I'm your Divine Darshan assistant. I can help you book temple visits quickly. Just say 'book ticket to [temple name]' to get started!"
        
        # Date selection
        elif state['step'] == 'date':
            date = self.extract_date(message)
            if date:
                state['booking_data']['date'] = date
                state['step'] = 'time'
                return f"Perfect! Date selected: {date} 📅\n\n⏰ Please choose your preferred time slot:\n1. 6:00 AM - 8:00 AM\n2. 8:00 AM - 10:00 AM\n3. 10:00 AM - 12:00 PM\n4. 12:00 PM - 2:00 PM\n5. 2:00 PM - 4:00 PM\n6. 4:00 PM - 6:00 PM\n7. 6:00 PM - 8:00 PM\n\nType the number (1-7) or enter custom time (e.g., 09:30-11:30)."
            else:
                return "Please provide a valid date. You can say:\n• Tomorrow\n• Next Sunday\n• 25/12/2024\n• December 25th"
        
        # Time selection
        elif state['step'] == 'time':
            time_slot = self.extract_time(message)
            if time_slot:
                state['booking_data']['time_slot'] = time_slot
                state['step'] = 'persons'
                return f"Time: {time_slot}. How many people?"
            else:
                return "Please select a valid time slot (1-7) or enter custom time format like '09:30-11:30'"
        
        # Number of persons
        elif state['step'] == 'persons':
            persons = self.extract_number(message)
            if persons and 1 <= persons <= 10:
                state['booking_data']['persons'] = persons
                state['step'] = 'extras'
                temple = Temple.query.get(state['booking_data']['temple_id'])
                prasads = Prasad.query.filter_by(temple_id=temple.id, is_available=True).all()
                poojas = Pooja.query.filter_by(temple_id=temple.id, is_available=True).all()
                
                extras_text = f"Number of people: {persons} 👥\n\n🛍️ Would you like to add any extras?\n\n"
                
                if prasads:
                    extras_text += "📦 Available Prasad:\n"
                    for p in prasads:
                        extras_text += f"• {p.name} - ₹{p.price}\n"
                
                if poojas:
                    extras_text += "\n🕯️ Available Poojas:\n"
                    for p in poojas:
                        extras_text += f"• {p.name} - ₹{p.price} ({p.duration} mins)\n"
                
                extras_text += "\nSay 'add [item name]' to include items, or 'no extras' to proceed with darshan only."
                return extras_text
            else:
                return "Please enter a valid number of people (1-10)."
        
        # Extras selection
        elif state['step'] == 'extras':
            if 'no' in message or 'skip' in message or 'proceed' in message:
                state['step'] = 'confirm'
                return self.generate_booking_summary(state['booking_data'])
            else:
                # Handle prasad/pooja selection
                added_items = self.extract_extras(message, state['booking_data']['temple_id'])
                if added_items:
                    if 'prasads' not in state['booking_data']:
                        state['booking_data']['prasads'] = []
                    if 'poojas' not in state['booking_data']:
                        state['booking_data']['poojas'] = []
                    
                    state['booking_data']['prasads'].extend(added_items.get('prasads', []))
                    state['booking_data']['poojas'].extend(added_items.get('poojas', []))
                    
                    return f"Added items successfully! ✅\n\nSay 'add more items' to continue or 'proceed to booking' to confirm."
                else:
                    return "I couldn't find that item. Please check the available items above or say 'no extras' to proceed."
        
        # Confirmation
        elif state['step'] == 'confirm':
            if any(word in message for word in ['yes', 'confirm', 'book', 'proceed']):
                booking_result = self.create_booking(state['booking_data'], user_id)
                if booking_result['success']:
                    # Reset conversation
                    self.conversation_state[user_id] = {'step': 'greeting', 'booking_data': {}}
                    return f"🎉 Booking confirmed!\n\nBooking ID: {booking_result['booking_id']}\nTotal Amount: ₹{booking_result['total_amount']}\n\n💳 Please proceed to payment: /payment/{booking_result['booking_id']}\n\nThank you for choosing Divine Darshan! 🙏"
                else:
                    return f"❌ Booking failed: {booking_result['error']}\n\nPlease try again or contact support."
            elif any(word in message for word in ['no', 'cancel', 'change']):
                self.conversation_state[user_id] = {'step': 'greeting', 'booking_data': {}}
                return "Booking cancelled. Feel free to start a new booking anytime! 🙏"
            else:
                return "Please confirm by saying 'yes' to proceed with booking or 'no' to cancel."
        
        return "I didn't understand that. Please try again or say 'help' for assistance."

    def extract_temple(self, message):
        for temple_name, temple_data in self.temples.items():
            for keyword in temple_data['keywords']:
                if keyword in message:
                    return temple_data['id']
        return None

    def extract_date(self, message):
        # Handle relative dates
        if 'tomorrow' in message:
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        elif 'today' in message:
            return datetime.now().strftime('%Y-%m-%d')
        elif 'next week' in message:
            return (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Handle DD/MM/YYYY format
        date_pattern = r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})'
        match = re.search(date_pattern, message)
        if match:
            day, month, year = match.groups()
            try:
                date_obj = datetime(int(year), int(month), int(day))
                return date_obj.strftime('%Y-%m-%d')
            except:
                return None
        
        return None

    def extract_time(self, message):
        # Handle numbered options
        numbers = re.findall(r'\b(\d)\b', message)
        if numbers:
            slot_num = int(numbers[0])
            if 1 <= slot_num <= 7:
                return self.time_slots[slot_num - 1]
        
        # Handle custom time format (HH:MM-HH:MM)
        time_pattern = r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})'
        time_match = re.search(time_pattern, message)
        if time_match:
            start_time = time_match.group(1)
            end_time = time_match.group(2)
            # Validate time format
            try:
                start_hour, start_min = map(int, start_time.split(':'))
                end_hour, end_min = map(int, end_time.split(':'))
                if (0 <= start_hour <= 23 and 0 <= start_min <= 59 and 
                    0 <= end_hour <= 23 and 0 <= end_min <= 59 and
                    (start_hour < end_hour or (start_hour == end_hour and start_min < end_min))):
                    return f"{start_time}-{end_time}"
            except:
                pass
        
        # Handle time periods
        if 'morning' in message:
            return '06:00-08:00'
        elif 'afternoon' in message:
            return '12:00-14:00'
        elif 'evening' in message:
            return '18:00-20:00'
        
        # Handle predefined time ranges
        for slot in self.time_slots:
            if any(time in message for time in slot.split('-')):
                return slot
        
        return None

    def extract_number(self, message):
        numbers = re.findall(r'\b(\d+)\b', message)
        return int(numbers[0]) if numbers else None

    def extract_extras(self, message, temple_id):
        prasads = Prasad.query.filter_by(temple_id=temple_id, is_available=True).all()
        poojas = Pooja.query.filter_by(temple_id=temple_id, is_available=True).all()
        
        result = {'prasads': [], 'poojas': []}
        
        for prasad in prasads:
            if prasad.name.lower() in message:
                result['prasads'].append({'id': prasad.id, 'quantity': 1})
        
        for pooja in poojas:
            if pooja.name.lower() in message:
                result['poojas'].append({'id': pooja.id})
        
        return result if result['prasads'] or result['poojas'] else None

    def generate_booking_summary(self, booking_data):
        temple = Temple.query.get(booking_data['temple_id'])
        total_amount = booking_data['persons'] * 50
        
        summary = f"📋 Booking Summary:\n\n"
        summary += f"🏛️ Temple: {temple.name}\n"
        summary += f"📅 Date: {booking_data['date']}\n"
        summary += f"⏰ Time: {booking_data['time_slot']}\n"
        summary += f"👥 People: {booking_data['persons']}\n"
        summary += f"💰 Darshan Fee: ₹{booking_data['persons'] * 50}\n"
        
        if booking_data.get('prasads'):
            summary += "\n📦 Prasad Items:\n"
            for prasad_data in booking_data['prasads']:
                prasad = Prasad.query.get(prasad_data['id'])
                total_amount += prasad.price * prasad_data['quantity']
                summary += f"• {prasad.name} x{prasad_data['quantity']} - ₹{prasad.price * prasad_data['quantity']}\n"
        
        if booking_data.get('poojas'):
            summary += "\n🕯️ Pooja Services:\n"
            for pooja_data in booking_data['poojas']:
                pooja = Pooja.query.get(pooja_data['id'])
                total_amount += pooja.price
                summary += f"• {pooja.name} - ₹{pooja.price}\n"
        
        summary += f"\n💳 Total Amount: ₹{total_amount}\n\n"
        summary += "Confirm booking? (Yes/No)"
        
        return summary

    def create_booking(self, booking_data, user_id):
        try:
            # Import here to avoid circular imports
            from app import Temple, Booking, User, Prasad, Pooja, Order, OrderItem, db, generate_confirmation_id, generate_qr_code
            
            confirmation_id = generate_confirmation_id()
            darshan_fee = booking_data['persons'] * 50
            services_amount = 0
            
            # Calculate services amount
            if booking_data.get('prasads'):
                for prasad_data in booking_data['prasads']:
                    prasad = Prasad.query.get(prasad_data['id'])
                    services_amount += prasad.price * prasad_data['quantity']
            
            if booking_data.get('poojas'):
                for pooja_data in booking_data['poojas']:
                    pooja = Pooja.query.get(pooja_data['id'])
                    services_amount += pooja.price
            
            total_amount = darshan_fee + services_amount
            
            # Create booking
            booking = Booking(
                user_id=user_id,
                temple_id=booking_data['temple_id'],
                date=datetime.strptime(booking_data['date'], '%Y-%m-%d').date(),
                time_slot=booking_data['time_slot'],
                persons=booking_data['persons'],
                confirmation_id=confirmation_id,
                total_amount=total_amount,
                status='pending',
                payment_status='pending'
            )
            db.session.add(booking)
            db.session.flush()
            
            # Create order with QR code
            qr_code = generate_qr_code()
            order = Order(
                booking_id=booking.id,
                total_amount=services_amount,
                qr_code=qr_code
            )
            db.session.add(order)
            db.session.flush()
            
            # Add order items
            if booking_data.get('prasads'):
                for prasad_data in booking_data['prasads']:
                    prasad = Prasad.query.get(prasad_data['id'])
                    order_item = OrderItem(
                        order_id=order.id,
                        item_type='prasad',
                        item_id=prasad.id,
                        quantity=prasad_data['quantity'],
                        price=prasad.price * prasad_data['quantity']
                    )
                    db.session.add(order_item)
            
            if booking_data.get('poojas'):
                for pooja_data in booking_data['poojas']:
                    pooja = Pooja.query.get(pooja_data['id'])
                    order_item = OrderItem(
                        order_id=order.id,
                        item_type='pooja',
                        item_id=pooja.id,
                        quantity=1,
                        price=pooja.price
                    )
                    db.session.add(order_item)
            
            db.session.commit()
            
            return {
                'success': True,
                'booking_id': booking.id,
                'total_amount': total_amount,
                'qr_code': qr_code
            }
            
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'error': str(e)
            }

# Global chatbot instance
temple_chatbot = TempleBookingChatbot()