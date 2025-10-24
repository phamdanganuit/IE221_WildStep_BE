#!/usr/bin/env python
"""
Script để tạo lại user admin với password hash đúng
"""
import os
import sys
import django
from datetime import datetime
import base64

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from users.models import User
from users.auth import hash_password, check_password

def create_admin_user():
    """Tạo lại user admin với password hash đúng"""
    
    # Kiểm tra xem file ảnh có tồn tại không
    avatar_path = "avt.jpg"
    if not os.path.exists(avatar_path):
        print(f"Khong tim thay file anh: {avatar_path}")
        return False
    
    try:
        # Đọc ảnh và chuyển thành base64
        with open(avatar_path, "rb") as image_file:
            image_data = image_file.read()
            avatar_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Xóa user admin cũ nếu có
        User.objects(email="admin@shoe-shop.com").delete()
        
        # Tạo user admin mới với password hash đúng
        admin_user = User(
            email="admin@shoe-shop.com",
            password_hash=hash_password("admin123"),  # Sử dụng bcrypt
            role="admin",
            username="admin",
            displayName="Administrator",
            phone="0123456789",
            sex="female",
            birth=datetime(1995, 6, 15),
            avatar=f"data:image/jpeg;base64,{avatar_base64}",
            vouchers=[]
        )
        
        # Lưu vào database
        admin_user.save()
        
        print("Tao lai user admin thanh cong!")
        print(f"   Email: {admin_user.email}")
        print(f"   Username: {admin_user.username}")
        print(f"   Display Name: {admin_user.displayName}")
        print(f"   Phone: {admin_user.phone}")
        print(f"   Sex: {admin_user.sex}")
        print(f"   Birth: {admin_user.birth}")
        print(f"   Role: {admin_user.role}")
        print(f"   Avatar: Da upload tu {avatar_path}")
        print(f"   Created at: {admin_user.created_at}")
        
        # Test password
        if check_password("admin123", admin_user.password_hash):
            print("   Password test: THANH CONG!")
        else:
            print("   Password test: THAT BAI!")
        
        return True
        
    except Exception as e:
        print(f"Loi khi tao user admin: {str(e)}")
        return False

def main():
    """Hàm main"""
    print("Bat dau tao lai user admin...")
    print("=" * 50)
    
    success = create_admin_user()
    
    print("=" * 50)
    if success:
        print("Hoan thanh!")
    else:
        print("That bai!")
    
    return success

if __name__ == "__main__":
    main()
