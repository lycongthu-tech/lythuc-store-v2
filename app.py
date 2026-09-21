from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'lythucstore_secret_key'

DATABASE = 'dulieu.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS san_pham (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ten TEXT NOT NULL,
            gia INTEGER NOT NULL,
            gia_cu INTEGER,
            anh TEXT NOT NULL,
            link_affiliate TEXT NOT NULL,
            danh_muc TEXT DEFAULT 'the-thao-nam',
            tag TEXT DEFAULT '-20%'
        )
    ''')
    
    # Kiểm tra xem bảng có đang trống hay không để tự động nạp lại 11 sản phẩm mẫu
    cursor.execute('SELECT COUNT(*) FROM san_pham')
    count = cursor.fetchone()[0]
    if count == 0:
        san_pham_mau = [
            ("Áo Thun Thể Thao Nam Vải Poly Cao Cấp", 89000, 120000, "https://images.unsplash.com/photo-1581655353564-df123a1eb820", "https://vt.tiktok.com/", "the-thao-nam", "-25%"),
            ("Quần Short Gym Nam Có Túi Kéo Khóa", 99000, 150000, "https://images.unsplash.com/photo-1517445312882-bc9910d016b7", "https://vt.tiktok.com/", "the-thao-nam", "-33%"),
            ("Áo Khoác Chạy Bộ Nam - Dài Tay Cao Cấp", 169000, 220000, "https://images.unsplash.com/photo-1556905055-8f358a7a47b2", "https://vt.tiktok.com/", "the-thao-nam", "-23%"),
            ("Bộ Quần Áo Tập Gym Nam Thể Thao Mùa Hè", 199000, 280000, "https://images.unsplash.com/photo-1534438327276-14e5300c3a48", "https://vt.tiktok.com/", "the-thao-nam", "-28%"),
            ("Áo Tập Yoga Nữ Không Gọng Tôn Dáng", 89000, 130000, "https://images.unsplash.com/photo-1518310383802-640c2de311b2", "https://vt.tiktok.com/", "the-thao-nu", "-31%"),
            ("Quần Legging Nữ Cạp Cao Nâng Mông", 109000, 160000, "https://images.unsplash.com/photo-1506126613408-eca07ce68773", "https://vt.tiktok.com/", "the-thao-nu", "-31%"),
            ("Áo Khoác Gió Thể Thao Nữ Chống Nước Nhẹ", 159000, 220000, "https://images.unsplash.com/photo-1544367567-0f2fcb009e0b", "https://vt.tiktok.com/", "the-thao-nu", "-27%"),
            ("Băng Quấn Cổ Tay Tập Gym Chống Trượt", 45000, 70000, "https://images.unsplash.com/photo-1584735935682-2f2b69dff9d2", "https://vt.tiktok.com/", "the-thao-nu", "-35%"),
            ("Đai Lưng Tập Gym Bảo Vệ Cột Sống", 225000, 320000, "https://images.unsplash.com/photo-1517838277536-f5f99be501cd", "https://vt.tiktok.com/", "phu-kien", "-30%"),
            ("Thảm Tập Yoga Cao Su Non Chống Trượt", 140000, 200000, "https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f", "https://vt.tiktok.com/", "phu-kien", "-30%"),
            ("Bột Whey Protein Hỗ Trợ Tăng Cơ Giảm Mỡ", 650000, 850000, "https://images.unsplash.com/photo-1579722883378-7634e4096053", "https://vt.tiktok.com/", "whey-tpbs", "-23%")
        ]
        cursor.executemany('''
            INSERT INTO san_pham (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', san_pham_mau)
        conn.commit()
        
    conn.close()

init_db()

def format_gia(gia):
    if not gia:
        return ""
    return "{:,}đ".format(int(gia)).replace(",", ".")

@app.route('/')
def index():
    conn = get_db_connection()
    sp_db = conn.execute('SELECT * FROM san_pham').fetchall()
    conn.close()
    
    danh_sach_san_pham = []
    for item in sp_db:
        gia_moi = item['gia']
        gia_cu = item['gia_cu'] if item['gia_cu'] else int(gia_moi * 1.25)
        phan_tram_giam = int(round((1 - (gia_moi / gia_cu)) * 100)) if gia_cu > 0 else 0
        
        danh_sach_san_pham.append({
            'id': item['id'],
            'ten': item['ten'],
            'gia': format_gia(gia_moi),
            'gia_cu': format_gia(gia_cu),
            'giam_gia': f"-{phan_tram_giam}%",
            'anh': item['anh'],
            'link_affiliate': item['link_affiliate'],
            'danh_muc': item['danh_muc'],
            'tag': item['tag'] if item['tag'] else f"-{phan_tram_giam}%"
        })
        
    return render_template('index.html', san_pham=danh_sach_san_pham)

# ĐĂNG NHẬP ADMIN
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        ten_dang_nhap = request.form['username']
        mat_khau = request.form['password']
        if ten_dang_nhap == 'thuc' and mat_khau == '123456':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

# TRANG QUẢN TRỊ ADMIN
@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    sp_db = conn.execute('SELECT * FROM san_pham ORDER BY id DESC').fetchall()
    conn.close()
    
    danh_sach = []
    for item in sp_db:
        danh_sach.append({
            'id': item['id'],
            'ten': item['ten'],
            'gia': item['gia'],
            'gia_cu': item['gia_cu'] if item['gia_cu'] else int(item['gia'] * 1.25),
            'gia_formatted': format_gia(item['gia']),
            'gia_cu_formatted': format_gia(item['gia_cu']) if item['gia_cu'] else format_gia(int(item['gia'] * 1.25)),
            'anh': item['anh'],
            'link_affiliate': item['link_affiliate'],
            'danh_muc': item['danh_muc'],
            'tag': item['tag']
        })
    
    return render_template('admin.html', san_pham=danh_sach)

# THÊM SẢN PHẨM MỚI
@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    ten = request.form['ten']
    gia = int(request.form['gia'])
    gia_cu_input = request.form.get('gia_cu')
    gia_cu = int(gia_cu_input) if gia_cu_input else int(gia * 1.25)
    anh = request.form['anh']
    link_affiliate = request.form['link_affiliate']
    danh_muc = request.form['danh_muc']
    tag = request.form.get('tag', '-20%')
    
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO san_pham (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

# CẬP NHẬT / SỬA SẢN PHẨM (MỚI THÊM)
@app.route('/admin/edit/<int:id>', methods=['POST'])
def edit_product(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    ten = request.form['ten']
    gia = int(request.form['gia'])
    gia_cu_input = request.form.get('gia_cu')
    gia_cu = int(gia_cu_input) if gia_cu_input else int(gia * 1.25)
    anh = request.form['anh']
    link_affiliate = request.form['link_affiliate']
    danh_muc = request.form['danh_muc']
    tag = request.form.get('tag', '-20%')
    
    conn = get_db_connection()
    conn.execute('''
        UPDATE san_pham
        SET ten = ?, gia = ?, gia_cu = ?, anh = ?, link_affiliate = ?, danh_muc = ?, tag = ?
        WHERE id = ?
    ''', (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag, id))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

# XOÁ SẢN PHẨM
@app.route('/admin/delete/<int:id>')
def delete_product(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    conn.execute('DELETE FROM san_pham WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)