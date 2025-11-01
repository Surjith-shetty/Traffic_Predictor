from app import app, db, Temple, Crowd, Prasad, Pooja
import shutil
import os

def update_other_temples():
    with app.app_context():
        temples = Temple.query.all()
        
        # Copy images to static folder
        static_dir = "static"
        os.makedirs(static_dir, exist_ok=True)
        
        temple_data = [
            {
                'name': 'Murudeshwara Temple',
                'location': 'Murudeshwara, Karnataka',
                'latitude': 14.0942,
                'longitude': 74.4849,
                'capacity': 300,
                'description': 'Famous Shiva temple with the world\'s second tallest Shiva statue.',
                'image_src': r"C:\Users\srikh\Downloads\2.jpeg",
                'image_name': 'murudeshwara_temple.jpeg'
            },
            {
                'name': 'Sri Krishna Temple, Udupi',
                'location': 'Udupi, Karnataka',
                'latitude': 13.3409,
                'longitude': 74.7421,
                'capacity': 250,
                'description': 'Ancient Krishna temple famous for its unique worship through a window.',
                'image_src': r"C:\Users\srikh\Downloads\3.jpeg",
                'image_name': 'udupi_temple.jpeg'
            },
            {
                'name': 'Chennakeshava Temple, Belur',
                'location': 'Belur, Karnataka',
                'latitude': 13.1622,
                'longitude': 75.8648,
                'capacity': 150,
                'description': 'Hoysala architecture masterpiece dedicated to Lord Vishnu.',
                'image_src': r"C:\Users\srikh\Downloads\4.jpeg",
                'image_name': 'belur_temple.jpeg'
            }
        ]
        
        # Update temples starting from index 1 (skip Virupaksha)
        for i, data in enumerate(temple_data):
            if i + 1 < len(temples):
                temple = temples[i + 1]
            else:
                # Create new temple if not enough exist
                temple = Temple()
                db.session.add(temple)
                db.session.flush()
            
            # Copy image
            if os.path.exists(data['image_src']):
                shutil.copy2(data['image_src'], os.path.join(static_dir, data['image_name']))
                image_url = f"/static/{data['image_name']}"
            else:
                image_url = f"https://example.com/{data['image_name']}"
            
            # Update temple details
            temple.name = data['name']
            temple.location = data['location']
            temple.latitude = data['latitude']
            temple.longitude = data['longitude']
            temple.capacity = data['capacity']
            temple.opening_time = '06:00'
            temple.closing_time = '20:00'
            temple.description = data['description']
            temple.image_url = image_url
            temple.is_active = True
            
            # Ensure crowd data exists
            crowd = Crowd.query.filter_by(temple_id=temple.id).first()
            if not crowd:
                crowd = Crowd(temple_id=temple.id, status='Low', count=0, accuracy=1.0)
                db.session.add(crowd)
            
            # Clear and add prasads
            Prasad.query.filter_by(temple_id=temple.id).delete()
            prasads = [
                Prasad(name='Coconut', price=15, temple_id=temple.id),
                Prasad(name='Flowers', price=20, temple_id=temple.id),
                Prasad(name='Prasadam', price=25, temple_id=temple.id)
            ]
            for prasad in prasads:
                db.session.add(prasad)
            
            # Clear and add poojas
            Pooja.query.filter_by(temple_id=temple.id).delete()
            poojas = [
                Pooja(name='Abhishek', price=101, duration=30, temple_id=temple.id),
                Pooja(name='Aarti', price=51, duration=15, temple_id=temple.id)
            ]
            for pooja in poojas:
                db.session.add(pooja)
            
            print(f"✅ {data['name']} updated successfully!")
        
        db.session.commit()
        print("🏛️ All temples updated!")

if __name__ == "__main__":
    update_other_temples()