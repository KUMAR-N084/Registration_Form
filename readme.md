# Secure User Registration System with Admin Panel

A comprehensive, secure web application for user registration with advanced validation, database storage, admin panel, and CSV export capabilities.

## 🎯 Project Overview

This is an **MCA 1st Semester** academic project that demonstrates:
- Full-stack web development
- Secure authentication and authorization
- Database management
- Form validation (client & server-side)
- Modern UI/UX design
- Data export functionality

## 📁 Project Structure

```
registration-system/
│
├── app.py                          # Flask application (main backend)
├── requirements.txt                # Python dependencies
├── .env                           # Environment variables (create this)
│
├── templates/
│   ├── index.html                 # Registration form
│   ├── admin_login.html           # Admin login page
│   ├── admin_dashboard.html       # Admin dashboard
│   └── user_detail.html           # User detail view
│
├── static/
│   ├── script.js                  # Frontend JavaScript
│   └── style.css                  # Existing CSS file
│
└── instance/
    └── registration.db            # SQLite database (auto-generated)
```

## 🛠️ Technology Stack

### Backend
- **Python 3.8+**
- **Flask** - Web framework
- **Flask-SQLAlchemy** - ORM
- **Flask-Login** - Authentication
- **Werkzeug** - Password hashing

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with animations
- **JavaScript (ES6+)** - Client-side validation

### Database
- **SQLite** (for local development)
- Easily upgradeable to **MySQL/PostgreSQL**

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Basic command line knowledge

## 🚀 Installation & Setup

### Step 1: Install Python Dependencies

Create a `requirements.txt` file:

```txt
Flask==3.0.0
Flask-SQLAlchemy==3.1.1
Flask-Login==0.6.3
Werkzeug==3.0.1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### Step 2: Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-super-secret-key-change-this-in-production
DATABASE_URL=sqlite:///registration.db
```

**Important:** Change `SECRET_KEY` to a random string for security.

Generate a secure key using Python:

```python
import secrets
print(secrets.token_hex(32))
```

### Step 3: Initialize Database

Run the Flask application to create tables:

```bash
python app.py
```

This will:
- Create the SQLite database
- Set up all tables
- Create a default admin account:
  - **Username:** `admin`
  - **Password:** `admin123`

⚠️ **Change the default admin password immediately!**

### Step 4: Project File Organization

Ensure your files are organized as follows:

```
registration-system/
├── app.py
├── requirements.txt
├── .env
├── templates/
│   ├── index.html
│   ├── admin_login.html
│   ├── admin_dashboard.html
│   └── user_detail.html
└── static/
    ├── script.js
    └── style.css
```

### Step 5: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## 📱 Usage Guide

### User Registration

1. Navigate to `http://localhost:5000`
2. Fill out the registration form with:
   - Profile photo
   - Personal details
   - Contact information
   - Address details
   - Password and security question
3. Click "Register"
4. View confirmation modal

### Admin Access

1. Navigate to `http://localhost:5000/admin/login`
2. Login with credentials:
   - Username: `admin`
   - Password: `admin123`
3. Access the dashboard to:
   - View all registered users
   - Search and filter users
   - View detailed user profiles
   - Export data to CSV
   - Delete users

### Admin Features

#### Dashboard
- View total user count
- Search users by name, username, or email
- Pagination for large datasets
- Quick actions (View/Delete)

#### Export CSV
- Click "Export CSV" in the dashboard
- Downloads a complete CSV file with all user data
- File naming format: `registrations_YYYYMMDD_HHMMSS.csv`

## 🔒 Security Features

### Implemented Security Measures

1. **Password Hashing**
   - Uses Werkzeug's PBKDF2-SHA256
   - Never stores passwords in plain text

2. **Server-Side Validation**
   - All inputs re-validated on backend
   - Prevents bypass of client-side validation

3. **SQL Injection Prevention**
   - Uses SQLAlchemy ORM
   - Parameterized queries

4. **Session Management**
   - Flask-Login for secure sessions
   - Protected admin routes with `@login_required`

5. **Input Sanitization**
   - Validation for all form fields
   - Rejection of dummy/malicious data
   - Pattern detection for gibberish

6. **File Upload Security**
   - Type validation (JPG, PNG, SVG only)
   - Size limits (5MB max)
   - Resolution checks

## 🗄️ Database Schema

### Users Table
```sql
- id (Primary Key)
- first_name, last_name
- username (Unique)
- email (Unique)
- mobile
- dob, age
- gender
- address, postal_code, country, state, city
- education
- profile_photo (Base64)
- security_question, security_answer
- password_hash
- guardian_name, guardian_email, guardian_phone (Nullable)
- created_at, updated_at
```

