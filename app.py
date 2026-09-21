import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SECRET_KEY'] = 'lythucstore_secret_key_2026'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dulieu.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Mật khẩu quản trị (Anh có thể đổi thành mật khẩu của anh ở đây)
ADMIN_USERNAME = "thuc"
ADMIN_PASSWORD = "1598thuc"

class SanPham(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(200), nullable=False)
    gia_cu = db.Column(db.String(50))
    gia_moi = db.Column(db.String(50), nullable=False)
    hinh_anh = db.Column(db.String(500), nullable=False)
    link_tiktok = db.Column(db.String(500))
    badge = db.Column(db.String(50))
    danh_muc = db.Column(db.String(50))

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    san_phams = SanPham.query.all()
    return render_template('index.html', san_phams=san_phams)

# Trang Đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('admin'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger')
    return render_template('login.html')

# Trang Đăng xuất
@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Đã đăng xuất!', 'info')
    return redirect(url_for('login'))

# Trang Quản trị Admin (Yêu cầu đăng nhập)
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    san_phams = SanPham.query.all()
    return render_template('admin.html', san_phams=san_phams)

@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    ten = request.form.get('ten')
    gia_cu = request.form.get('gia_cu')
    gia_moi = request.form.get('gia_moi')
    hinh_anh = request.form.get('hinh_anh')
    link_tiktok = request.form.get('link_tiktok')
    badge = request.form.get('badge')
    danh_muc = request.form.get('danh_muc')

    sp = SanPham(ten=ten, gia_cu=gia_cu, gia_moi=gia_moi, hinh_anh=hinh_anh, 
                 link_tiktok=link_tiktok, badge=badge, danh_muc=danh_muc)
    db.session.add(sp)
    db.session.commit()
    return redirect(url_for('admin'))

@app.route('/admin/delete/<int:id>')
def delete_product(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    sp = SanPham.query.get_or_404(id)
    db.session.delete(sp)
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '_main_':
    app.run(debug=True)