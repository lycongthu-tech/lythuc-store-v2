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

# Danh sách 11 sản phẩm mẫu v1
du_lieu_v1 = [
    {
        "ten": "(Mua 3 giảm 10k tặng móc khoá) Áo Thun Unisex From Rộng Top Women",
        "gia": "89.000đ",
        "gia_cu": "140.000đ",
        "danh_muc": "the-thao-nu",
        "tag": "Lượt mua 127k",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhtpBg81aX-I6p9s/",
        "anh": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lzxbv3atd8i558.webp"
    },
    {
        "ten": "Bộ Đồ Đùi Thể Thao Nữ NQ Có Túi Kéo, Gym, Yoga, Chạy Bộ, Mặc Nhà",
        "gia": "89.000đ",
        "gia_cu": "140.000đ",
        "danh_muc": "the-thao-nu",
        "tag": "-36%",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhpyXqkUpR-VFFsR/",
        "anh": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lynof44a080xc7.webp"
    },
    {
        "ten": "Áo Thun Nén Gym Nam - Dài Tay Cao Cấp",
        "gia": "109.000đ",
        "gia_cu": "169.000đ",
        "danh_muc": "the-thao-nam",
        "tag": "Hàng Việt",
        "link_affiliate": "https://vt.tiktok.com/ZS9AroE8UMsfw-ydKK6/",
        "anh": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-louoqxybyqyzf2.webp"
    },
    {
        "ten": "Găng Tay Tập Gym Chống Trượt Bảo Vệ Tay",
        "gia": "12x.000đ",
        "gia_cu": "200.000đ",
        "danh_muc": "phu-kien",
        "tag": "Chính hãng",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhxJcV9y7a-9vJhC/",
        "anh": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lyetjvzf69whe0.webp"
    },
    {
        "ten": "Thảm Tập Gym Yoga Chống Trượt Giảm Chấn",
        "gia": "225.000đ",
        "gia_cu": "350.000đ",
        "danh_muc": "phu-kien",
        "tag": "mall",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhQa7MJMBa-BPWUt/",
        "anh": "https://down-vn.img.susercontent.com/file/sg-11134201-820nt-mnavz44ql6v91d.webp"
    },
    {
        "ten": "Quần Jogger Thể Thao Nam vải poly cao cấp",
        "gia": "140.000đ",
        "gia_cu": "179.000đ",
        "danh_muc": "the-thao-nam",
        "tag": "Hàng Việt",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhC5Moeddf-WlmzF/",
        "anh": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lpc25e8dopce45.webp"
    },
    {
        "ten": "Áo 3 Lỗ Thun Gân, Co Giãn Thoáng Mát",
        "gia": "52.000đ",
        "gia_cu": "150.000đ",
        "danh_muc": "the-thao-nam",
        "tag": "-65%",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhXFoEKkpq-VVSPv/",
        "anh": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcT2arFvo8BmKG7VYBJMXXNFc-QrF0fB49LcvEFsI0JvuQCVDr6G"
    },
    {
        "ten": "Áo Thun Thể Thao Nam Fron Ôm, Thun Lạnh Cao Cấp",
        "gia": "95.000đ",
        "gia_cu": "149.000đ",
        "danh_muc": "the-thao-nam",
        "tag": "-36%",
        "link_affiliate": "https://vt.tiktok.com/ZS9Ahq3tcdLfB-i2kKQ/",
        "anh": "https://down-vn.img.susercontent.com/file/vn-11134207-7qukw-lhyfmy2e4mo164.webp"
    },
    {
        "ten": "Sữa Dinh Dưỡng Muscle Mass Gainer 12lbs, WHEYSTORE",
        "gia": "2.890.000đ",
        "gia_cu": "3.200.000đ",
        "danh_muc": "whey-tpbs",
        "tag": "Giảm 300k",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhnEJxHYHk-Q7j5m/",
        "anh": "https://www.wheystore.vn/images/products/2023/12/14/large/inforgraphic-muscle-mass-gainer-12lbs_1702548078.jpg.webp"
    },
    {
        "ten": "Viên Kẽm AMAGAIN bổ sung kẽm Chelamax Bisglycinate",
        "gia": "152.000đ",
        "gia_cu": "175.000đ",
        "danh_muc": "whey-tpbs",
        "tag": "Hơn 400k lượt mua",
        "link_affiliate": "https://vt.tiktok.com/ZS9Ah7QRcrLQ1-TVFV9/",
        "anh": "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSlxZv08rKht6wDB9mEAgl1ukLBQmGvzUQDxH85D7qJVw&s=10"
    },
    {
        "ten": "Bộ Đồ Đùi Thể Thao Nữ NQ Có Túi Kéo, Gym, Yoga, Chạy Bộ, Mặc Nhà",
        "gia": "89.000đ",
        "gia_cu": "140.000đ",
        "danh_muc": "the-thao-nu",
        "tag": "-36%",
        "link_affiliate": "https://vt.tiktok.com/ZS9AhpyXqkUpR-VFFsR/",
        "anh": "https://down-vn.img.susercontent.com/file/vn-11134207-7r98o-lynof44a080xc7.webp"
    }
]

# Khởi tạo CSDL và tự động nạp dữ liệu nếu CSDL đang trống
with app.app_context():
    db.create_all()
    if SanPham.query.count() == 0:
        for item in du_lieu_v1:
            sp = SanPham(
                ten=item["ten"],
                gia=item["gia"],
                gia_cu=item.get("gia_cu", ""),
                danh_muc=item.get("danh_muc", ""),
                tag=item.get("tag", ""),
                link_affiliate=item["link_affiliate"],
                anh=item["anh"]
            )
            db.session.add(sp)
        db.session.commit()

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
        
        # Anh chỉnh Tên đăng nhập & Mật khẩu ở dòng này:
        if ten_dang_nhap == 'thuc' and mat_khau == '123456':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            return render_template('login.html', error="Tên đăng nhập hoặc mật khẩu không chính xác!")
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