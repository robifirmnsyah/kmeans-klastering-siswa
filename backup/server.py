from flask import Flask, render_template, session, url_for, request, redirect, jsonify, make_response,flash, send_from_directory
from datetime import datetime
import mysql.connector as connection
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from fpdf import FPDF
plt.switch_backend('agg')
from sklearn.metrics import davies_bouldin_score

app = Flask(__name__)

app.secret_key = 'admin'

db = connection.connect(
    host="localhost",
    user="admin",
    password="admin123",
    database="klastering_siswa"
)

@app.route('/')
def index():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))
    return redirect(url_for('home'))

# Login route modification
@app.route('/login', methods=['POST', 'GET'])
def login():
    pesan = None  # Set pesan to None initially
    if request.method == 'GET':
        if session.get('sudah_login'):
            return redirect(url_for('home'))
        return render_template('pages/login.html', pesan=pesan)
    
    if request.method == 'POST':
        identifier = request.form['username']  # Bisa berupa username atau nip
        password = request.form['password']
        cursor = db.cursor(dictionary=True)
        
        # Query untuk mencocokkan username atau nip dengan password
        sql = 'SELECT * FROM users WHERE (username = %s OR nip = %s) AND password = %s'
        cursor.execute(sql, (identifier, identifier, password))
        account = cursor.fetchone()
        cursor.close()
        
        if account:
            session['sudah_login'] = True
            session['nip'] = account['nip']
            session['username'] = account['username']
            session['nama'] = account['nama']  # Tambahkan baris ini untuk menyimpan nama
            session['role'] = account['role']
            return redirect(url_for('home'))
        else:
            pesan = "Sepertinya user / pass salah / akun tidak ada"
            return render_template('pages/login.html', pesan=pesan)

@app.route('/dashboard')
def dashboard():
    cursor = db.cursor(dictionary=True)

    # Query untuk mendapatkan total siswa dan jumlah per klaster hanya untuk jurusan Rekayasa Perangkat Lunak
    cursor.execute("SELECT COUNT(*) AS total_siswa FROM dataset WHERE jurusan = 'Rekayasa Perangkat Lunak'")
    total_siswa = cursor.fetchone()['total_siswa']

    cursor.execute("SELECT COUNT(*) AS jumlah FROM dataset WHERE cluster = 1 AND jurusan = 'Rekayasa Perangkat Lunak'")
    jumlah_klaster_1 = cursor.fetchone()['jumlah']

    cursor.execute("SELECT COUNT(*) AS jumlah FROM dataset WHERE cluster = 2 AND jurusan = 'Rekayasa Perangkat Lunak'")
    jumlah_klaster_2 = cursor.fetchone()['jumlah']

    cursor.execute("SELECT COUNT(*) AS jumlah FROM dataset WHERE cluster = 3 AND jurusan = 'Rekayasa Perangkat Lunak'")
    jumlah_klaster_3 = cursor.fetchone()['jumlah']

    # Data untuk grafik 5 tahun terakhir
    current_year = datetime.now().year
    years = [f"{year}/{year+1}" for year in range(current_year - 4, current_year + 1)]
    data_per_tahun = {}
    for tahun in years:
        cursor.execute(
            """
            SELECT cluster, COUNT(*) AS jumlah_siswa
            FROM dataset
            WHERE tahun_ajaran = %s
            GROUP BY cluster
            """, (tahun,)
        )
        results = cursor.fetchall()
        data_per_tahun[tahun] = {row['cluster']: row['jumlah_siswa'] for row in results}

    # Ambil semua id jurusan
    cursor.execute("SELECT id FROM jurusan")
    all_jurusan_ids = [row['id'] for row in cursor.fetchall()]

    # Inisialisasi data_per_jurusan dengan semua id jurusan
    data_per_jurusan = {str(jurusan_id): {'1': 0, '2': 0, '3': 0} for jurusan_id in all_jurusan_ids}

    # Query untuk mendapatkan jumlah siswa per klaster berdasarkan jurusan
    cursor.execute(
        """
        SELECT jurusan.id AS jurusan_id, dataset.cluster, COUNT(*) AS jumlah_siswa
        FROM dataset
        JOIN jurusan ON dataset.jurusan = jurusan.nama_jurusan  -- sesuaikan kondisi join dengan struktur tabel Anda
        GROUP BY jurusan.id, dataset.cluster
        """
    )

    # Isi data_per_jurusan dengan hasil query
    for row in cursor.fetchall():
        jurusan_id = str(row['jurusan_id'])
        data_per_jurusan[jurusan_id][str(row['cluster'])] = row['jumlah_siswa']


    data_per_jurusan_str = {str(key): value for key, value in data_per_jurusan.items()}  # Ubah jurusan key ke string

    cursor.close()

    # Kirim data ke template
    return render_template(
        'pages/dashboard.html',
        total_siswa=total_siswa,
        jumlah_klaster_1=jumlah_klaster_1,
        jumlah_klaster_2=jumlah_klaster_2,
        jumlah_klaster_3=jumlah_klaster_3,
        data_per_tahun=data_per_tahun,
        years=years,
        data_per_jurusan=data_per_jurusan_str
    )



