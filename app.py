from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
import os
import sqlite3
import time
import cloudinary
import cloudinary.uploader

app = Flask(__name__)
app.secret_key = 'lythucstore_secret_key_2026'

cloudinary.config(
    cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
    api_key=os.environ.get('CLOUDINARY_API_KEY'),
    api_secret=os.environ.get('CLOUDINARY_API_SECRET'),
    secure=True
)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = 'dulieu.db'
CATEGORY_LABELS = {
    'all': 'Tất cả',
    'the-thao-nam': 'Thể thao nam',
    'the-thao-nu': 'Thể thao nữ',
    'phu-kien': 'Phụ kiện & dụng cụ',
    'whey-tpbs': 'Whey / Thực phẩm bổ sung'
}


def save_uploaded_image(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    filename = secure_filename(file_storage.filename)
    if not filename:
        return None

    try:
        result = cloudinary.uploader.upload(
            file_storage,
            folder='lythuc_store/products',
            resource_type='image'
        )
        return result.get('secure_url') or result.get('url')
    except Exception:
        # Fallback to local upload nếu Cloudinary chưa được cấu hình
        name, ext = os.path.splitext(filename)
        unique_name = f"{int(time.time() * 1000)}_{name[:80]}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file_storage.save(file_path)
        return f"/static/uploads/{unique_name}"


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

    existing_columns = [row[1] for row in cursor.execute('PRAGMA table_info(san_pham)').fetchall()]
    for column_name, column_type in [
        ('gia_cu', 'INTEGER'),
        ('link_affiliate', 'TEXT'),
        ('danh_muc', 'TEXT'),
        ('tag', 'TEXT'),
    ]:
        if column_name not in existing_columns:
            try:
                cursor.execute(f'ALTER TABLE san_pham ADD COLUMN {column_name} {column_type}')
                conn.commit()
            except Exception:
                pass

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
    return '{:,}đ'.format(int(gia)).replace(',', '.')


@app.route('/')
def index():
    selected_category = request.args.get('danh_muc', 'all')
    conn = get_db_connection()

    if selected_category and selected_category != 'all':
        sp_db = conn.execute('SELECT * FROM san_pham WHERE danh_muc = ? ORDER BY id DESC', (selected_category,)).fetchall()
    else:
        sp_db = conn.execute('SELECT * FROM san_pham ORDER BY id DESC').fetchall()
    conn.close()

    san_pham = []
    for item in sp_db:
        gia_moi = item['gia']
        gia_cu = item['gia_cu'] if item['gia_cu'] else int(gia_moi * 1.25)
        phan_tram_giam = int(round((1 - (gia_moi / gia_cu)) * 100)) if gia_cu > 0 else 0
        raw_tag = (item['tag'] or '').strip()
        tag_text = raw_tag if raw_tag else f'-{phan_tram_giam}%'
        san_pham.append({
            'id': item['id'],
            'ten': item['ten'],
            'gia_formatted': format_gia(gia_moi),
            'gia_cu_formatted': format_gia(gia_cu),
            'giam_gia': f'-{phan_tram_giam}%',
            'tag': tag_text,
            'anh': item['anh'],
            'link_affiliate': item['link_affiliate'],
            'danh_muc': item['danh_muc'],
            'tag_style': 'sale' if raw_tag and raw_tag.startswith('-') else 'custom'
        })

    return render_template(
        'index.html',
        san_pham=san_pham,
        danh_muc_options=CATEGORY_LABELS,
        selected_category=selected_category
    )


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        ten_dang_nhap = request.form.get('ten_dang_nhap')
        mat_khau = request.form.get('mat_khau')
        if ten_dang_nhap == 'thuc' and mat_khau == '123456':
            session['logged_in'] = True
            return redirect(url_for('admin'))
        error = 'Tên đăng nhập hoặc mật khẩu không đúng!'
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/admin')
def admin():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    selected_category = request.args.get('danh_muc', 'all')
    conn = get_db_connection()
    if selected_category and selected_category != 'all':
        sp_db = conn.execute('SELECT * FROM san_pham WHERE danh_muc = ? ORDER BY id DESC', (selected_category,)).fetchall()
    else:
        sp_db = conn.execute('SELECT * FROM san_pham ORDER BY id DESC').fetchall()
    conn.close()

    danh_sach = []
    for item in sp_db:
        row = dict(item)
        gia_val = row.get('gia', 0)
        gia_cu_val = row.get('gia_cu')
        danh_sach.append({
            'id': row.get('id'),
            'ten': row.get('ten', ''),
            'gia': gia_val,
            'gia_cu': gia_cu_val if gia_cu_val else 0,
            'gia_formatted': format_gia(gia_val),
            'gia_cu_formatted': format_gia(gia_cu_val) if gia_cu_val else '',
            'anh': row.get('anh', ''),
            'link_affiliate': row.get('link_affiliate', ''),
            'danh_muc': row.get('danh_muc', ''),
            'tag': row.get('tag', '')
        })

    return render_template(
        'admin.html',
        san_pham=danh_sach,
        danh_muc_options=CATEGORY_LABELS,
        selected_category=selected_category
    )


@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    ten = request.form['ten']
    gia = int(request.form['gia'])
    gia_cu_input = request.form.get('gia_cu')
    gia_cu = int(gia_cu_input) if gia_cu_input else int(gia * 1.25)
    link_affiliate = request.form.get('link_affiliate', '')
    danh_muc = request.form.get('danh_muc', 'the-thao-nam')
    tag = request.form.get('tag', '-20%')

    anh_url = request.form.get('anh', '').strip()
    anh_upload = save_uploaded_image(request.files.get('file_anh'))
    anh = anh_upload or anh_url or 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518'

    conn = get_db_connection()
    conn.execute('''
        INSERT INTO san_pham (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag))
    conn.commit()
    conn.close()

    return redirect(url_for('admin'))


@app.route('/admin/edit/<int:id>', methods=['POST'])
def edit_product(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    ten = request.form['ten']
    gia = int(request.form['gia'])
    gia_cu_input = request.form.get('gia_cu')
    gia_cu = int(gia_cu_input) if gia_cu_input else 0
    link_affiliate = request.form.get('link_affiliate', '')
    danh_muc = request.form.get('danh_muc', 'the-thao-nam')
    tag = request.form.get('tag', '')

    anh_url = request.form.get('anh', '').strip()
    anh_upload = save_uploaded_image(request.files.get('file_anh'))
    if anh_upload:
        anh = anh_upload
    elif anh_url:
        anh = anh_url
    else:
        anh = request.form.get('anh_cu', '')

    conn = get_db_connection()
    conn.execute('''
        UPDATE san_pham
        SET ten = ?, gia = ?, gia_cu = ?, anh = ?, link_affiliate = ?, danh_muc = ?, tag = ?
        WHERE id = ?
    ''', (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag, id))
    conn.commit()
    conn.close()

    return redirect(url_for('admin'))


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
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))