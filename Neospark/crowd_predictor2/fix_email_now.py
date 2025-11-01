import webbrowser
import time

print("URGENT EMAIL FIX REQUIRED")
print("=" * 50)
print("Gmail is blocking login with regular password!")
print("You MUST generate an App Password NOW")
print()

print("STEP 1: Opening Gmail Security Settings...")
webbrowser.open("https://myaccount.google.com/security")
time.sleep(2)

print("\nSTEP 2: DO THESE ACTIONS:")
print("1. Sign in with: srikharsri.j@gmail.com")
print("2. Find '2-Step Verification' - TURN IT ON")
print("3. Find 'App passwords' - CLICK IT")
print("4. Select 'Mail' app")
print("5. COPY the 16-character password")

print("\nSTEP 3: Enter the App Password here:")
app_password = input("Paste your 16-character App Password: ").strip().replace(" ", "")

if len(app_password) == 16:
    # Update config.py immediately
    with open('config.py', 'r') as f:
        content = f.read()
    
    updated_content = content.replace(
        "MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'zcfrdrpgxalygkrp'",
        f"MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or '{app_password}'"
    )
    
    with open('config.py', 'w') as f:
        f.write(updated_content)
    
    print(f"\nFIXED! App password updated: {app_password}")
    
    # Test immediately
    print("\nTesting email NOW...")
    import subprocess
    result = subprocess.run(["python", "test_email.py"], capture_output=True, text=True)
    
    if "Test email sent successfully!" in result.stdout:
        print("EMAIL IS NOW WORKING! Booking emails will be sent!")
    else:
        print("Still not working. Check the app password again.")
        print(result.stdout)
else:
    print("❌ Wrong length! App password must be exactly 16 characters.")
    print("Try again - remove any spaces.")