@app.route('/home', methods=['POST', 'GET'])
def home():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    user_id = session['nip']

    # Ambil data kelas dari tabel users
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT kelas FROM users WHERE nip = %s', (user_id,))
    user_info = cursor.fetchone()
    cursor.close()

    if user_info is None:
        return "User not found", 404

    # Ambil id_jurusan dari kelas
    kelas = user_info['kelas']
    id_jurusan = kelas.split()[1]  # Mengambil bagian kedua dari kelas sebagai id_jurusan

    # Ambil nama jurusan dari tabel jurusan
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT nama_jurusan FROM jurusan WHERE id = %s', (id_jurusan,))
    jurusan_info = cursor.fetchone()
    cursor.close()

    nama_jurusan = jurusan_info['nama_jurusan'] if jurusan_info else 'Unknown Jurusan'

    # Mengambil data mata pelajaran berdasarkan kelas
    kelas_id = ' '.join(kelas.split()[:-1])  # Menghilangkan angka di akhir kelas
    cursor = db.cursor(dictionary=True)
    cursor.execute('SELECT * FROM mata_pelajaran WHERE id = %s', (kelas_id,))
    mapel_data = cursor.fetchone()
    cursor.close()

    if request.method == 'GET':
        cursor = db.cursor(dictionary=True)
        sql = 'SELECT * FROM dataset WHERE id_user = %s'
        cursor.execute(sql, (user_id,))
        results = cursor.fetchall()
        cursor.close()

        return render_template('pages/home.html', data=results, kelas=kelas, nama_jurusan=nama_jurusan, mapel=mapel_data)

    if request.method == 'POST':
        if 'preview' in request.form:
            file = request.files.get('file')
            jurusan = request.form.get('jurusan', '')
            semester = request.form.get('semester', '')
            tahun_awal = request.form.get('tahun_awal', '')
            tahun_akhir = request.form.get('tahun_akhir', '')
            tahun_ajaran = f"{tahun_awal}/{tahun_akhir}"

            # Simpan input form ke session
            session['jurusan'] = jurusan
            session['semester'] = semester
            session['tahun_awal'] = tahun_awal
            session['tahun_akhir'] = tahun_akhir
            session['tahun_ajaran'] = tahun_ajaran  # Tambahkan ini agar bisa dipakai di fungsi klastering

            preview_data = []

            if file.filename.endswith('.xlsx') or file.filename.endswith('.xls'):
                # Convert Excel file to DataFrame
                excel_data = pd.read_excel(file)

                # Debugging: Print actual column names
                print(excel_data.columns)  # Check what columns are actually loaded

                # Renaming columns based on the Excel data
                excel_data.columns = ['nis', 'nama_siswa', 'mapel1', 'mapel2', 'mapel3', 'mapel4']

                # Check if we have the expected number of columns
                if len(excel_data.columns) < 6:
                    flash("File format tidak dikenali atau kolom tidak sesuai!", "error")
                    return redirect(url_for('home'))  # Handle error

                preview_data = []
                
                # Process the data rows from the DataFrame
                for index, row in excel_data.iterrows():
                    # Convert nilai to float and compute rata-rata and total
                    nilai_mapel = list(map(float, [row['mapel1'], row['mapel2'], row['mapel3'], row['mapel4']]))  # Only 4 subjects
                    rata_rata = sum(nilai_mapel) / len(nilai_mapel)  # Calculate average

                    preview_data.append({
                        'nis': row['nis'],
                        'nama_siswa': row['nama_siswa'],
                        'mapel1': row['mapel1'],
                        'mapel2': row['mapel2'],
                        'mapel3': row['mapel3'],
                        'mapel4': row['mapel4'],
                        'rata_rata': round(rata_rata, 2)  # Store average rounded to 2 decimal places
                    })

                session['preview_data'] = preview_data

                return render_template('pages/home.html', preview_data=preview_data, kelas=kelas, nama_jurusan=nama_jurusan, mapel=mapel_data)


        if 'simpan' in request.form:
            preview_data = session.get('preview_data', [])
            jurusan = nama_jurusan  # Gunakan nama_jurusan yang diambil sebelumnya
            semester = session.get('semester')
            tahun_awal = session.get('tahun_awal')
            tahun_ajaran = f"{tahun_awal}/{session.get('tahun_akhir')}"

            # Langkah 1: Ambil data mata pelajaran yang relevan untuk klastering
            mapel_data_for_clustering = []
            for baris in preview_data:
                mapel_data_for_clustering.append([
                    baris['mapel1'], baris['mapel2'], baris['mapel3'], 
                    baris['mapel4']  # Hanya 4 mapel
                ])

            try:
                # Langkah 2: Proses klastering menggunakan KMeans
                kmeans = KMeans(n_clusters=3, n_init='auto', max_iter=300, random_state=123)
                labels = kmeans.fit_predict(mapel_data_for_clustering)

                # Tambahkan hasil klastering (label) ke preview_data
                for i, baris in enumerate(preview_data):
                    baris['cluster'] = int(labels[i]) + 1

                cursor = db.cursor()

                # Langkah 3: Simpan data ke database setelah klastering
                for baris in preview_data:
                    sql = """INSERT INTO dataset (id_user, nis, nama_siswa, kelas, mapel1, mapel2, mapel3, 
                            mapel4, rata_rata, jurusan, semester, tahun_ajaran, cluster) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

                    
                    val = (session['nip'], baris['nis'], baris['nama_siswa'], kelas, baris['mapel1'], 
                        baris['mapel2'], baris['mapel3'], baris['mapel4'],
                        baris['rata_rata'], jurusan, semester, tahun_ajaran, baris['cluster'])
                    
                    cursor.execute(sql, val)

                db.commit()
                flash("Data berhasil disimpan dengan hasil klastering", "success")
            except Exception as e:
                db.rollback()
                print(f"Terjadi kesalahan: {str(e)}")
                flash(f"Terjadi kesalahan: {str(e)}", "error")
            finally:
                cursor.close()

            session['success_message'] = 'Data berhasil disimpan dengan hasil klastering!'
            
            return redirect(url_for('hasil_analisis'))

        elif 'cancel' in request.form:
            session.pop('preview_data', None)

            return redirect(url_for('home'))

@app.route('/download-template')
def download_template():
    return send_from_directory(directory='sample', path='template.csv', as_attachment=True)

@app.route('/hasil_analisis', methods=['GET'])
def hasil_analisis():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))
    
    # Dapatkan role dari session
    role = session.get('role')
    
    # Query untuk mendapatkan data berdasarkan role
    cursor = db.cursor(dictionary=True)
    
    if role == 'admin':
        # Admin melihat seluruh data siswa
        sql = '''SELECT MIN(id) AS id, kelas, jurusan, semester, tahun_ajaran 
                 FROM dataset 
                 GROUP BY kelas, jurusan, semester, tahun_ajaran'''
        cursor.execute(sql)
    else:
        # User melihat data yang mereka input sendiri
        user_id = session['nip']
        sql = '''SELECT MIN(id) AS id, kelas, jurusan, semester, tahun_ajaran 
                 FROM dataset 
                 WHERE id_user = %s 
                 GROUP BY kelas, jurusan, semester, tahun_ajaran'''
        cursor.execute(sql, (user_id,))
    
    results = cursor.fetchall()
    cursor.close()

    # Kirim data ke template hasil_analisis.html untuk ditampilkan
    return render_template('pages/hasil_analisis.html', data=results, enumerate=enumerate)


@app.route('/delete_hasil_analisis', methods=['POST'])
def delete_hasil_analisis():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    # Get data from the form submission
    id_user = request.form.get('id_user')
    kelas = request.form.get('kelas')
    jurusan = request.form.get('jurusan')
    semester = request.form.get('semester')
    tahun_ajaran = request.form.get('tahun_ajaran')

    # Prepare SQL to delete the records matching the provided values
    cursor = db.cursor()
    try:
        sql = """DELETE FROM dataset 
                 WHERE id_user = %s 
                 AND kelas = %s 
                 AND jurusan = %s 
                 AND semester = %s 
                 AND tahun_ajaran = %s"""
        val = (id_user, kelas, jurusan, semester, tahun_ajaran)
        cursor.execute(sql, val)
        db.commit()
        flash("Data berhasil dihapus", "success")
    except Exception as e:
        db.rollback()
        flash(f"Terjadi kesalahan: {str(e)}", "error")
    finally:
        cursor.close()

    return redirect(url_for('hasil_analisis'))

@app.route('/hasil_klastering')
def hasil_klastering():
    # Ambil informasi dari session atau query string
    kelas = request.args.get('kelas')
    jurusan = request.args.get('jurusan')
    semester = request.args.get('semester')
    tahun_ajaran = request.args.get('tahun_ajaran')

    session['kelas'] = kelas
    session['jurusan'] = jurusan
    session['semester'] = semester
    session['tahun_ajaran'] = tahun_ajaran

    # Ambil data klastering dari database untuk ditampilkan
    cursor = db.cursor(dictionary=True)
    sql = '''SELECT * FROM dataset WHERE kelas = %s AND jurusan = %s AND semester = %s AND tahun_ajaran = %s'''
    cursor.execute(sql, (kelas, jurusan, semester, tahun_ajaran))
    hasil_klaster = cursor.fetchall()
    
    # Mengambil data mata pelajaran berdasarkan kelas (sama dengan di home)
    kelas_id = ' '.join(kelas.split()[:-1])  # Menghilangkan angka di akhir kelas
    cursor.execute('SELECT * FROM mata_pelajaran WHERE id = %s', (kelas_id,))
    mapel_data = cursor.fetchone()
    
    cursor.close()

    return render_template('pages/hasil_klastering.html', data=hasil_klaster, kelas=kelas, jurusan=jurusan, semester=semester, tahun_ajaran=tahun_ajaran, mapel=mapel_data)

@app.route('/jumlah_klaster')
def jumlah_klaster():
    kelas = request.args.get('kelas')
    jurusan = request.args.get('jurusan')
    semester = request.args.get('semester')
    tahun_ajaran = request.args.get('tahun_ajaran')

    sql_query = """
    SELECT 
        cluster, 
        COUNT(*) AS jumlah, 
        COALESCE(AVG(mapel1), 0) AS rata_rata_mapel1,
        COALESCE(AVG(mapel2), 0) AS rata_rata_mapel2,
        COALESCE(AVG(mapel3), 0) AS rata_rata_mapel3,
        COALESCE(AVG(mapel4), 0) AS rata_rata_mapel4
    FROM dataset 
    WHERE kelas = %s AND jurusan = %s AND semester = %s AND tahun_ajaran = %s
    GROUP BY cluster
    """

    cursor = db.cursor(dictionary=True)
    cursor.execute(sql_query, (kelas, jurusan, semester, tahun_ajaran))
    data = cursor.fetchall()
    cursor.close()  # Close the cursor after finishing

    return jsonify({
        'label': [row['cluster'] for row in data],
        'jumlah': [row['jumlah'] for row in data],
        'rata_rata_mapel1': [float(row['rata_rata_mapel1']) for row in data],
        'rata_rata_mapel2': [float(row['rata_rata_mapel2']) for row in data],
        'rata_rata_mapel3': [float(row['rata_rata_mapel3']) for row in data],
        'rata_rata_mapel4': [float(row['rata_rata_mapel4']) for row in data]
    })


@app.route('/download_pdf')
def download_pdf():
    # Ambil data klastering dari MySQL dengan filter cluster 0 hingga 2 dan urutkan berdasarkan cluster
    kelas = request.args.get('kelas')
    jurusan = request.args.get('jurusan')
    semester = request.args.get('semester')
    tahun_ajaran = request.args.get('tahun_ajaran')

    cursor = db.cursor(dictionary=True)
    sql = '''SELECT nis, nama_siswa, mapel1, mapel2, mapel3, mapel4, rata_rata, cluster 
             FROM dataset 
             WHERE kelas = %s AND jurusan = %s AND semester = %s AND tahun_ajaran = %s
             AND cluster BETWEEN 1 AND 3
             ORDER BY cluster ASC'''  # Tambahkan klausa ORDER BY untuk mengurutkan data berdasarkan cluster
    cursor.execute(sql, (kelas, jurusan, semester, tahun_ajaran))
    hasil_klaster = cursor.fetchall()
    cursor.close()

    # Buat PDF
    pdf = FPDF()
    pdf.add_page()

    # Judul
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="Hasil Analisa dan Clustering (Cluster 0 - 2)", ln=True, align='C')

    # Informasi kelas, jurusan, dll.
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Kelas: {kelas}", ln=True)
    pdf.cell(200, 10, txt=f"Jurusan: {jurusan}", ln=True)
    pdf.cell(200, 10, txt=f"Semester: {semester}", ln=True)
    pdf.cell(200, 10, txt=f"Tahun Ajaran: {tahun_ajaran}", ln=True)

    # Spasi antara judul dan tabel
    pdf.ln(10)

    # Membuat header tabel
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(20, 10, 'NIS', 1)
    pdf.cell(50, 10, 'Nama Siswa', 1)  # Lebarkan kolom Nama Siswa
    pdf.cell(15, 10, 'Mapel 1', 1)
    pdf.cell(15, 10, 'Mapel 2', 1)
    pdf.cell(15, 10, 'Mapel 3', 1)
    pdf.cell(15, 10, 'Mapel 4', 1)
    pdf.cell(20, 10, 'Rata-rata', 1)  # Kolom Rata-rata langsung dari dataset
    pdf.cell(20, 10, 'Cluster', 1)
    pdf.ln()

    # Menambahkan data ke tabel
    pdf.set_font("Arial", size=10)
    for row in hasil_klaster:
        pdf.cell(20, 10, str(row['nis']), 1)

        # Menggunakan MultiCell untuk nama_siswa agar otomatis turun ke baris baru jika panjang
        x, y = pdf.get_x(), pdf.get_y()
        pdf.multi_cell(50, 10, row['nama_siswa'], border=1)
        pdf.set_xy(x + 50, y)  # Pindahkan posisi ke kolom berikutnya setelah multi_cell

        pdf.cell(15, 10, str(row['mapel1']), 1)
        pdf.cell(15, 10, str(row['mapel2']), 1)
        pdf.cell(15, 10, str(row['mapel3']), 1)
        pdf.cell(15, 10, str(row['mapel4']), 1)
        pdf.cell(20, 10, str(row['rata_rata']), 1)  # Ambil rata-rata langsung dari kolom
        pdf.cell(20, 10, str(row['cluster']), 1)
        pdf.ln()

    # Simpan PDF ke response dan buat agar langsung diunduh
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=hasil_klastering.pdf'  # Ganti ke attachment untuk langsung download

    return response


@app.route('/anggota_klaster')
def anggota_klaster():
    cluster = request.args.get('cluster')
    kelas = session.get('kelas')
    jurusan = session.get('jurusan')
    semester = session.get('semester')
    tahun_ajaran = session.get('tahun_ajaran')

    # Query untuk mengambil siswa berdasarkan cluster
    cursor = db.cursor(dictionary=True)
    sql = '''SELECT nis, nama_siswa, mapel1, mapel2, mapel3, mapel4, cluster 
             FROM dataset 
             WHERE kelas = %s AND jurusan = %s AND semester = %s AND tahun_ajaran = %s AND cluster = %s'''
    cursor.execute(sql, (kelas, jurusan, semester, tahun_ajaran, cluster))
    anggota_klaster = cursor.fetchall()
    cursor.close()

    return jsonify(anggota_klaster)

@app.route('/users')
def users():
    if not session.get('sudah_login') or session.get('role') != 'admin':
        flash("Anda tidak memiliki izin untuk mengakses halaman ini", "error")
        return redirect(url_for('home'))

    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    return render_template('pages/users.html', users=users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nip = request.form['nip']
        nama = request.form['nama']
        kelas = request.form['kelas']
        role = request.form['role']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        cursor = db.cursor()
        sql = "INSERT INTO users (nip, nama, kelas, role, username, email, password) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        val = (nip, nama, kelas, role, username, email, password)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        
        success_message = "Berhasil Menambahkan User!"
        return render_template('pages/add_user.html', success_message=success_message)

    return render_template('pages/add_user.html', success_message=None)

@app.route('/delete_user', methods=['POST'])
def delete_user():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    # Dapatkan user_id dari form, sekarang ini adalah nip
    user_id = request.form.get('user_id')

    cursor = db.cursor()
    try:
        # Hapus user berdasarkan nip
        sql = "DELETE FROM users WHERE nip = %s"
        cursor.execute(sql, (user_id,))
        db.commit()
        flash("Pengguna berhasil dihapus", "success")
    except Exception as e:
        db.rollback()
        flash(f"Terjadi kesalahan: {str(e)}", "error")
    finally:
        cursor.close()

    return redirect(url_for('users'))

@app.route('/edit_user/<user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)

    # Mengambil data user berdasarkan NIP (user_id)
    cursor.execute("SELECT * FROM users WHERE nip = %s", (user_id,))
    user = cursor.fetchone()

    if request.method == 'POST':
        nip = request.form['nip']
        nama = request.form['nama']
        kelas = request.form['kelas']
        role = request.form['role']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Update data user
        sql = """
        UPDATE users 
        SET nip = %s, nama = %s, kelas = %s, role = %s, username = %s, email = %s, password = %s 
        WHERE nip = %s
        """
        val = (nip, nama, kelas, role, username, email, password, user_id)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()

        return redirect(url_for('users'))

    return render_template('pages/edit_user.html', user=user)

@app.route('/logout')
def logout():
    pesan = 'anda logout'
    session.pop('sudah_login', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login',pesan = pesan))

if __name__ == "__main__":
    app.run(port=8080, debug=True)