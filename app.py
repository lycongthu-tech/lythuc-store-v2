import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = 'lythucstore_secret_key'

# Cấu hình Cơ sở dữ liệu SQLite
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(BASE_DIR, 'dulieu.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model Bảng Sản Phẩm
class SanPham(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(200), nullable=False)
    gia = db.Column(db.String(50), nullable=False)
    gia_cu = db.Column(db.String(50))
    danh_muc = db.Column(db.String(50))
    tag = db.Column(db.String(50))
    link_affiliate = db.Column(db.String(500), nullable=False)
    anh = db.Column(db.String(500), nullable=False)

# Khởi tạo CSDL
with app.app_context():
    db.create_all()

# Trang chủ
@app.route('/')
def index():
    san_pham = SanPham.query.all()
    return render_template('index.html', san_pham=san_pham)

# Trang đăng nhập Admin
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ten_dang_nhap = request.form.get('ten_dang_nhap')
        mat_khau = request.form.get('mat_khau')
        
        # ANH ĐỔI TÊN ĐĂNG NHẬP VÀ MẬT KHẨU TẠI ĐÂY:
        if ten_dang_nhap == 'thuc' and mat_khau == '1598thuc':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Tên đăng nhập hoặc mật khẩu không đúng!")
    return render_template('login.html')

# Trang Quản trị Admin
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        ten = request.form.get('ten')
        gia = request.form.get('gia')
        gia_cu = request.form.get('gia_cu')
        danh_muc = request.form.get('danh_muc')
        tag = request.form.get('tag')
        link_affiliate = request.form.get('link_affiliate')
        anh = request.form.get('anh')

        sp_moi = SanPham(
            ten=ten, gia=gia, gia_cu=gia_cu, 
            danh_muc=danh_muc, tag=tag, 
            link_affiliate=link_affiliate, anh=anh
        )
        db.session.add(sp_moi)
        db.session.commit()
        return redirect(url_for('admin'))

    san_pham = SanPham.query.all()
    return render_template('admin.html', san_pham=san_pham)

# Đăng xuất Admin
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)