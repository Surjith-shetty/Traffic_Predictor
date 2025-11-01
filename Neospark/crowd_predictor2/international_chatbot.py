import re
from datetime import datetime, timedelta
import json

class InternationalTravelerChatbot:
    def __init__(self):
        self.conversation_state = {}
        self.temples_data = {
            1: {
                'name': 'Somnath Temple',
                'location': 'Somnath, Gujarat',
                'keywords': ['somnath', 'gujarat'],
                'significance': 'First of the 12 Jyotirlinga shrines of Lord Shiva',
                'best_time': 'October to March',
                'dress_code': 'Traditional Indian attire preferred',
                'cultural_info': 'Remove shoes before entering, photography restricted in sanctum'
            },
            2: {
                'name': 'Dwarka Temple',
                'location': 'Dwarka, Gujarat', 
                'keywords': ['dwarka', 'krishna'],
                'significance': 'Sacred city of Lord Krishna, one of Char Dham',
                'best_time': 'October to March',
                'dress_code': 'Modest clothing, cover shoulders and legs',
                'cultural_info': 'Ancient city with rich mythology, evening aarti is spectacular'
            },
            3: {
                'name': 'Ambaji Temple',
                'location': 'Ambaji, Gujarat',
                'keywords': ['ambaji', 'amba', 'goddess'],
                'significance': 'One of 51 Shakti Peethas dedicated to Goddess Amba',
                'best_time': 'October to March',
                'dress_code': 'Traditional attire recommended',
                'cultural_info': 'Hilltop temple, carry water, respect local customs'
            },
            4: {
                'name': 'Pavagadh Temple',
                'location': 'Pavagadh, Gujarat',
                'keywords': ['pavagadh', 'kalika'],
                'significance': 'Kalika Mata temple, UNESCO World Heritage site',
                'best_time': 'October to March',
                'dress_code': 'Comfortable clothing for hill climbing',
                'cultural_info': 'Ropeway available, ancient fort complex'
            }
        }
        
        self.countries_info = {
            'usa': {'currency': 'USD', 'visa': 'Tourist Visa required', 'time_diff': '-10.5 to -13.5 hours'},
            'uk': {'currency': 'GBP', 'visa': 'Tourist Visa required', 'time_diff': '-4.5 hours'},
            'canada': {'currency': 'CAD', 'visa': 'Tourist Visa required', 'time_diff': '-9.5 to -12.5 hours'},
            'australia': {'currency': 'AUD', 'visa': 'Tourist Visa required', 'time_diff': '+4.5 to +8.5 hours'},
            'germany': {'currency': 'EUR', 'visa': 'Tourist Visa required', 'time_diff': '-3.5 hours'},
            'japan': {'currency': 'JPY', 'visa': 'Tourist Visa required', 'time_diff': '+3.5 hours'},
            'singapore': {'currency': 'SGD', 'visa': 'Visa on arrival', 'time_diff': '+2.5 hours'}
        }

    def process_message(self, message, user_id=None):
        message = message.lower().strip()
        
        if user_id not in self.conversation_state:
            self.conversation_state[user_id] = {
                'step': 'greeting',
                'user_info': {},
                'selected_temple': None
            }
        
        state = self.conversation_state[user_id]
        
        # Greeting and country identification
        if state['step'] == 'greeting':
            if any(word in message for word in ['hello', 'hi', 'help', 'guide', 'temple', 'visit']):
                return self.get_country_selection()
            else:
                return "🙏 Namaste! Welcome to India's Divine Temple Guide! I'm here to help international travelers explore our sacred temples. Where are you visiting from?"
        
        # Country selection
        elif state['step'] == 'country':
            country = self.extract_country(message)
            if country:
                state['user_info']['country'] = country
                state['step'] = 'temple_selection'
                return self.get_temple_selection_with_country_info(country)
            else:
                return "I'd love to help you! Which country are you visiting from? (e.g., USA, UK, Canada, Australia, Germany, Japan, Singapore, etc.)"
        
        # Temple selection
        elif state['step'] == 'temple_selection':
            temple_id = self.extract_temple(message)
            if temple_id:
                state['selected_temple'] = temple_id
                state['step'] = 'guide_type'
                return self.get_guide_type_selection(temple_id)
            else:
                return "Please select a temple by typing its name or number (1-4), or ask about a specific temple like 'Tell me about Somnath Temple'"
        
        # Guide type selection
        elif state['step'] == 'guide_type':
            guide_type = self.extract_guide_type(message)
            if guide_type:
                temple_id = state['selected_temple']
                if guide_type == 'complete':
                    return self.get_complete_temple_guide(temple_id, state['user_info']['country'])
                elif guide_type == 'cultural':
                    return self.get_cultural_guide(temple_id)
                elif guide_type == 'practical':
                    return self.get_practical_guide(temple_id, state['user_info']['country'])
                elif guide_type == 'booking':
                    state['step'] = 'booking_help'
                    return self.get_booking_assistance(temple_id)
            else:
                return "Please choose what type of guidance you need:\\n1. Complete Guide\\n2. Cultural Information\\n3. Practical Tips\\n4. Booking Help\\n\\nType the number or name of your choice."
        
        # Booking assistance
        elif state['step'] == 'booking_help':
            if any(word in message for word in ['yes', 'book', 'proceed', 'help']):
                temple_id = state['selected_temple']
                temple = self.temples_data[temple_id]
                return f"🎫 To book your visit to {temple['name']}:\\n\\n1. Visit our booking page: /temple/{temple_id}\\n2. Select your preferred date and time\\n3. Choose number of visitors\\n4. Add prasad or pooja services if desired\\n5. Complete payment\\n\\n💡 Tip: Book 2-3 days in advance for better slot availability!\\n\\nWould you like me to guide you through another temple or provide more information?"
            else:
                return "No problem! Is there anything else about the temple you'd like to know? Or would you like to explore another temple?"
        
        # Handle follow-up questions
        if any(word in message for word in ['another', 'different', 'other', 'more']):
            state['step'] = 'temple_selection'
            return "🏛️ Which other temple would you like to explore?\\n\\n" + self.get_temple_list()
        
        if any(word in message for word in ['start', 'begin', 'new', 'restart']):
            state['step'] = 'greeting'
            return self.get_country_selection()
        
        return "I'm here to help! You can:\\n• Ask about another temple\\n• Get booking help\\n• Learn about cultural practices\\n• Start over\\n\\nWhat would you like to do?"

    def get_country_selection(self):
        self.conversation_state[list(self.conversation_state.keys())[-1]]['step'] = 'country'
        return "🌍 Welcome to India's Sacred Temple Guide!\\n\\nI'll provide personalized guidance based on your country. Which country are you visiting from?\\n\\n🇺🇸 USA  🇬🇧 UK  🇨🇦 Canada  🇦🇺 Australia\\n🇩🇪 Germany  🇯🇵 Japan  🇸🇬 Singapore\\n\\nOr just type your country name!"

    def extract_country(self, message):
        country_keywords = {
            'usa': ['usa', 'america', 'united states', 'us'],
            'uk': ['uk', 'britain', 'england', 'united kingdom'],
            'canada': ['canada', 'canadian'],
            'australia': ['australia', 'australian', 'aussie'],
            'germany': ['germany', 'german', 'deutschland'],
            'japan': ['japan', 'japanese', 'nippon'],
            'singapore': ['singapore', 'singaporean']
        }
        
        for country, keywords in country_keywords.items():
            if any(keyword in message for keyword in keywords):
                return country
        return None

    def get_temple_selection_with_country_info(self, country):
        country_info = self.countries_info.get(country, {})
        
        response = f"🎌 Great! Guidance for visitors from {country.upper()}:\\n\\n"
        
        if country_info:
            response += f"💱 Currency: {country_info.get('currency', 'N/A')} → INR (Indian Rupee)\\n"
            response += f"📋 Visa: {country_info.get('visa', 'Check requirements')}\\n"
            response += f"🕐 Time Difference: {country_info.get('time_diff', 'Check local time')}\\n\\n"
        
        response += "🏛️ **Sacred Temples to Explore:**\\n\\n"
        response += "1️⃣ **Somnath Temple** - First Jyotirlinga, Gujarat coast\\n"
        response += "2️⃣ **Dwarka Temple** - Lord Krishna's sacred city\\n"
        response += "3️⃣ **Ambaji Temple** - Powerful Goddess shrine\\n"
        response += "4️⃣ **Pavagadh Temple** - UNESCO heritage hilltop temple\\n\\n"
        response += "Which temple interests you? Type the number or temple name!"
        
        return response

    def extract_temple(self, message):
        # Check for numbers
        if '1' in message or 'somnath' in message:
            return 1
        elif '2' in message or 'dwarka' in message or 'krishna' in message:
            return 2
        elif '3' in message or 'ambaji' in message or 'amba' in message:
            return 3
        elif '4' in message or 'pavagadh' in message or 'kalika' in message:
            return 4
        
        # Check keywords
        for temple_id, temple_data in self.temples_data.items():
            if any(keyword in message for keyword in temple_data['keywords']):
                return temple_id
        return None

    def get_guide_type_selection(self, temple_id):
        temple = self.temples_data[temple_id]
        
        response = f"🕉️ **{temple['name']}** Selected!\\n\\n"
        response += f"📍 Location: {temple['location']}\\n"
        response += f"✨ Significance: {temple['significance']}\\n\\n"
        response += "What type of guidance do you need?\\n\\n"
        response += "1️⃣ **Complete Guide** - Everything you need to know\\n"
        response += "2️⃣ **Cultural Information** - Traditions, customs, etiquette\\n"
        response += "3️⃣ **Practical Tips** - Travel, timing, what to bring\\n"
        response += "4️⃣ **Booking Help** - How to book your visit\\n\\n"
        response += "Type the number or name of your choice!"
        
        return response

    def extract_guide_type(self, message):
        if '1' in message or 'complete' in message or 'everything' in message:
            return 'complete'
        elif '2' in message or 'cultural' in message or 'tradition' in message or 'custom' in message:
            return 'cultural'
        elif '3' in message or 'practical' in message or 'tip' in message or 'travel' in message:
            return 'practical'
        elif '4' in message or 'book' in message or 'booking' in message:
            return 'booking'
        return None

    def get_complete_temple_guide(self, temple_id, country):
        temple = self.temples_data[temple_id]
        
        guide = f"📖 **Complete Guide: {temple['name']}**\\n\\n"
        
        # Temple Overview
        guide += f"🏛️ **Temple Overview:**\\n"
        guide += f"• Location: {temple['location']}\\n"
        guide += f"• Significance: {temple['significance']}\\n"
        guide += f"• Best Time to Visit: {temple['best_time']}\\n\\n"
        
        # Cultural Guidelines
        guide += f"🙏 **Cultural Guidelines:**\\n"
        guide += f"• Dress Code: {temple['dress_code']}\\n"
        guide += f"• Cultural Notes: {temple['cultural_info']}\\n"
        guide += f"• Remove shoes before entering\\n"
        guide += f"• Maintain silence in prayer areas\\n"
        guide += f"• Photography may be restricted\\n\\n"
        
        # Practical Information
        guide += f"⏰ **Timing & Practical Info:**\\n"
        guide += f"• Temple Hours: 6:00 AM - 8:00 PM (typical)\\n"
        guide += f"• Best Visit Time: Early morning (6-9 AM) or evening (6-8 PM)\\n"
        guide += f"• Duration: 2-3 hours for complete experience\\n"
        guide += f"• Entry Fee: ₹50 per person for darshan\\n\\n"
        
        # What to Expect
        guide += f"🎯 **What to Expect:**\\n"
        guide += f"• Security check at entrance\\n"
        guide += f"• Queue for main darshan (15-45 minutes)\\n"
        guide += f"• Prasad (blessed food) available for purchase\\n"
        guide += f"• Special pooja ceremonies available\\n\\n"
        
        # International Visitor Tips
        guide += f"🌍 **Tips for {country.upper()} Visitors:**\\n"
        guide += f"• Carry valid passport/ID\\n"
        guide += f"• Indian Rupees needed (cards accepted for booking)\\n"
        guide += f"• Respect local customs and traditions\\n"
        guide += f"• Learn basic Hindi greetings: 'Namaste' (hello/goodbye)\\n\\n"
        
        guide += f"Would you like specific help with booking or have other questions?"
        
        return guide

    def get_cultural_guide(self, temple_id):
        temple = self.temples_data[temple_id]
        
        guide = f"🕉️ **Cultural Guide: {temple['name']}**\\n\\n"
        
        guide += f"📿 **Religious Significance:**\\n"
        guide += f"• {temple['significance']}\\n"
        guide += f"• Sacred to millions of Hindu devotees worldwide\\n"
        guide += f"• Center of spiritual energy and devotion\\n\\n"
        
        guide += f"🙏 **Temple Etiquette:**\\n"
        guide += f"• Remove shoes before entering temple premises\\n"
        guide += f"• Dress modestly - {temple['dress_code']}\\n"
        guide += f"• Maintain silence in prayer areas\\n"
        guide += f"• Don't point feet toward deity\\n"
        guide += f"• Join palms and bow when entering sanctum\\n\\n"
        
        guide += f"🎭 **Rituals You'll Witness:**\\n"
        guide += f"• Aarti (prayer with lamps) - morning and evening\\n"
        guide += f"• Devotees offering flowers, coconuts, sweets\\n"
        guide += f"• Chanting of mantras and bhajans\\n"
        guide += f"• Circumambulation (walking around deity)\\n\\n"
        
        guide += f"🎁 **Offerings & Prasad:**\\n"
        guide += f"• Prasad: Blessed food distributed to devotees\\n"
        guide += f"• Common offerings: Flowers, fruits, sweets, coconut\\n"
        guide += f"• Receive prasad with both hands\\n"
        guide += f"• Consider it sacred - consume respectfully\\n\\n"
        
        guide += f"💡 **Cultural Sensitivity:**\\n"
        guide += f"• Photography rules: {temple['cultural_info']}\\n"
        guide += f"• Observe and respect local customs\\n"
        guide += f"• Ask permission before photographing people\\n"
        guide += f"• Participate respectfully in rituals\\n\\n"
        
        guide += f"Need practical travel tips or booking help?"
        
        return guide

    def get_practical_guide(self, temple_id, country):
        temple = self.temples_data[temple_id]
        
        guide = f"🎒 **Practical Guide: {temple['name']}**\\n\\n"
        
        guide += f"🚗 **How to Reach:**\\n"
        guide += f"• Location: {temple['location']}\\n"
        guide += f"• Nearest Airport: Check domestic flights from major cities\\n"
        guide += f"• Train: Indian Railways connects to nearby stations\\n"
        guide += f"• Taxi/Cab: Available from airports and stations\\n"
        guide += f"• Local Transport: Auto-rickshaws, buses available\\n\\n"
        
        guide += f"⏰ **Best Time to Visit:**\\n"
        guide += f"• Season: {temple['best_time']} (pleasant weather)\\n"
        guide += f"• Daily: Early morning (6-9 AM) - less crowded\\n"
        guide += f"• Evening: 6-8 PM for evening aarti\\n"
        guide += f"• Avoid: 11 AM - 2 PM (peak crowd + hot weather)\\n\\n"
        
        guide += f"🎒 **What to Bring:**\\n"
        guide += f"• Valid ID/Passport (required for entry)\\n"
        guide += f"• Comfortable walking shoes (easy to remove)\\n"
        guide += f"• Modest clothing - {temple['dress_code']}\\n"
        guide += f"• Water bottle (stay hydrated)\\n"
        guide += f"• Small bag for prasad and belongings\\n"
        guide += f"• Cash in Indian Rupees\\n\\n"
        
        guide += f"💰 **Budget Planning:**\\n"
        guide += f"• Temple Entry: ₹50 per person\\n"
        guide += f"• Prasad: ₹15-50 per item\\n"
        guide += f"• Special Pooja: ₹51-251\\n"
        guide += f"• Transportation: Varies by distance\\n"
        guide += f"• Food: ₹100-300 per meal\\n\\n"
        
        guide += f"📱 **Useful Apps & Services:**\\n"
        guide += f"• Our temple booking system (book in advance!)\\n"
        guide += f"• Google Translate (Hindi-English)\\n"
        guide += f"• Uber/Ola for transportation\\n"
        guide += f"• Paytm/PhonePe for digital payments\\n\\n"
        
        guide += f"🏨 **Accommodation Tips:**\\n"
        guide += f"• Book hotels near temple for convenience\\n"
        guide += f"• Dharamshalas (pilgrim lodges) available\\n"
        guide += f"• Check reviews for international traveler-friendly places\\n\\n"
        
        guide += f"Ready to book your visit? I can help with that!"
        
        return guide

    def get_booking_assistance(self, temple_id):
        temple = self.temples_data[temple_id]
        
        response = f"🎫 **Booking Your Visit to {temple['name']}**\\n\\n"
        
        response += f"📋 **Booking Process:**\\n"
        response += f"1. Visit our booking page\\n"
        response += f"2. Select your preferred date (check crowd predictions)\\n"
        response += f"3. Choose time slot (7 options available)\\n"
        response += f"4. Enter number of visitors\\n"
        response += f"5. Add prasad or pooja services (optional)\\n"
        response += f"6. Complete secure payment\\n"
        response += f"7. Receive QR code via email\\n\\n"
        
        response += f"💡 **Booking Tips:**\\n"
        response += f"• Book 2-3 days in advance for better availability\\n"
        response += f"• Morning slots (6-9 AM) are less crowded\\n"
        response += f"• Green calendar days = low crowd\\n"
        response += f"• Yellow = medium crowd, Red = high crowd\\n"
        response += f"• Pre-book prasad to skip queues\\n\\n"
        
        response += f"💳 **Payment & Confirmation:**\\n"
        response += f"• International cards accepted\\n"
        response += f"• Secure payment gateway\\n"
        response += f"• Instant email confirmation with QR code\\n"
        response += f"• Show QR code at temple for entry\\n\\n"
        
        response += f"Would you like me to help you start the booking process?"
        
        return response

    def get_temple_list(self):
        temple_list = ""
        for temple_id, temple_data in self.temples_data.items():
            temple_list += f"{temple_id}. {temple_data['name']} - {temple_data['location']}\\n"
        return temple_list

# Global international chatbot instance
international_chatbot = InternationalTravelerChatbot()