### Admins Table
```sql
- id (Primary Key)
- admin_username (Unique)
- admin_email (Unique)
- password_hash
- last_login
- created_at
```

## 📊 CSV Export Format

The exported CSV includes:
```
ID, First Name, Last Name, Username, Email, Mobile, 
Date of Birth, Age, Gender, Address, Postal Code, 
Country, State, City, Education, Security Question, 
Guardian Name, Guardian Email, Guardian Phone, Registration Date
```

## 🎨 UI/UX Features

- **Dark Theme** - Modern, professional appearance
- **Responsive Design** - Works on desktop and mobile
- **Smooth Animations** - Transitions and hover effects
- **Accessibility** - ARIA labels, keyboard navigation
- **Real-time Validation** - Instant feedback
- **Visual Feedback** - Color-coded validation states

## 🔧 Configuration Options

### Switching to MySQL

Update `.env`:

```env
DATABASE_URL=mysql+pymysql://username:password@localhost/registration_db
```

Install MySQL driver:

```bash
pip install pymysql
```

### Changing Secret Key

Generate and update in `.env`:

```python
import secrets
print(secrets.token_hex(32))
```

### Adjusting File Upload Limits

In `app.py`:

```python
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB
```

## 🐛 Troubleshooting

### Database Issues

**Problem:** Tables not created

**Solution:**
```python
from app import app, db
with app.app_context():
    db.create_all()
```

### Import Errors

**Problem:** Module not found

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Port Already in Use

**Problem:** Port 5000 is busy

**Solution:** Change port in `app.py`:
```python
app.run(debug=True, port=5001)
```

## 📈 Future Enhancements

### Planned Features
- [ ] User login and dashboard
- [ ] Email verification
- [ ] Password reset functionality
- [ ] Role-based access control
- [ ] Analytics dashboard
- [ ] PDF export
- [ ] Email notifications
- [ ] Two-factor authentication
- [ ] API endpoints
- [ ] CAPTCHA integration

## 🎓 Academic Mapping

### Demonstrates Knowledge Of:

1. **Web Technologies**
   - HTML5 semantic markup
   - CSS3 animations and layouts
   - JavaScript ES6+ features

2. **Python Programming**
   - Object-oriented design
   - Error handling
   - File operations

3. **Database Management**
   - Schema design
   - CRUD operations
   - Relationships and constraints

4. **Software Engineering**
   - MVC architecture
   - Modular design
   - Code organization

5. **Security Principles**
   - Authentication/Authorization
   - Input validation
   - Secure password storage

## 📝 Code Documentation

### Key Functions

#### Backend (app.py)

```python
@app.route('/register', methods=['POST'])
def register():
    """
    Handles user registration with server-side validation
    Returns: JSON response with success/error message
    """

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    """
    Admin dashboard with pagination and search
    Requires: Admin authentication
    """

@app.route('/admin/export-csv')
@login_required
def export_csv():
    """
    Exports all user data to CSV format
    Returns: CSV file download
    """
```

#### Frontend (script.js)

```javascript
validate(field)
// Validates a single form field with custom rules
// Returns: boolean

checkFormValid()
// Checks if entire form is valid and enables/disables submit
// Returns: void

hasRepetitivePattern(str)
// Detects gibberish and repetitive patterns
// Returns: boolean
```

## 👥 Creating Additional Admin Accounts

Option 1: Using Python Shell

```python
from app import app, db, Admin
from werkzeug.security import generate_password_hash

with app.app_context():
    new_admin = Admin(
        admin_username='newadmin',
        admin_email='newadmin@example.com',
        password_hash=generate_password_hash('securepassword')
    )
    db.session.add(new_admin)
    db.session.commit()
```

Option 2: Create a utility script (`create_admin.py`)

```python
from app import app, db, Admin
from werkzeug.security import generate_password_hash
import sys

def create_admin(username, email, password):
    with app.app_context():
        if Admin.query.filter_by(admin_username=username).first():
            print(f"Admin {username} already exists!")
            return
        
        admin = Admin(
            admin_username=username,
            admin_email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(admin)
        db.session.commit()
        print(f"Admin {username} created successfully!")

if __name__ == '__main__':
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
    else:
        create_admin(sys.argv[1], sys.argv[2], sys.argv[3])
```

Usage:
```bash
python create_admin.py newadmin admin@example.com password123
```

## 📄 License

This is an academic project for educational purposes.

## 🤝 Contributing

This is a student project. Feedback and suggestions are welcome!

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review code comments
3. Consult Flask documentation: https://flask.palletsprojects.com/

---

**Built with ❤️ for MCA 1st Semester**

**Note:** Remember to change default credentials and secret keys before any production use!