from flask import Flask, render_template, session, url_for, request, redirect, jsonify, make_response,flash
import csv, io
import mysql.connector as connection
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
plt.switch_backend('agg')
from datetime import datetime
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

@app.route('/login', methods=['POST', 'GET'])
def login():
    pesan = 'akun tidak ada'
    if request.method == 'GET':
        if session.get('sudah_login'):
            return redirect(url_for('home'))
        return render_template('pages/login.html', pesan=pesan)
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor = db.cursor(dictionary=True)
        sql = 'SELECT * FROM users WHERE username = %s AND password = %s'
        cursor.execute(sql, (username, password))
        account = cursor.fetchone()
        cursor.close()
        
        if account:
            session['sudah_login'] = True
            session['nip'] = account['nip']  # Menyimpan ID pengguna ke session
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            pesan = "Sepertinya user / pass salah / akun tidak ada"
            return render_template('pages/login.html', pesan=pesan)

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

            if file:
                muat_data = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
                baca_csv = csv.reader(muat_data)
                next(baca_csv)
                for baris in baca_csv:
                    preview_data.append({
                        'nis': baris[0],
                        'nama_siswa': baris[1],
                        'mapel1': baris[2],
                        'mapel2': baris[3],
                        'mapel3': baris[4],
                        'mapel4': baris[5],
                        'mapel5': baris[6],
                        'nilai_total': baris[7],
                        'rata_rata': baris[8]
                    })

                session['preview_data'] = preview_data

            return render_template('pages/home.html', preview_data=preview_data, kelas=kelas, nama_jurusan=nama_jurusan, mapel=mapel_data)

        if 'simpan' in request.form:
            preview_data = session.get('preview_data', [])
            jurusan = nama_jurusan  # Gunakan nama_jurusan yang diambil sebelumnya
            semester = session.get('semester')
            tahun_awal = session.get('tahun_awal')
            tahun_ajaran = f"{tahun_awal}/{session.get('tahun_akhir')}"

            cursor = db.cursor()

            try:
                for baris in preview_data:
                    sql = """INSERT INTO dataset (id_user, nis, nama_siswa, kelas, mapel1, mapel2, mapel3, 
                            mapel4, mapel5, nilai_total, rata_rata, jurusan, semester, tahun_ajaran) 
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    val = (session['nip'], baris['nis'], baris['nama_siswa'], kelas, baris['mapel1'], baris['mapel2'],
                            baris['mapel3'], baris['mapel4'], baris['mapel5'], baris['nilai_total'],
                            baris['rata_rata'], jurusan, semester, tahun_ajaran)
                    cursor.execute(sql, val)

                db.commit()
                flash("Data berhasil disimpan", "success")
            except Exception as e:
                db.rollback()
                flash(f"Terjadi kesalahan: {str(e)}", "error")
            finally:
                cursor.close()

            session['success_message'] = 'Data berhasil disimpan!'

            # Redirect ke klastering setelah simpan
            return redirect(url_for('klastering'))

        elif 'cancel' in request.form:
            session.pop('preview_data', None)  # Hapus data preview dari session

            # Return setelah cancel
            return redirect(url_for('home'))

@app.route('/klastering')
def klastering():
    info_data = 'Kosong'
    info_instruksi = 'Kosong'
    saran = 'Syarat Terpenuhi! Proses dapat Dilaksanakan'
    lanjut = False

    # Ambil data instruksi terbaru
    sql_instruksi = "SELECT * FROM instruksi ORDER BY id DESC LIMIT 1"
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql_instruksi)
    hasil_instruksi = cursor.fetchone()
    cursor.close()  # Pastikan cursor ditutup setelah query

    if hasil_instruksi:
        info_instruksi = 'Tersedia'
        permintaan_klaster = hasil_instruksi['kluster']
        permintaan_iterasi = hasil_instruksi['iterasi']
        parameter = hasil_instruksi['parameter']
        lanjut = True
    else:
        info_instruksi = 'Kosong'
        saran = '! Silahkan isi instruksi yang kosong dahulu !'
        lanjut = False

    # Ambil parameter filter dari session atau instruksi (misalnya disimpan saat upload data)
    kelas = session.get('kelas', None)
    jurusan = session.get('jurusan', None)
    semester = session.get('semester', None)
    tahun_ajaran = session.get('tahun_ajaran', None)

    if not all([kelas, jurusan, semester, tahun_ajaran]):
        saran = '! Filter data belum lengkap, silakan lengkapi data upload terlebih dahulu !'
        lanjut = False

    # Query untuk mendapatkan data dari dataset berdasarkan parameter instruksi dan filter
    sql_data = """
        SELECT mapel1, mapel2, mapel3, mapel4, mapel5 
        FROM dataset 
        WHERE kelas = %s AND jurusan = %s AND semester = %s AND tahun_ajaran = %s
    """
    cursor = db.cursor(dictionary=True)  # Buat cursor baru
    cursor.execute(sql_data, (kelas, jurusan, semester, tahun_ajaran))
    hasil_data = cursor.fetchall()  # Ambil semua hasil query sebelum menjalankan query lain
    cursor.close()  # Tutup cursor setelah query selesai

    # Konversi hasil_data menjadi dataframe
    df = pd.DataFrame(hasil_data)

    # Query untuk mengambil id dataset
    sql_id = """
        SELECT id 
        FROM dataset 
        WHERE kelas = %s AND jurusan = %s AND semester = %s AND tahun_ajaran = %s
    """
    cursor = db.cursor(dictionary=True)  # Buat cursor baru
    cursor.execute(sql_id, (kelas, jurusan, semester, tahun_ajaran))
    hasil_id = cursor.fetchall()
    cursor.close()  # Tutup cursor setelah query selesai

    if not df.empty:
        info_data = 'Tersedia'
        lanjut = True
    else:
        info_data = 'Kosong'
        saran = '! Silahkan isi data yang kosong dahulu !'
        lanjut = False

    if not lanjut:
        return render_template('pages/klastering.html', info_data=info_data, info_instruksi=info_instruksi, saran=saran)

    # Proses klastering menggunakan KMeans
    kmeans = KMeans(n_clusters=permintaan_klaster, n_init='auto', max_iter=permintaan_iterasi)
    label = np.array(kmeans.fit_predict(df))

    # Hitung Davies-Bouldin Index (DBI) untuk menilai kualitas klaster
    dbi = davies_bouldin_score(df, label)
    session['dbi'] = dbi  # Simpan nilai DBI ke session untuk ditampilkan nanti

    # Simpan hasil klastering ke database
    cursor = db.cursor()  # Buat cursor baru untuk query update
    for k, m in enumerate(hasil_id):
        sql_update = "UPDATE dataset SET cluster = %s WHERE id = %s"
        val = (str(label[k]), str(m['id']))
        cursor.execute(sql_update, val)
    db.commit()
    cursor.close()  # Tutup cursor setelah query selesai
    
    flash(f"Klastering selesai dengan DBI: {dbi}", "success")
    return redirect(url_for('hasil_analisis'))


@app.route('/hasil_analisis', methods=['GET'])
def hasil_analisis():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))
    
    # Query untuk mendapatkan semua data input dari user yang login
    cursor = db.cursor(dictionary=True)
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
    cursor.close()

    return render_template('pages/hasil_klastering.html', data=hasil_klaster, kelas=kelas, jurusan=jurusan, semester=semester, tahun_ajaran=tahun_ajaran)

@app.route('/jumlah_klaster')
def jumlah_klaster():
    kelas = request.args.get('kelas')
    jurusan = request.args.get('jurusan')
    semester = request.args.get('semester')
    tahun_ajaran = request.args.get('tahun_ajaran')

    sql_query = """
    SELECT cluster, COUNT(*) as jumlah 
    FROM dataset 
    WHERE kelas = %s AND jurusan = %s AND semester = %s AND tahun_ajaran = %s
    GROUP BY cluster
    """
    cursor = db.cursor(dictionary=True)
    cursor.execute(sql_query, (kelas, jurusan, semester, tahun_ajaran))
    data = cursor.fetchall()
    return jsonify({
        'label': [row['cluster'] for row in data],
        'jumlah': [row['jumlah'] for row in data]
    })

@app.route('/cek_per_cluster/<id>')
def cek_per_cluster(id):
    user_id = session.get('id')
    if not user_id:
        return redirect(url_for('login'))

    # Ambil parameter tambahan dari session atau request
    kelas = session.get('kelas')
    jurusan = session.get('jurusan')
    semester = session.get('semester')
    tahun_ajaran = session.get('tahun_ajaran')

    cursor = db.cursor(dictionary=True)
    sql = """
    SELECT nis, nama_siswa, mapel1, mapel2, nilai_binggris, nilai_ipa, nilai_ips, nilai_total, rata_rata, cluster 
    FROM dataset 
    WHERE cluster=%s AND id_user=%s AND kelas=%s AND jurusan=%s AND semester=%s AND tahun_ajaran=%s
    """
    cursor.execute(sql, (id, user_id, kelas, jurusan, semester, tahun_ajaran))
    data = cursor.fetchall()
    
    return make_response(jsonify(data))


@app.route('/dbi')
def dbi():
    hasil_dbi = session.get('dbi')
    return render_template('pages/dbi.html',data=hasil_dbi)

@app.route('/users')
def users():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

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
        
        return redirect(url_for('users'))
    
    return render_template('pages/add_user.html')

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

@app.route('/about')
def about():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))
    return render_template('pages/about.html')
    

@app.route('/logout')
def logout():
    pesan = 'anda logout'
    session.pop('sudah_login', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login',pesan = pesan))

if __name__ == "__main__":
    app.run(port=8080, debug=True)