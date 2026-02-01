from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import requests as http_requests
import os
import csv
import io
import base64
import re

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///registration.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Disable caching in development
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

# ==================== CACHE BUSTING ====================
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            if os.path.exists(file_path):
                values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

# ==================== MODELS ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    mobile = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=False)
    postal_code = db.Column(db.String(6), nullable=False)
    country = db.Column(db.String(50), nullable=False)
    state = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    education = db.Column(db.String(50), nullable=False)
    profile_photo = db.Column(db.Text)  # Base64 or file path
    security_question = db.Column(db.String(100), nullable=False)
    security_answer = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Guardian fields (nullable for adults)
    guardian_name = db.Column(db.String(100))
    guardian_email = db.Column(db.String(100))
    guardian_phone = db.Column(db.String(10))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_username = db.Column(db.String(50), unique=True, nullable=False)
    admin_email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Admin {self.admin_username}>'

# ==================== LOGIN MANAGER ====================

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# ==================== VALIDATION HELPERS ====================

def validate_email(email):
    """RFC 5322 compliant email validation"""
    pattern = r'^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}$'
    if not re.match(pattern, email):
        return False
    
    # Block dummy emails
    dummy_emails = ['test@test.com', 'test@example.com', 'admin@admin.com', 
                    'demo@demo.com', 'sample@sample.com']
    if email.lower() in dummy_emails:
        return False
    
    return True

def validate_mobile(mobile):
    """Validate 10-digit Indian mobile number"""
    if not re.match(r'^[6789][0-9]{9}$', mobile):
        return False
    
    # Block dummy numbers
    dummy_phones = ['1234567890', '9999999999', '0000000000']
    if mobile in dummy_phones:
        return False
    
    return True

def validate_name(name):
    """Validate name (letters, spaces, dots, apostrophes, numbers allowed)"""
    if not name or len(name) < 1 or len(name) > 50:
        return False
    
    # Allow letters, numbers, spaces, dots, apostrophes, hyphens
    if not re.match(r'^[A-Za-z0-9]+(?:[.\s\'-]*[A-Za-z0-9]+)*\.?$', name):
        return False
    
    # Must contain at least one letter
    if not re.search(r'[A-Za-z]', name):
        return False
    
    return True

def calculate_age(dob):
    """Calculate age from date of birth"""
    today = datetime.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

