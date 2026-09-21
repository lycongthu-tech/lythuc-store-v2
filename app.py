from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import sqlite3
import time
import secrets
import cloudinary
import cloudinary.uploader
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-only-change-this-secret')
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'thuc')
ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH') or generate_password_hash(
    os.environ.get('ADMIN_PASSWORD', '123456')
)


def generate_csrf_token():
    if 'csrf_token' not in session:
        session['csrf_token'] = secrets.token_hex(32)
    return session['csrf_token']


@app.before_request
def validate_csrf():
    if request.method == 'POST' and request.endpoint in {'add_product', 'edit_product', 'delete_product'}:
        token = request.form.get('csrf_token')
        if not token or token != session.get('csrf_token'):
            flash('Phiên làm việc đã hết hạn hoặc request không hợp lệ.', 'error')
            return redirect(url_for('admin'))


cloudinary.config(
    cloud_name=(os.environ.get('CLOUDINARY_CLOUD_NAME') or '').strip(),
    api_key=(os.environ.get('CLOUDINARY_API_KEY') or '').strip(),
    api_secret=(os.environ.get('CLOUDINARY_API_SECRET') or '').strip(),
    secure=True
)

DATABASE_URL = (os.environ.get('DATABASE_URL') or '').strip().strip('"').strip("'") or None
IS_PRODUCTION = os.environ.get('RENDER') == 'true' or os.environ.get('FLASK_ENV') == 'production'
HAS_CLOUDINARY_CONFIG = all([
    (os.environ.get('CLOUDINARY_CLOUD_NAME') or '').strip(),
    (os.environ.get('CLOUDINARY_API_KEY') or '').strip(),
    (os.environ.get('CLOUDINARY_API_SECRET') or '').strip(),
])

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATABASE = os.path.join(app.root_path, 'dulieu.db')
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
        if not HAS_CLOUDINARY_CONFIG and IS_PRODUCTION:
            raise RuntimeError('Cloudinary chưa được cấu hình trên môi trường production.')
        result = cloudinary.uploader.upload(
            file_storage,
            folder='lythuc_store/products',
            resource_type='image'
        )
        return result.get('secure_url') or result.get('url')
    except Exception:
        if IS_PRODUCTION:
            app.logger.exception('Cloudinary upload failed')
            raise

        # Chỉ fallback local khi chạy development; filesystem Render không bền vững.
        name, ext = os.path.splitext(filename)
        unique_name = f"{int(time.time() * 1000)}_{name[:80]}{ext}"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_name)
        file_storage.save(file_path)
        return f"/static/uploads/{unique_name}"


def get_db_connection():
    if DATABASE_URL:
        postgres_url = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        return PostgresConnection(psycopg2.connect(postgres_url))

    if IS_PRODUCTION:
        raise RuntimeError('DATABASE_URL chưa được cấu hình trên môi trường production.')

    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    @staticmethod
    def _convert_placeholders(query):
        return query.replace('?', '%s')

    def execute(self, query, parameters=()):
        cursor = self.connection.cursor(cursor_factory=RealDictCursor)
        cursor.execute(self._convert_placeholders(query), parameters)
        return cursor

    def executemany(self, query, parameters):
        cursor = self.connection.cursor()
        cursor.executemany(self._convert_placeholders(query), parameters)
        return cursor

    def cursor(self):
        return self.connection.cursor(cursor_factory=RealDictCursor)

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    if DATABASE_URL:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS san_pham (
                id SERIAL PRIMARY KEY,
                ten TEXT NOT NULL,
                gia INTEGER NOT NULL,
                gia_cu INTEGER,
                anh TEXT NOT NULL,
                link_affiliate TEXT NOT NULL,
                danh_muc TEXT DEFAULT 'the-thao-nam',
                tag TEXT DEFAULT '-20%'
            )
        ''')
    else:
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

    if DATABASE_URL:
        cursor.execute(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'san_pham'"
        )
        existing_columns = [row['column_name'] for row in cursor.fetchall()]
    else:
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

    cursor.execute('SELECT COUNT(*) AS count FROM san_pham')
    count_row = cursor.fetchone()
    count = count_row['count'] if DATABASE_URL else count_row[0]
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
        conn.executemany('''
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
    search_query = request.args.get('q', '').strip()
    conn = get_db_connection()

    query = 'SELECT * FROM san_pham'
    conditions = []
    parameters = []
    if selected_category and selected_category != 'all':
        conditions.append('danh_muc = ?')
        parameters.append(selected_category)
    if search_query:
        conditions.append('LOWER(ten) LIKE LOWER(?)')
        parameters.append(f'%{search_query}%')
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    sp_db = conn.execute(query + ' ORDER BY id DESC', tuple(parameters)).fetchall()
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
        selected_category=selected_category,
        search_query=search_query
    )


