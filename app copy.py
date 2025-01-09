from flask import Flask, render_template, session, url_for, request, redirect, jsonify, make_response
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
            session['id'] = account['id']  # Menyimpan ID pengguna ke session
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            pesan = "Sepertinya user / pass salah / akun tidak ada"
            return render_template('pages/login.html', pesan=pesan)

@app.route('/home', methods=['POST', 'GET'])
def home():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    if request.method == 'GET':
        cursor = db.cursor(dictionary=True)
        user_id = session['id']
        sql = 'SELECT * FROM dataset WHERE id_user = %s'
        cursor.execute(sql, (user_id,))
        results = cursor.fetchall()
        cursor.close()
        return render_template('pages/home.html', data=results)

    if request.method == 'POST':
        if 'preview' in request.form:
            file = request.files.get('file')
            kelas = request.form.get('kelas', '')
            jurusan = request.form.get('jurusan', '')
            semester = request.form.get('semester', '')
            tahun_awal = request.form.get('tahun_awal', '')
            tahun_akhir = request.form.get('tahun_akhir', '')
            tahun_ajaran = f"{tahun_awal}/{tahun_akhir}"

            # Simpan input form ke session agar tidak hilang setelah submit
            session['kelas'] = kelas
            session['jurusan'] = jurusan
            session['semester'] = semester
            session['tahun_awal'] = tahun_awal
            session['tahun_akhir'] = tahun_akhir

            if file:
                muat_data = io.StringIO(file.stream.read().decode('UTF-8'), newline=None)
                baca_csv = csv.reader(muat_data)
                next(baca_csv)

                preview_data = []
                for baris in baca_csv:
                    if len(baris) == 9:
                        preview_data.append({
                            'nis': baris[0],
                            'nama_siswa': baris[1],
                            'mapel1': baris[2],
                            'mapel2': baris[3],
                            'mapel3': baris[4],
                            'mapel4': baris[5],
                            'mapel5': baris[6],
                            'nilai_total': baris[7],
                            'rata_rata': baris[8],
                        })

                # Simpan preview_data ke session
                session['preview_data'] = preview_data

                return render_template('pages/home.html', preview_data=preview_data)

        elif 'simpan' in request.form:
            # Ambil data dari session
            preview_data = session.get('preview_data', [])
            kelas = session.get('kelas')
            jurusan = session.get('jurusan')
            semester = session.get('semester')
            tahun_awal = session.get('tahun_awal')
            tahun_ajaran = f"{tahun_awal}/{session.get('tahun_akhir')}"

            cursor = db.cursor()
            for baris in preview_data:
                sql = """INSERT INTO dataset (id_user, nis, nama_siswa, mapel1, mapel2, mapel3, 
                        mapel4, mapel5, nilai_total, rata_rata, kelas, jurusan, semester, tahun_ajaran) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                val = (session['id'], baris['nis'], baris['nama_siswa'], baris['mapel1'], baris['mapel2'], 
                       baris['mapel3'], baris['mapel4'], baris['mapel5'], baris['nilai_total'], 
                       baris['rata_rata'], kelas, jurusan, semester, tahun_ajaran)
                cursor.execute(sql, val)
            db.commit()
            cursor.close()

        elif 'cancel' in request.form:
            # Hapus data dari session jika cancel ditekan
            session.pop('preview_data', None)
            session.pop('kelas', None)
            session.pop('jurusan', None)
            session.pop('semester', None)
            session.pop('tahun_awal', None)
            session.pop('tahun_akhir', None)

    return redirect(url_for('home'))



@app.route('/hasil_analisis', methods=['GET'])
def hasil_analisis():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))
    
    # Query untuk mendapatkan semua data input dari user yang login
    cursor = db.cursor(dictionary=True)
    user_id = session['id']
    sql = '''SELECT MIN(id) AS id, kelas, jurusan, semester, tahun_ajaran 
             FROM dataset 
             WHERE id_user = %s 
             GROUP BY kelas, jurusan, semester, tahun_ajaran'''
    cursor.execute(sql, (user_id,))
    results = cursor.fetchall()
    cursor.close()

    # Kirim data ke template hasil_analisis.html untuk ditampilkan
    return render_template('pages/hasil_analisis.html', data=results, enumerate=enumerate)

# @app.route('/hitung_elbow',methods=['POST','GET'])
# def hitung_elbow():
#     if request.method == 'POST':
#         klaster = int(request.form['klaster'])

#         tarik_data = pd.read_sql('SELECT mapel1, mapel2, mapel3, mapel4, mapel5, nilai_total FROM dataset WHERE id_user = %s', db, params=(session['id'],))
#         wcss = []

#         for i in range(1, klaster+1):
#             kmeans = KMeans(n_clusters=i, n_init='auto')
#             kmeans.fit_predict(tarik_data)
#             wcss.append(kmeans.inertia_)
        
#         plt.plot(range(1, klaster+1), wcss, marker='o')
#         plt.ylabel('wcss')
#         plt.xlabel('Jumlah Klaster')
#         plt.title('Perhitungan Elbow')
#         stempel_waktu = datetime.now().strftime("%H-%M-%S")
#         nama_baru = stempel_waktu + 'plot.png'
#         plt.savefig(f'static/temp/{nama_baru}')
#         plt.close('all')
#         return render_template('pages/hasil_elbow.html', gambar=nama_baru)

@app.route('/klastering')
def klastering():
    info_data = 'Kosong'
    info_instruksi = 'Kosong'
    saran = 'Syarat Terpenuhi! Proses dapat Dilaksanakan'
    lanjut = False

    sqlan = 'SELECT parameter FROM instruksi ORDER BY id DESC'
    cursor = db.cursor(dictionary=False)
    cursor.execute(sqlan)
    sql_data = cursor.fetchall()[0][0]
    db.commit()

    if '%s' in sql_data:
        cursor.execute(sql_data, (session['id'],))
    else:
        cursor.execute(sql_data)  # Tidak ada parameter
    data = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    hasil_data = pd.DataFrame(data, columns=columns)

    sql_instruksi = "SELECT * FROM instruksi ORDER BY id DESC"
    cursor.execute(sql_instruksi)
    hasil_instruksi = cursor.fetchall()
    db.commit()

    sql_id = "SELECT id FROM dataset WHERE id_user = %s"
    cursor.execute(sql_id, (session['id'],))
    hasil_id = cursor.fetchall()
    db.commit()
    cursor.close()

    if len(hasil_data) > 0:
        info_data = 'Tersedia'
        lanjut = True
    else:
        info_data = 'Kosong'
        saran = '! Silahkan isi data yang kosong dahulu !'
        lanjut = False
    
    if len(hasil_instruksi) > 0:
        info_instruksi = 'Tersedia'
        lanjut = True
    else:
        info_instruksi = 'Kosong'
        saran = '! Silahkan isi data yang kosong dahulu !'
        lanjut = False

    if not lanjut:
        return render_template('pages/klastering.html', info_data=info_data, info_instruksi=info_instruksi, saran=saran)

    # Set langsung jumlah klaster dan iterasi
    permintaan_klaster = 3  # Set jumlah klaster yang diinginkan
    permintaan_iterasi = 10  # Set jumlah iterasi yang diinginkan

    kmeans = KMeans(n_clusters=permintaan_klaster, n_init='auto', max_iter=permintaan_iterasi)
    label = np.array(kmeans.fit_predict(hasil_data))

    dbi = davies_bouldin_score(hasil_data, kmeans.fit_predict(hasil_data))
    session['dbi'] = dbi

    for k, m in enumerate(hasil_id):
        cursor = db.cursor()
        sql = "UPDATE dataset SET cluster = %s WHERE id  = %s"
        val = (str(label[k]), str(m[0]))  # Sesuaikan indeks jika perlu
        cursor.execute(sql, val)
        db.commit()

    return render_template('pages/klastering.html', info_data=info_data, info_instruksi=info_instruksi, saran=saran)

@app.route('/hasil_klastering')
def hasil_klastering():
    # Dapatkan nilai dari request atau session
    kelas = request.args.get('kelas')
    jurusan = request.args.get('jurusan')
    semester = request.args.get('semester')
    tahun_ajaran = request.args.get('tahun_ajaran')

    # Simpan di session
    session['kelas'] = kelas
    session['jurusan'] = jurusan
    session['semester'] = semester
    session['tahun_ajaran'] = tahun_ajaran

    return render_template('pages/hasil_klastering.html', kelas=kelas, jurusan=jurusan, semester=semester, tahun_ajaran=tahun_ajaran)

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
    SELECT nis, nama_siswa, mapel1, mapel2, mapel3, mapel4, mapel5, nilai_total, rata_rata, cluster 
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
    sql = 'SELECT * FROM users'
    cursor.execute(sql)
    users_data = cursor.fetchall()
    cursor.close()
    return render_template('pages/users.html', users=users_data)

@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        jabatan = request.form['jabatan']
        role = request.form['role']
        
        cursor = db.cursor()
        sql = "INSERT INTO users (name, username, email, password, jabatan, role) VALUES (%s, %s, %s, %s, %s, %s)"
        val = (name, username, email, password, jabatan, role)
        cursor.execute(sql, val)
        db.commit()
        cursor.close()
        
        return redirect(url_for('users'))
    
    return render_template('pages/add_user.html')


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
    app.run(debug=True)
