from app import app, db, User, Admin

with app.app_context():
    print("\n" + "="*60)
    print("DATABASE DEBUG")
    print("="*60 + "\n")
    
    total_users = User.query.count()
    print(f"Total Users: {total_users}\n")
    
    if total_users > 0:
        users = User.query.order_by(User.created_at.desc()).limit(5).all()
        for user in users:
            print(f"- {user.first_name} {user.last_name} (@{user.username})")
    else:
        print("❌ NO USERS FOUND - Registration not saving!")
    
    print("\n" + "="*60 + "\n")