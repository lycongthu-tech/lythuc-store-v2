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