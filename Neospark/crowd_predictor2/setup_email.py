import webbrowser

def setup_gmail_app_password():
    print("🔧 Gmail App Password Setup")
    print("=" * 40)
    
    print("\n1. Opening Gmail Security Settings...")
    webbrowser.open("https://myaccount.google.com/security")
    
    print("\n2. Follow these steps:")
    print("   ✅ Sign in with: srikharsri.j@gmail.com")
    print("   ✅ Enable '2-Step Verification' (if not already enabled)")
    print("   ✅ Go to 'App passwords' section")
    print("   ✅ Select 'Mail' as the app")
    print("   ✅ Generate password")
    
    print("\n3. Copy the 16-character password and paste it here:")
    app_password = input("Enter your Gmail App Password: ").strip()
    
    if len(app_password) == 16:
        # Update config.py
        with open('config.py', 'r') as f:
            content = f.read()
        
        # Replace the password
        updated_content = content.replace(
            "MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'zcfrdrpgxalygkrp'",
            f"MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '{app_password}'"
        )
        
        with open('config.py', 'w') as f:
            f.write(updated_content)
        
        print(f"\n✅ Config updated with app password: {app_password}")
        print("✅ Email should now work for booking confirmations!")
        
        # Test the email
        print("\n🧪 Testing email configuration...")
        import subprocess
        subprocess.run(["python", "test_email.py"])
        
    else:
        print("❌ Invalid app password length. Should be 16 characters.")

if __name__ == "__main__":
    setup_gmail_app_password()