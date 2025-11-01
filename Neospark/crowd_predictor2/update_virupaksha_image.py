from app import app, db, Temple
import shutil
import os

def update_virupaksha_image():
    with app.app_context():
        # Find Virupaksha Temple
        temple = Temple.query.filter_by(name='Virupaksha Temple').first()
        
        if temple:
            # Copy new image
            source_image = r"C:\Users\srikh\Downloads\1.jpeg"
            static_dir = "static"
            os.makedirs(static_dir, exist_ok=True)
            
            if os.path.exists(source_image):
                shutil.copy2(source_image, os.path.join(static_dir, "virupaksha_temple.jpeg"))
                temple.image_url = "/static/virupaksha_temple.jpeg"
                db.session.commit()
                print("✅ Virupaksha Temple image updated successfully!")
            else:
                print("❌ Source image not found")
        else:
            print("❌ Virupaksha Temple not found")

if __name__ == "__main__":
    update_virupaksha_image()