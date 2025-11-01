from app import app, db, Temple, Crowd, Prasad, Pooja
import shutil
import os

def update_temples():
    with app.app_context():
        # Update existing temples to Virupaksha Temple
        temples = Temple.query.all()
        
        # If no temples exist, create one
        if not temples:
            temple = Temple()
            db.session.add(temple)
            temples = [temple]
        
        # Copy image to static folder
        source_image = r"C:\Users\srikh\Downloads\1.jpeg"
        static_dir = "static"
        os.makedirs(static_dir, exist_ok=True)
        
        if os.path.exists(source_image):
            shutil.copy2(source_image, os.path.join(static_dir, "virupaksha_temple.jpeg"))
            image_url = "/static/virupaksha_temple.jpeg"
        else:
            image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8b/Virupaksha_Temple_Hampi.jpg/500px-Virupaksha_Temple_Hampi.jpg"
        
        # Update first temple to Virupaksha Temple
        temple = temples[0]
        temple.name = 'Virupaksha Temple'
        temple.location = 'Hampi, Karnataka'
        temple.latitude = 15.3350
        temple.longitude = 76.4600
        temple.capacity = 200
        temple.opening_time = '06:00'
        temple.closing_time = '20:00'
        temple.description = 'Ancient temple dedicated to Lord Shiva, UNESCO World Heritage site in Hampi ruins.'
        temple.image_url = image_url
        temple.is_active = True
        
        # Deactivate other temples
        for i in range(1, len(temples)):
            temples[i].is_active = False
        
        # Update crowd data
        crowd = Crowd.query.filter_by(temple_id=temple.id).first()
        if not crowd:
            crowd = Crowd(temple_id=temple.id, status='Low', count=0, accuracy=1.0)
            db.session.add(crowd)
        
        # Clear existing prasads and poojas for this temple
        Prasad.query.filter_by(temple_id=temple.id).delete()
        Pooja.query.filter_by(temple_id=temple.id).delete()
        
        # Add new prasads
        prasads = [
            Prasad(name='Vibhuti', price=20, temple_id=temple.id),
            Prasad(name='Rudraksha', price=50, temple_id=temple.id),
            Prasad(name='Coconut', price=15, temple_id=temple.id),
            Prasad(name='Flowers', price=25, temple_id=temple.id)
        ]
        
        # Add new poojas
        poojas = [
            Pooja(name='Shiva Abhishek', price=101, duration=30, temple_id=temple.id),
            Pooja(name='Rudrabhishek', price=251, duration=45, temple_id=temple.id),
            Pooja(name='Evening Aarti', price=51, duration=20, temple_id=temple.id)
        ]
        
        for prasad in prasads:
            db.session.add(prasad)
        for pooja in poojas:
            db.session.add(pooja)
        
        db.session.commit()
        print("✅ Virupaksha Temple added successfully!")
        print(f"📍 Location: Hampi, Karnataka")
        print(f"🖼️ Image: {image_url}")

if __name__ == "__main__":
    update_temples()