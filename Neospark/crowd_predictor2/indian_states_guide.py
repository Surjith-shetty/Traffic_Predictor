import re
from datetime import datetime, timedelta
import json

class IndianStatesGuide:
    def __init__(self):
        self.conversation_state = {}
        self.temples = {
            'Tirupati Balaji': {'location': 'Andhra Pradesh', 'deity': 'Lord Venkateswara'},
            'Meenakshi Temple': {'location': 'Tamil Nadu', 'deity': 'Goddess Meenakshi'},
            'Siddhivinayak': {'location': 'Maharashtra', 'deity': 'Lord Ganesha'},
            'Shirdi Sai Baba': {'location': 'Maharashtra', 'deity': 'Sai Baba'},
            'Somnath': {'location': 'Gujarat', 'deity': 'Lord Shiva'},
            'Golden Temple': {'location': 'Punjab', 'deity': 'Guru Granth Sahib'},
            'Kashi Vishwanath': {'location': 'Uttar Pradesh', 'deity': 'Lord Shiva'},
            'Jagannath Puri': {'location': 'Odisha', 'deity': 'Lord Jagannath'}
        }
        
        self.temple_navigation = {
            'Tirupati Balaji': {
                'entry': 'Enter Gate 1 → Remove shoes at counter → Security check',
                'hand_leg_wash': 'Go left from Gate 1 → Wash hands and feet at designated area',
                'darshan_queue': 'Move right then left → Join darshan queue → Follow serpentine path',
                'main_darshan': 'Enter sanctum → Bow to Lord Balaji → Move quickly (30 seconds)',
                'prasadam': 'Go back from darshan hall → Turn right → Prasadam counter',
                'exit': 'Exit through Gate 2 → Collect shoes → Main exit'
            },
            'Meenakshi Temple': {
                'entry': 'East Gate entry → Remove shoes → Security check',
                'hand_leg_wash': 'Left side washing area → Clean hands and feet',
                'darshan_queue': 'Right corridor → Meenakshi shrine first → Then Sundareswarar',
                'main_darshan': 'Clockwise pradakshina → Both shrines → Offer prayers',
                'prasadam': 'Back to main hall → Prasadam distribution center',
                'exit': 'Same East Gate → Collect footwear → Exit'
            },
            'Siddhivinayak': {
                'entry': 'Main gate → Security check → Remove shoes',
                'hand_leg_wash': 'Right side washing area → Clean hands and feet', 
                'darshan_queue': 'Climb stairs → Join queue → Follow rope barriers',
                'main_darshan': 'Enter temple → Bow to Ganesha → Offer prayers',
                'prasadam': 'Downstairs → Prasadam distribution → Modak specialty',
                'exit': 'Main stairs down → Collect footwear → Exit gate'
            },
            'Shirdi Sai Baba': {
                'entry': 'Queue complex entry → Security → Remove footwear',
                'hand_leg_wash': 'Left side → Wash hands and feet at taps',
                'darshan_queue': 'Follow queue barriers → Multiple lines merge → Be patient',
                'main_darshan': 'Enter sanctum → Bow to Sai Baba → Quick darshan',
                'prasadam': 'Exit darshan → Right turn → Prasadam counter',
                'exit': 'Main exit → Collect shoes → Outside complex'
            },
            'Somnath': {
                'entry': 'Main entrance → Security check → Remove footwear',
                'hand_leg_wash': 'Right side washing area → Clean hands and feet',
                'darshan_queue': 'Enter main hall → Join queue lines → Follow crowd',
                'main_darshan': 'Enter sanctum → Bow to Shiva Linga → Offer prayers',
                'prasadam': 'Exit sanctum → Left turn → Prasadam counter',
                'exit': 'Main hall → Collect shoes → Exit gate'
            }
        }

    def process_message(self, message, user_id=None):
        message = message.lower().strip()
        
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {
                'step': 'temple_selection',
                'selected_temple': None
            }
        
        state = self.conversation_state[user_id]
        
        if state['step'] == 'temple_selection':
            temple_name = self.extract_temple(message)
            if temple_name:
                state['selected_temple'] = temple_name
                state['step'] = 'guide_type'
                return self.get_guide_type_selection(temple_name)
            else:
                return self.get_temple_selection()
        
        elif state['step'] == 'guide_type':
            guide_type = self.extract_guide_type(message)
            if guide_type:
                temple_name = state['selected_temple']
                if guide_type == 'navigation':
                    return self.get_detailed_navigation(temple_name)
                elif guide_type == 'complete':
                    return self.get_complete_temple_guide(temple_name)
                elif guide_type == 'cultural':
                    return self.get_cultural_guide(temple_name)
                elif guide_type == 'booking':
                    return self.get_booking_assistance(temple_name)
            else:
                return "Please choose: 1. Step-by-step Navigation 2. Complete Guide 3. Cultural Info 4. Booking Help"
        
        return "I can help with temple navigation. Which temple would you like guidance for?"

    def get_temple_selection(self):
        response = "🏛️ **Temple Navigation Guide**\n\n"
        response += "Select a temple for detailed step-by-step navigation:\n\n"
        for i, (temple, info) in enumerate(self.temples.items(), 1):
            response += f"{i}. **{temple}** - {info['location']}\n"
        response += "\nType temple name or number for detailed directions!"
        return response

    def extract_temple(self, message):
        temple_numbers = {
            '1': 'Tirupati Balaji', '2': 'Meenakshi Temple', '3': 'Siddhivinayak', '4': 'Shirdi Sai Baba',
            '5': 'Somnath', '6': 'Golden Temple', '7': 'Kashi Vishwanath', '8': 'Jagannath Puri'
        }
        
        for num, temple in temple_numbers.items():
            if num in message:
                return temple
        
        for temple_name in self.temples.keys():
            if temple_name.lower() in message or any(word in message for word in temple_name.lower().split()):
                return temple_name
        return None





    def get_guide_type_selection(self, temple_name):
        response = f"🕉️ **{temple_name}** Selected!\n\n"
        response += "What type of guidance do you need?\n\n"
        response += "1️⃣ **Step-by-step Navigation** - Detailed directions inside temple\n"
        response += "2️⃣ **Complete Guide** - Everything about the temple\n"
        response += "3️⃣ **Cultural Information** - Traditions and customs\n"
        response += "4️⃣ **Booking Help** - How to book your visit\n\n"
        response += "Type number or name!"
        return response

    def extract_guide_type(self, message):
        if '1' in message or 'navigation' in message or 'direction' in message or 'step' in message:
            return 'navigation'
        elif '2' in message or 'complete' in message or 'everything' in message:
            return 'complete'
        elif '3' in message or 'cultural' in message or 'tradition' in message:
            return 'cultural'
        elif '4' in message or 'book' in message or 'booking' in message:
            return 'booking'
        return None

    def get_detailed_navigation(self, temple_name):
        if temple_name not in self.temple_navigation:
            return f"Navigation details for {temple_name} will be added soon. Please try another temple!"
        
        nav = self.temple_navigation[temple_name]
        
        response = f"🗺️ **Step-by-Step Navigation: {temple_name}**\n\n"
        
        response += "**STEP 1: ENTRY**\n"
        response += f"📍 {nav['entry']}\n\n"
        
        response += "**STEP 2: HAND & FEET WASHING**\n"
        response += f"🚿 {nav['hand_leg_wash']}\n\n"
        
        response += "**STEP 3: DARSHAN QUEUE**\n"
        response += f"👥 {nav['darshan_queue']}\n\n"
        
        response += "**STEP 4: MAIN DARSHAN**\n"
        response += f"🙏 {nav['main_darshan']}\n\n"
        
        response += "**STEP 5: PRASADAM COLLECTION**\n"
        response += f"🍯 {nav['prasadam']}\n\n"
        
        response += "**STEP 6: EXIT**\n"
        response += f"🚪 {nav['exit']}\n\n"
        
        response += "💡 **Tips:**\n"
        response += "• Follow these steps in order\n"
        response += "• Ask temple staff if confused\n"
        response += "• Keep your belongings secure\n"
        response += "• Maintain queue discipline\n\n"
        
        response += "Need booking help or more information?"
        
        return response

    def get_complete_temple_guide(self, temple_name):
        temple_info = self.temples.get(temple_name, {})
        response = f"📖 **Complete Guide: {temple_name}**\n\n"
        
        response += f"📍 **Location:** {temple_info.get('location', 'India')}\n"
        response += f"🙏 **Deity:** {temple_info.get('deity', 'Divine')}\n"
        response += f"⏰ **Temple Hours:** 6:00 AM - 8:00 PM\n"
        response += f"💰 **Entry Fee:** ₹50 per person\n"
        response += f"🕐 **Visit Duration:** 2-3 hours\n\n"
        
        response += "**🗺️ Navigation Summary:**\n"
        if temple_name in self.temple_navigation:
            nav = self.temple_navigation[temple_name]
            response += f"1. {nav['entry']}\n"
            response += f"2. {nav['hand_leg_wash']}\n"
            response += f"3. {nav['darshan_queue']}\n"
            response += f"4. {nav['main_darshan']}\n"
            response += f"5. {nav['prasadam']}\n"
            response += f"6. {nav['exit']}\n\n"
        
        response += "**📋 What to Bring:**\n"
        response += "• Valid ID for entry\n"
        response += "• Comfortable shoes (easy to remove)\n"
        response += "• Modest clothing\n"
        response += "• Water bottle\n"
        response += "• Cash for prasadam\n\n"
        
        response += "**🙏 Temple Etiquette:**\n"
        response += "• Remove shoes before entering\n"
        response += "• Maintain silence in prayer areas\n"
        response += "• Follow photography rules\n"
        response += "• Respect queue discipline\n\n"
        
        response += "Need step-by-step navigation or booking help?"
        
        return response

    def get_cultural_guide(self, temple_name):
        response = f"🕉️ **Cultural Guide: {temple_name}**\n\n"
        
        response += "**🙏 Temple Etiquette:**\n"
        response += "• Remove shoes before entering temple premises\n"
        response += "• Dress modestly - cover shoulders and legs\n"
        response += "• Maintain silence in prayer areas\n"
        response += "• Don't point feet toward deity\n"
        response += "• Join palms and bow when entering sanctum\n\n"
        
        response += "**🎭 Rituals You'll Witness:**\n"
        response += "• Aarti (prayer with lamps) - morning and evening\n"
        response += "• Devotees offering flowers, coconuts, sweets\n"
        response += "• Chanting of mantras and bhajans\n"
        response += "• Circumambulation (walking around deity)\n\n"
        
        response += "**🎁 Offerings & Prasad:**\n"
        response += "• Prasad: Blessed food distributed to devotees\n"
        response += "• Common offerings: Flowers, fruits, sweets, coconut\n"
        response += "• Receive prasad with both hands\n"
        response += "• Consider it sacred - consume respectfully\n\n"
        
        response += "**📸 Photography Guidelines:**\n"
        response += "• Photography may be restricted in sanctum\n"
        response += "• Ask permission before photographing people\n"
        response += "• Respect 'no photography' signs\n"
        response += "• Flash photography usually not allowed\n\n"
        
        response += "Need detailed navigation directions?"
        
        return response

    def get_booking_assistance(self, temple_name):
        response = f"🎫 **Booking Your Visit to {temple_name}**\n\n"
        
        response += "**📋 Booking Process:**\n"
        response += "1. Visit our booking page\n"
        response += "2. Select your preferred date\n"
        response += "3. Choose time slot (7 options available)\n"
        response += "4. Enter number of visitors\n"
        response += "5. Add prasad or pooja services (optional)\n"
        response += "6. Complete secure payment\n"
        response += "7. Receive QR code via email\n\n"
        
        response += "**💡 Booking Tips:**\n"
        response += "• Book 2-3 days in advance\n"
        response += "• Morning slots (6-9 AM) are less crowded\n"
        response += "• Green calendar days = low crowd\n"
        response += "• Pre-book prasad to skip queues\n\n"
        
        response += "**💳 Payment & Entry:**\n"
        response += "• Cards and UPI accepted\n"
        response += "• Instant email confirmation with QR code\n"
        response += "• Show QR code at temple for entry\n"
        response += "• Follow the navigation steps I provided\n\n"
        
        response += "Ready to book? I can guide you through the temple navigation!"
        
        return response

# Global Indian states guide instance
indian_states_guide = IndianStatesGuide()