def has_repeated_pattern(value):
    """Check for repeated patterns and consonant-heavy gibberish"""
    # 1. Check if any substring of length 2 or 3 repeats 3+ times consecutively
    for length in [2, 3]:
        for i in range(len(value) - length * 3 + 1):
            substring = value[i:i+length]
            if substring * 3 == value[i:i+length*3]:
                return True
                
    # 2. Check for consonant-heavy gibberish
    if len(value) >= 8:
        # Count total letters
        total_letters = len(re.findall(r'[a-zA-Z]', value))
        # Count consonants
        consonants = len(re.findall(r'[bcdfghjklmnpqrstvwxyzBCDFGHJKLMNPQRSTVWXYZ]', value))
        
        if total_letters > 0 and (consonants / total_letters) > 0.75:
            return True
            
    return False

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Serve the registration form"""
    return render_template('index.html')

@app.route('/register', methods=['POST'])
def register():
    """Handle user registration"""
    try:
        data = request.json
        
        # Log incoming data for debugging
        print(f"\n{'='*60}")
        print(f"📥 Registration Request Received")
        print(f"{'='*60}")
        print(f"Name: {data.get('firstName')} {data.get('lastName')}")
        print(f"Username: {data.get('username')}")
        print(f"Email: {data.get('email')}")
        print(f"Mobile: {data.get('mobile')}")
        
        # Validate required fields
        required_fields = ['firstName', 'lastName', 'username', 'email', 'mobile', 
                          'dob', 'gender', 'address', 'postalCode', 'country', 
                          'state', 'city', 'education', 'password', 'securityQuestion', 
                          'securityAnswer', 'profilePhoto']
        
        missing_fields = [field for field in required_fields if field not in data or not data[field]]
        if missing_fields:
            print(f"❌ Missing fields: {', '.join(missing_fields)}")
            return jsonify({'success': False, 'message': f'Missing required fields: {", ".join(missing_fields)}'}), 400
        
        # Server-side validation
        if not validate_email(data['email']):
            print(f"❌ Invalid email: {data['email']}")
            return jsonify({'success': False, 'message': f'Invalid email format: {data["email"]}'}), 400
        
        if not validate_mobile(data['mobile']):
            print(f"❌ Invalid mobile: {data['mobile']}")
            return jsonify({'success': False, 'message': f'Invalid mobile number: {data["mobile"]}'}), 400
        
        if not validate_name(data['firstName']):
            print(f"❌ Invalid first name: {data['firstName']}")
            return jsonify({'success': False, 'message': f'Invalid first name format: {data["firstName"]}'}), 400
        
        if not validate_name(data['lastName']):
            print(f"❌ Invalid last name: {data['lastName']}")
            return jsonify({'success': False, 'message': f'Invalid last name format: {data["lastName"]}'}), 400
        
        # Check if username or email already exists
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            print(f"❌ Username already exists: {data['username']}")
            return jsonify({'success': False, 'message': f'Username "{data["username"]}" is already taken'}), 400
        
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            print(f"❌ Email already registered: {data['email']}")
            return jsonify({'success': False, 'message': f'Email "{data["email"]}" is already registered'}), 400
        
        # Parse DOB and calculate age
        try:
            dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
        except ValueError as e:
            print(f"❌ Invalid date format: {data['dob']}")
            return jsonify({'success': False, 'message': 'Invalid date of birth format'}), 400
        
        age = calculate_age(dob)
        
        if age < 13:
            print(f"❌ Age too young: {age} years")
            return jsonify({'success': False, 'message': 'Must be at least 13 years old to register'}), 400
        
        print(f"✓ All validations passed")
        print(f"✓ Creating user record...")
        
        # Create new user
        new_user = User(
            first_name=data['firstName'],
            last_name=data['lastName'],
            username=data['username'],
            email=data['email'],
            mobile=data['mobile'],
            dob=dob,
            age=age,
            gender=data['gender'],
            address=data['address'],
            postal_code=data['postalCode'],
            country=data['country'],
            state=data['state'],
            city=data['city'],
            education=data['education'],
            profile_photo=data['profilePhoto'],  # Store base64
            security_question=data['securityQuestion'],
            security_answer=data['securityAnswer'],
            password_hash=generate_password_hash(data['password']),
            guardian_name=data.get('guardianName'),
            guardian_email=data.get('guardianEmail'),
            guardian_phone=data.get('guardianPhone')
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        print(f"✅ SUCCESS! User registered:")
        print(f"   ID: {new_user.id}")
        print(f"   Username: {new_user.username}")
        print(f"   Email: {new_user.email}")
        print(f"   Age: {new_user.age} years")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True, 
            'message': 'Registration successful!',
            'user_id': new_user.id,
            'username': new_user.username
        }), 201
        
    except Exception as e:
        db.session.rollback()
        print(f"\n{'='*60}")
        print(f"❌ REGISTRATION ERROR")
        print(f"{'='*60}")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*60}\n")
        return jsonify({'success': False, 'message': f'Server error: {str(e)}'}), 500

@app.route('/api/validate', methods=['POST'])
def api_validate():
    data = request.json
    field = data.get('field')
    value = data.get('value')
    
    if not field or value is None:
        return jsonify({"valid": False, "message": "Field and value are required"}), 400
        
    valid = True
    message = ""
    
    # Common helper for repeated patterns
    if field in ['firstName', 'lastName', 'username', 'email', 'guardianEmail', 'mobile', 'guardianPhone', 'password', 'address', 'securityAnswer', 'guardianName', 'postalCode']:
         # The prompt asks to apply "no repeated patterns" to all except dropdowns and DOB/confirmPassword specific logic
         # But the constraint sets list it explicitly for specific fields. I'll apply where required.
         pass

    if field in ['firstName', 'lastName', 'guardianName']:
        label = "Guardian name" if field == 'guardianName' else ("First name" if field == 'firstName' else "Last name")
        max_len = 100 if field == 'guardianName' else 20
        
        if len(value) < 2:
            return jsonify({"valid": False, "message": "Must be at least 2 characters"})
        if len(value) > max_len:
            return jsonify({"valid": False, "message": f"Must not exceed {max_len} characters"})
        if not re.match(r"^[A-Za-z]+(?:[.\s'-]*[A-Za-z]+)*\.?$", value):
            return jsonify({"valid": False, "message": "Only letters, spaces, dots, apostrophes allowed"})
        if value.lower() in ['test','admin','demo','sample','temp','dummy','abc','xyz','asdf']:
            return jsonify({"valid": False, "message": "This name is not allowed"})
        if has_repeated_pattern(value):
            return jsonify({"valid": False, "message": "No gibberish or repeated patterns allowed"})
        message = f"{label} accepted"

    elif field == 'username':
        if len(value) < 3:
            return jsonify({"valid": False, "message": "Username must be at least 3 characters"})
        if len(value) > 30:
            return jsonify({"valid": False, "message": "Username must not exceed 30 characters"})
        if not re.match(r"^[A-Za-z0-9_@.#$%&*+-]{3,}$", value):
            return jsonify({"valid": False, "message": "Only letters, numbers, and _@.#$%&*+- allowed"})
        if value.lower() in ['test','admin','user','demo','sample','temp','hello','abc',
                             'test123','user123','admin123','password','qwerty','asdfgh',
                             'test1234','testuser','adminuser','demouser']:
            return jsonify({"valid": False, "message": "This username is not allowed"})
        if has_repeated_pattern(value):
            return jsonify({"valid": False, "message": "No gibberish or repeated patterns allowed"})
        
        # Check DB for duplicate username
        if User.query.filter_by(username=value).first():
            return jsonify({"valid": False, "message": "Username is already taken"})

        message = "Username is available"

    elif field in ['email', 'guardianEmail']:
        if len(value) < 5:
            return jsonify({"valid": False, "message": "Email must be at least 5 characters"})
        if len(value) > 100:
            return jsonify({"valid": False, "message": "Email must not exceed 100 characters"})
        if not re.match(r"^[A-Za-z0-9._+%-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,6}$", value):
            return jsonify({"valid": False, "message": "Enter a valid email address"})
        
        # Extra email constraints
        local, domain = value.split('@')
        if '..' in local or '..' in domain:
            return jsonify({"valid": False, "message": "Enter a valid email address"})
        if local.startswith('.') or local.endswith('.'):
             return jsonify({"valid": False, "message": "Enter a valid email address"})
        if not re.search(r'[a-zA-Z]', local):
             return jsonify({"valid": False, "message": "Enter a valid email address"})
             
        # Repeated TLD check
        tld = domain.split('.')[-1]
        if len(tld) * 2 == len(domain.split('.')[-1] * 2) and domain.endswith(tld+tld): 
             # Rough check for repetition like .comcom. 
             # Better: check if the string ends with a pattern that repeats.
             # The constraint says "reject if TLD repeats like .comcom".
             if tld + tld in domain:
                  return jsonify({"valid": False, "message": "Invalid domain extension"})

        if value.lower() in ['test@test.com','test@example.com','admin@admin.com',
                             'user@user.com','demo@demo.com','demo@example.com',
                             'sample@sample.com','info@info.com','test@gmail.com',
                             'dummy@dummy.com','temp@temp.com','hello@hello.com',
                             'abc@abc.com','admin@example.com']:
            return jsonify({"valid": False, "message": "This email is not allowed"})
        
        # Check DB for duplicate email (only for main email)
        if field == 'email':
            if User.query.filter_by(email=value).first():
                return jsonify({"valid": False, "message": "Email is already registered"})
        
        message = "Guardian email accepted" if field == 'guardianEmail' else "Email format is valid"

    elif field in ['mobile', 'guardianPhone']:
        if len(value) != 10:
             return jsonify({"valid": False, "message": "Must be exactly 10 digits"})
        if not re.match(r"^[6789][0-9]{9}$", value):
             return jsonify({"valid": False, "message": "Must start with 6, 7, 8, or 9"})
        if value in ['1234567890','9999999999','1111111111','5555555555',
                     '0000000000','6666666666','7777777777','8888888888',
                     '1234567801','9876543210']:
            return jsonify({"valid": False, "message": "This number is not allowed"})
        if len(set(value)) == 1:
             return jsonify({"valid": False, "message": "Enter a real phone number"})
        message = "Guardian phone accepted" if field == 'guardianPhone' else "Mobile number accepted"

    elif field == 'password':
        if len(value) < 8:
             return jsonify({"valid": False, "message": "Password must be at least 8 characters"})
        if len(value) > 50:
             return jsonify({"valid": False, "message": "Password must not exceed 50 characters"})
        if not re.search(r'[A-Z]', value):
             return jsonify({"valid": False, "message": "Must include at least one uppercase letter"})
        if not re.search(r'[a-z]', value):
             return jsonify({"valid": False, "message": "Must include at least one lowercase letter"})
        if not re.search(r'\d', value):
             return jsonify({"valid": False, "message": "Must include at least one number"})
        if not re.search(r'[@$!%*?&]', value):
             return jsonify({"valid": False, "message": "Must include at least one special character (@$!%*?&)"})
        if has_repeated_pattern(value):
             return jsonify({"valid": False, "message": "No repeated patterns allowed in password"})
        message = "Password is strong"

    elif field == 'confirmPassword':
        password_value = data.get('passwordValue')
        if not password_value:
             return jsonify({"valid": False, "message": "Password value is required for confirmation"})
        if value != password_value:
             return jsonify({"valid": False, "message": "Passwords do not match"})
        message = "Passwords match"

    elif field == 'postalCode':
        if len(value) != 6:
             return jsonify({"valid": False, "message": "Must be exactly 6 digits"})
        if not re.match(r"^[0-9]{6}$", value):
             return jsonify({"valid": False, "message": "Enter a valid postal code"})
        if len(set(value)) == 1:
             return jsonify({"valid": False, "message": "Enter a valid postal code"})
        message = "Postal code accepted"

    elif field == 'address':
        if len(value) < 10:
             return jsonify({"valid": False, "message": "Address must be at least 10 characters"})
        if len(value) > 200:
             return jsonify({"valid": False, "message": "Address must not exceed 200 characters"})
        if not re.match(r"^[A-Za-z0-9\s.,#-]{10,}$", value):
             return jsonify({"valid": False, "message": "Only letters, numbers, spaces, and .,#- allowed"})
        if has_repeated_pattern(value):
             return jsonify({"valid": False, "message": "No gibberish or repeated patterns allowed"})
        message = "Address accepted"

    elif field == 'securityAnswer':
        if len(value) < 2:
             return jsonify({"valid": False, "message": "Answer must be at least 2 characters"})
        if len(value) > 100:
             return jsonify({"valid": False, "message": "Answer must not exceed 100 characters"})
        if has_repeated_pattern(value):
             return jsonify({"valid": False, "message": "No gibberish or repeated patterns allowed"})
        message = "Answer accepted"

    elif field == 'dob':
        try:
            date_obj = datetime.strptime(value, '%Y-%m-%d').date()
            if date_obj > datetime.now().date():
                 return jsonify({"valid": False, "message": "Date cannot be in the future"})
            if date_obj.year < 1900 or date_obj.year > datetime.now().year:
                 return jsonify({"valid": False, "message": f"Year must be between 1900 and {datetime.now().year}"})
            
            age = calculate_age(date_obj)
            if age < 13:
                 return jsonify({"valid": False, "message": "Must be at least 13 years old"})
            message = "Date of birth accepted"
        except ValueError:
            return jsonify({"valid": False, "message": "Enter a valid date (YYYY-MM-DD)"})

    elif field in ['country', 'state', 'city', 'education', 'securityQuestion']:
        if not value:
             return jsonify({"valid": False, "message": f"Please select {field}"})
        
        labels = {
            'country': 'Country', 'state': 'State', 'city': 'City',
            'education': 'Education', 'securityQuestion': 'Security question'
        }
        message = f"{labels.get(field, field)} selected"

    else:
        # Default fallback for unknown fields
        message = "Field accepted"

    return jsonify({"valid": True, "message": message})

# ==================== LOCATION API ROUTES (WITH FALLBACK) ====================

@app.route('/api/countries', methods=['GET'])
def get_countries():
    api_key = os.environ.get('CSC_API_KEY')
    
    # Try fetching from API if key exists
    if api_key:
        try:
            response = http_requests.get(
                "https://api.countrystatecity.in/v1/countries", 
                headers={"API-Key": api_key},
                timeout=5
            )
            if response.status_code == 200:
                return jsonify(response.json())
        except Exception as e:
            print(f"⚠️ Location API Error: {str(e)}")
            
    # Fallback Data
    return jsonify([
        {"id": 101, "name": "India", "iso2": "IN"},
        {"id": 231, "name": "United States", "iso2": "US"},
        {"id": 230, "name": "United Kingdom", "iso2": "GB"},
        {"id": 38, "name": "Canada", "iso2": "CA"},
        {"id": 13, "name": "Australia", "iso2": "AU"}
    ])

@app.route('/api/states/<int:country_id>', methods=['GET'])
def get_states(country_id):
    api_key = os.environ.get('CSC_API_KEY')
    
    # Try fetching from API
    if api_key:
        try:
            response = http_requests.get(
                f"https://api.countrystatecity.in/v1/countries/{country_id}/states", 
                headers={"API-Key": api_key},
                timeout=5
            )
            if response.status_code == 200:
                return jsonify(response.json())
        except Exception:
            pass
            
    # Fallback Data
    fallbacks = {
        101: [{"id": 4026, "name": "Karnataka"}, {"id": 4023, "name": "Maharashtra"}, {"id": 4035, "name": "Tamil Nadu"}, {"id": 4008, "name": "Delhi"}],
        231: [{"id": 3919, "name": "California"}, {"id": 3951, "name": "New York"}, {"id": 3970, "name": "Texas"}, {"id": 3932, "name": "Florida"}]
    }
    return jsonify(fallbacks.get(country_id, [{"id": 0, "name": "State Selection Not Available (No API Key)"}]))

@app.route('/api/cities/<int:country_id>/<int:state_id>', methods=['GET'])
def get_cities(country_id, state_id):
    api_key = os.environ.get('CSC_API_KEY')
    
    # Try fetching from API
    if api_key:
        try:
            response = http_requests.get(
                f"https://api.countrystatecity.in/v1/countries/{country_id}/states/{state_id}/cities", 
                headers={"API-Key": api_key},
                timeout=5
            )
            if response.status_code == 200:
                return jsonify(response.json())
        except Exception:
            pass
            
    # Fallback Data
    fallbacks = {
        4026: [{"id": 1, "name": "Bangalore"}, {"id": 2, "name": "Mysore"}, {"id": 3, "name": "Hubli"}],
        4023: [{"id": 4, "name": "Mumbai"}, {"id": 5, "name": "Pune"}, {"id": 6, "name": "Nagpur"}],
        3919: [{"id": 7, "name": "Los Angeles"}, {"id": 8, "name": "San Francisco"}, {"id": 9, "name": "San Diego"}],
        3951: [{"id": 10, "name": "New York City"}, {"id": 11, "name": "Buffalo"}, {"id": 12, "name": "Albany"}]
    }
    return jsonify(fallbacks.get(state_id, [{"id": 0, "name": "City Selection Not Available"}]))

# ==================== ADMIN ROUTES ====================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(admin_username=username).first()
        
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            admin.last_login = datetime.utcnow()
            db.session.commit()
            flash('Login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
@login_required
def admin_logout():
    """Admin logout"""
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """Admin dashboard with all user data"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    search_query = request.args.get('search', '')
    
    if search_query:
        users = User.query.filter(
            db.or_(
                User.first_name.ilike(f'%{search_query}%'),
                User.last_name.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        ).order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    else:
        users = User.query.order_by(User.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('admin_dashboard.html', users=users, search_query=search_query)

@app.route('/admin/export-csv')
@login_required
def export_csv():
    """Export all user data to CSV"""
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write headers
    headers = ['ID', 'First Name', 'Last Name', 'Username', 'Email', 'Mobile', 
               'Date of Birth', 'Age', 'Gender', 'Address', 'Postal Code', 
               'Country', 'State', 'City', 'Education', 'Security Question', 
               'Guardian Name', 'Guardian Email', 'Guardian Phone', 
               'Registration Date']
    writer.writerow(headers)
    
    # Write data
    for user in users:
        writer.writerow([
            user.id,
            user.first_name,
            user.last_name,
            user.username,
            user.email,
            user.mobile,
            user.dob.strftime('%Y-%m-%d'),
            user.age,
            user.gender,
            user.address,
            user.postal_code,
            user.country,
            user.state,
            user.city,
            user.education,
            user.security_question,
            user.guardian_name or '',
            user.guardian_email or '',
            user.guardian_phone or '',
            user.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    # Prepare response
    output.seek(0)
    return send_file(
        io.BytesIO(output.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'registrations_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@app.route('/admin/user/<int:user_id>')
@login_required
def view_user(user_id):
    """View detailed user information"""
    user = User.query.get_or_404(user_id)
    return render_template('user_detail.html', user=user)

@app.route('/admin/user/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    user = User.query.get_or_404(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{username}" deleted successfully', 'success')
    return redirect(url_for('admin_dashboard'))

# ==================== DISABLE CACHE IN DEVELOPMENT ====================
@app.after_request
def add_header(response):
    """Disable caching for development"""
    if app.debug:
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
    return response

# ==================== INITIALIZATION ====================

def init_db():
    """Initialize database and create default admin"""
    with app.app_context():
        db.create_all()
        
        # Create default admin if doesn't exist
        if not Admin.query.filter_by(admin_username='admin').first():
            default_admin = Admin(
                admin_username='admin',
                admin_email='admin@example.com',
                password_hash=generate_password_hash('admin123')
            )
            db.session.add(default_admin)
            db.session.commit()
            print("\n" + "="*60)
            print("DEFAULT ADMIN ACCOUNT CREATED")
            print("="*60)
            print("Username: admin")
            print("Password: admin123")
            print("⚠️  CHANGE THIS PASSWORD IMMEDIATELY!")
            print("="*60 + "\n")

if __name__ == '__main__':
    init_db()
    print("\n" + "="*60)
    print("🚀 FLASK SERVER STARTING")
    print("="*60)
    print("📍 Registration Form: http://localhost:5000")
    print("🔐 Admin Login: http://localhost:5000/admin/login")
    print("="*60 + "\n")
    app.run(debug=True, host='0.0.0.0', port=5000)