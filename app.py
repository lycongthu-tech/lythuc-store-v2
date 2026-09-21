from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__)

# Cấu hình cơ sở dữ liệu SQLite
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'dulieu.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Model Sản Phẩm
class SanPham(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ten = db.Column(db.String(200), nullable=False)
    gia = db.Column(db.String(50), nullable=False)
    danh_muc = db.Column(db.String(100), nullable=True)
    link_affiliate = db.Column(db.String(500), nullable=False)
    anh = db.Column(db.Text, nullable=False)

# Hàm khởi tạo database
with app.app_context():
    db.create_all()

# 1. TRANG CHỦ
@app.route('/')
def trang_chu():
    ds_san_pham = SanPham.query.all()
    return render_template('index.html', san_pham=ds_san_pham)

# 2. TRANG QUẢN TRỊ (ADMIN)
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        ten_sp = request.form.get('ten')
        gia_sp = request.form.get('gia')
        danh_muc_sp = request.form.get('danh_muc')
        link_aff = request.form.get('link_affiliate')
        anh_sp = request.form.get('anh')

        sp_moi = SanPham(
            ten=ten_sp, 
            gia=gia_sp, 
            danh_muc=danh_muc_sp, 
            link_affiliate=link_aff, 
            anh=anh_sp
        )
        db.session.add(sp_moi)
        db.session.commit()
        return redirect(url_for('admin'))

    ds_san_pham = SanPham.query.all()
    return render_template('admin.html', san_pham=ds_san_pham)

# 3. XÓA SẢN PHẨM
@app.route('/admin/xoa/<int:id>')
def xoa_san_pham(id):
    sp = SanPham.query.get_or_404(id)
    db.session.delete(sp)
    db.session.commit()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)