@app.route('/api/search')
def search_products():
    search_query = request.args.get('q', '').strip()
    if not search_query:
        return jsonify([])

    conn = get_db_connection()
    rows = conn.execute('''
        SELECT id, ten, gia, anh
        FROM san_pham
        WHERE LOWER(ten) LIKE LOWER(?)
        ORDER BY id DESC
        LIMIT 8
    ''', (f'%{search_query}%',)).fetchall()
    conn.close()

    return jsonify([
        {
            'id': row['id'],
            'ten': row['ten'],
            'gia': format_gia(row['gia']),
            'anh': row['anh']
        }
        for row in rows
    ])


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        ten_dang_nhap = request.form.get('ten_dang_nhap')
        mat_khau = request.form.get('mat_khau')
        if ten_dang_nhap == ADMIN_USERNAME and check_password_hash(ADMIN_PASSWORD_HASH, mat_khau or ''):
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
    search_query = request.args.get('q', '').strip()
    conn = get_db_connection()
    query = 'SELECT * FROM san_pham'
    conditions = []
    parameters = []
    if selected_category and selected_category != 'all':
        conditions.append('danh_muc = ?')
        parameters.append(selected_category)
    if search_query:
        conditions.append('(LOWER(ten) LIKE LOWER(?) OR LOWER(link_affiliate) LIKE LOWER(?) OR LOWER(tag) LIKE LOWER(?))')
        parameters.extend([f'%{search_query}%'] * 3)
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    sp_db = conn.execute(query + ' ORDER BY id DESC', tuple(parameters)).fetchall()
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
        selected_category=selected_category,
        search_query=search_query,
        csrf_token=generate_csrf_token()
    )


@app.route('/admin/add', methods=['POST'])
def add_product():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = None
    try:
        ten = request.form.get('ten', '').strip()
        gia = int(request.form.get('gia', '').strip())
        gia_cu_input = request.form.get('gia_cu', '').strip()
        gia_cu = int(gia_cu_input) if gia_cu_input else int(gia * 1.25)
        link_affiliate = request.form.get('link_affiliate', '').strip()
        danh_muc = request.form.get('danh_muc', 'the-thao-nam')
        tag = request.form.get('tag', '').strip()

        if not ten or gia <= 0 or gia_cu <= 0 or not link_affiliate:
            raise ValueError('Vui lòng nhập đầy đủ tên, giá bán, giá cũ và link sản phẩm hợp lệ.')

        anh_url = request.form.get('anh', '').strip()
        anh_upload = save_uploaded_image(request.files.get('file_anh'))
        anh = anh_upload or anh_url or 'https://images.unsplash.com/photo-1521572267360-ee0c2909d518'

        conn = get_db_connection()
        conn.execute('''
            INSERT INTO san_pham (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag))
        conn.commit()
        flash('Đã thêm sản phẩm thành công.', 'success')
    except (ValueError, TypeError) as error:
        if conn:
            conn.rollback()
        flash(str(error), 'error')
    except psycopg2.Error:
        if conn:
            conn.rollback()
        app.logger.exception('PostgreSQL insert failed')
        flash('Không thể lưu sản phẩm vào PostgreSQL. Hãy kiểm tra DATABASE_URL.', 'error')
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception('Không thể thêm sản phẩm')
        flash('Không thể thêm sản phẩm. Hãy xem log Render để biết chi tiết.', 'error')
    finally:
        if conn:
            conn.close()

    return redirect(url_for('admin'))


@app.route('/admin/edit/<int:id>', methods=['POST'])
def edit_product(id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    conn = None
    try:
        ten = request.form.get('ten', '').strip()
        gia = int(request.form.get('gia', '').strip())
        gia_cu_input = request.form.get('gia_cu', '').strip()
        gia_cu = int(gia_cu_input) if gia_cu_input else 0
        link_affiliate = request.form.get('link_affiliate', '').strip()
        danh_muc = request.form.get('danh_muc', 'the-thao-nam')
        tag = request.form.get('tag', '').strip()

        if not ten or gia <= 0 or (gia_cu_input and gia_cu <= 0) or not link_affiliate:
            raise ValueError('Vui lòng nhập đầy đủ tên, giá bán và link sản phẩm hợp lệ.')

        anh_url = request.form.get('anh', '').strip()
        anh_upload = save_uploaded_image(request.files.get('file_anh'))
        anh = anh_upload or anh_url or request.form.get('anh_cu', '')
        if not anh:
            raise ValueError('Sản phẩm cần có ảnh hoặc URL ảnh.')

        conn = get_db_connection()
        conn.execute('''
            UPDATE san_pham
            SET ten = ?, gia = ?, gia_cu = ?, anh = ?, link_affiliate = ?, danh_muc = ?, tag = ?
            WHERE id = ?
        ''', (ten, gia, gia_cu, anh, link_affiliate, danh_muc, tag, id))
        conn.commit()
        flash('Đã cập nhật sản phẩm thành công.', 'success')
    except (ValueError, TypeError) as error:
        if conn:
            conn.rollback()
        flash(str(error), 'error')
    except psycopg2.Error:
        if conn:
            conn.rollback()
        app.logger.exception('PostgreSQL update failed')
        flash('Không thể cập nhật sản phẩm vào PostgreSQL. Hãy kiểm tra DATABASE_URL.', 'error')
    except Exception:
        if conn:
            conn.rollback()
        app.logger.exception('Không thể cập nhật sản phẩm')
        flash('Không thể cập nhật sản phẩm. Hãy xem log Render để biết chi tiết.', 'error')
    finally:
        if conn:
            conn.close()

    return redirect(url_for('admin'))


@app.route('/admin/delete/<int:id>', methods=['POST'])
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