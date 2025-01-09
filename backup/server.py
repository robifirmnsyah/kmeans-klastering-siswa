from flask import Flask, render_template, session, url_for, request, redirect, jsonify, make_response,flash, send_from_directory
from datetime import datetime
from decimal import Decimal
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

@app.route('/dashboard', methods=['GET'])
def dashboard():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    
    # Set default values if not provided
    selected_jurusan = request.args.get('jurusan', 'Desain Komunikasi Visual')
    selected_kelas = request.args.get('id_kelas', 'X')
    selected_semester = request.args.get('semester', '')
    selected_tahun = request.args.get('tahun_ajaran', '')
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    # Get unique jurusan and tahun_ajaran
    cursor.execute('SELECT DISTINCT nama_jurusan FROM jurusan ORDER BY nama_jurusan')
    jurusan_list = cursor.fetchall()
    
    cursor.execute('SELECT DISTINCT tahun_ajaran FROM tahun_ajaran ORDER BY tahun_ajaran DESC')
    tahun_list = cursor.fetchall()

    # Base query
    base_sql = '''
        SELECT ds.nis, ds.nama_siswa, ds.kelas, ns.nilai_mapel1 AS mapel1, ns.nilai_mapel2 AS mapel2, 
               ns.nilai_mapel3 AS mapel3, ns.nilai_mapel4 AS mapel4, ns.cluster, ns.semester, ta.tahun_ajaran
        FROM data_siswa ds
        JOIN nilai_siswa ns ON ds.nis = ns.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
    '''
    params = []

    # Add filters
    where_clauses = []
    if selected_kelas:
        where_clauses.append('ds.id_kelas = %s')  # Changed from LIKE to exact match
        params.append(selected_kelas)  # Remove the % wildcards
    if selected_jurusan:
        where_clauses.append('ds.jurusan = %s')
        params.append(selected_jurusan)
    if selected_semester:
        where_clauses.append('ns.semester = %s')
        params.append(selected_semester)
    if selected_tahun:
        where_clauses.append('ta.tahun_ajaran = %s')
        params.append(selected_tahun)
        
    if where_clauses:
        base_sql += ' WHERE ' + ' AND '.join(where_clauses)
        
    base_sql += ' LIMIT %s OFFSET %s'
    params.extend([per_page, offset])
    
    cursor.execute(base_sql, tuple(params))
    siswa_data = cursor.fetchall()

    # Get total count for pagination
    count_sql = 'SELECT COUNT(*) as total FROM data_siswa ds JOIN nilai_siswa ns ON ds.nis = ns.nis JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta'
    if where_clauses:
        count_sql += ' WHERE ' + ' AND '.join(where_clauses)
    cursor.execute(count_sql, tuple(params[:-2]))  # Exclude LIMIT and OFFSET params
    total_records = cursor.fetchone()['total']
    total_pages = (total_records + per_page - 1) // per_page

    # Add filters for all queries
    base_where_clauses = []
    base_params = []
    if selected_kelas:
        base_where_clauses.append('ds.id_kelas = %s')  # Changed from LIKE to exact match
        base_params.append(selected_kelas)  # Remove the % wildcards
    if selected_jurusan:
        base_where_clauses.append('ds.jurusan = %s')
        base_params.append(selected_jurusan)
    if selected_semester:
        base_where_clauses.append('ns.semester = %s')
        base_params.append(selected_semester)
    if selected_tahun:
        base_where_clauses.append('ta.tahun_ajaran = %s')
        base_params.append(selected_tahun)

    # Base WHERE clause for all queries
    base_where = ''
    if base_where_clauses:
        base_where = 'WHERE ' + ' AND '.join(base_where_clauses)

    # Get total students with filters
    count_sql = f'''
        SELECT COUNT(DISTINCT ds.nis) as total 
        FROM data_siswa ds
        JOIN nilai_siswa ns ON ds.nis = ns.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
        {base_where}
    '''
    cursor.execute(count_sql, tuple(base_params))
    total_siswa = cursor.fetchone()['total']

    # Get cluster counts with filters
    cluster_sql = f'''
        SELECT ns.cluster, COUNT(DISTINCT ds.nis) as jumlah
        FROM nilai_siswa ns
        JOIN data_siswa ds ON ns.nis = ds.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
        {base_where}
        GROUP BY ns.cluster
    '''
    cursor.execute(cluster_sql, tuple(base_params))
    cluster_counts = {row['cluster']: row['jumlah'] for row in cursor.fetchall()}
    
    jumlah_klaster_1 = cluster_counts.get(1, 0)
    jumlah_klaster_2 = cluster_counts.get(2, 0)
    jumlah_klaster_3 = cluster_counts.get(3, 0)

    # Get average scores per cluster with filters
    avg_sql = f'''
        SELECT cluster, 
               AVG(nilai_mapel1) AS avg_mapel1, 
               AVG(nilai_mapel2) AS avg_mapel2, 
               AVG(nilai_mapel3) AS avg_mapel3, 
               AVG(nilai_mapel4) AS avg_mapel4
        FROM nilai_siswa ns
        JOIN data_siswa ds ON ns.nis = ds.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
        {base_where}
        GROUP BY cluster
        ORDER BY cluster
    '''
    cursor.execute(avg_sql, tuple(base_params))
    avg_mapel_per_cluster = cursor.fetchall()

    # Process data for template
    processed_data = {
        "mapel1": {"cluster1": None, "cluster2": None, "cluster3": None},
        "mapel2": {"cluster1": None, "cluster2": None, "cluster3": None},
        "mapel3": {"cluster1": None, "cluster2": None, "cluster3": None},
        "mapel4": {"cluster1": None, "cluster2": None, "cluster3": None},
    }
    for row in avg_mapel_per_cluster:
        cluster_key = f"cluster{row['cluster']}"
        processed_data["mapel1"][cluster_key] = row['avg_mapel1']
        processed_data["mapel2"][cluster_key] = row['avg_mapel2']
        processed_data["mapel3"][cluster_key] = row['avg_mapel3']
        processed_data["mapel4"][cluster_key] = row['avg_mapel4']

    # Get mapel data
    cursor.execute('SELECT * FROM mata_pelajaran')
    mapel_data = cursor.fetchall()
    mapel = {f"mapel{i+1}": mapel_data[i][f"mapel{i+1}"] for i in range(4)}

    # Get data for the last 5 years
    base_where_chart = ''
    if base_where_clauses:
        base_where_chart = 'WHERE ' + ' AND '.join(base_where_clauses)

    chart_sql = f'''
        WITH last_five_years AS (
            SELECT tahun_ajaran, id_ta
            FROM tahun_ajaran
            ORDER BY tahun_ajaran DESC
            LIMIT 5
        )
        SELECT lfy.tahun_ajaran, ns.cluster, COUNT(DISTINCT ds.nis) as jumlah
        FROM last_five_years lfy
        LEFT JOIN nilai_siswa ns ON ns.id_ta = lfy.id_ta
        LEFT JOIN data_siswa ds ON ds.nis = ns.nis
        LEFT JOIN tahun_ajaran ta ON ta.id_ta = ns.id_ta
        {base_where_chart}
        GROUP BY lfy.tahun_ajaran, ns.cluster
        ORDER BY lfy.tahun_ajaran ASC
    '''

    # Get all years from tahun_ajaran table first
    cursor.execute('''
        SELECT tahun_ajaran 
        FROM tahun_ajaran 
        ORDER BY tahun_ajaran DESC 
        LIMIT 5
    ''')
    all_years = [row['tahun_ajaran'] for row in cursor.fetchall()]

    # Process data for chart with all years
    years = sorted(all_years)  # Get all 5 years
    data_per_tahun = {year: {1: 0, 2: 0, 3: 0} for year in years}  # Initialize with zeros

    # Execute chart query with parameters
    cursor.execute(chart_sql, tuple(base_params))
    data_per_tahun_raw = cursor.fetchall()

    # Fill in actual data where it exists
    for row in data_per_tahun_raw:
        if row['cluster'] is not None:  # Check if there's actual cluster data
            data_per_tahun[row['tahun_ajaran']][row['cluster']] = row['jumlah']

    # Get id for mata_pelajaran
    if selected_kelas and selected_jurusan:
        # Get id_jurusan for selected jurusan
        cursor.execute('SELECT id_jurusan FROM jurusan WHERE nama_jurusan = %s', (selected_jurusan,))
        jurusan_result = cursor.fetchone()
        if jurusan_result:
            id_jurusan = jurusan_result['id_jurusan']
            mapel_id = f"{selected_kelas} {id_jurusan}"
        else:
            mapel_id = None
    else:
        mapel_id = None
    
    # Get mapel data with correct id
    if mapel_id:
        cursor.execute('SELECT * FROM mata_pelajaran WHERE id = %s', (mapel_id,))
        mapel_data = cursor.fetchone()
        if mapel_data:
            mapel = {}
            for i in range(1, 5):
                mapel_key = f"mapel{i}"
                mapel[mapel_key] = mapel_data[mapel_key] if mapel_data[mapel_key] else f"Mapel {i}"
        else:
            mapel = {f"mapel{i}": f"Mapel {i}" for i in range(1, 5)}
    else:
        mapel = {f"mapel{i}": f"Mapel {i}" for i in range(1, 5)}

    cursor.close()

    return render_template('pages/dashboard.html', 
                           siswa_data=siswa_data, 
                           jurusan_list=jurusan_list, 
                           tahun_list=tahun_list, 
                           selected_jurusan=selected_jurusan, 
                           selected_kelas=selected_kelas, 
                           selected_semester=selected_semester, 
                           selected_tahun=selected_tahun, 
                           total_siswa=total_siswa, 
                           jumlah_klaster_1=jumlah_klaster_1, 
                           jumlah_klaster_2=jumlah_klaster_2, 
                           jumlah_klaster_3=jumlah_klaster_3, 
                           processed_data=processed_data, 
                           page=page, 
                           total_pages=total_pages,
                           mapel=mapel,
                           years=years,
                           data_per_tahun=data_per_tahun)

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
    cursor.execute('SELECT nama_jurusan FROM jurusan WHERE id_jurusan = %s', (id_jurusan,))  # Changed from id to id_jurusan
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
        sql = 'SELECT * FROM data_siswa WHERE nip = %s'
        cursor.execute(sql, (user_id,))
        results = cursor.fetchall()
        cursor.close()

        return render_template('pages/home.html', data=results, kelas=kelas, nama_jurusan=nama_jurusan, mapel=mapel_data)

    if request.method == 'POST':
        if 'preview' in request.form:
            preview_data = []
            file = request.files.get('file')
            semester = request.form.get('semester', '')
            tahun_awal = request.form.get('tahun_awal', '')
            tahun_akhir = request.form.get('tahun_akhir', '')

            # Store data in session
            session['preview_data'] = preview_data
            session['kelas'] = kelas  # Store user's class
            session['jurusan'] = nama_jurusan  # Store user's major name
            session['semester'] = semester
            session['tahun_awal'] = tahun_awal
            session['tahun_akhir'] = tahun_akhir

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
                print(f"Debug - Jurusan: {nama_jurusan}")
                return render_template('pages/home.html', 
                                    preview_data=preview_data, 
                                    kelas=kelas,
                                    nama_jurusan=nama_jurusan,
                                    mapel=mapel_data)
                                    
        if 'simpan' in request.form:
            cursor = db.cursor(dictionary=True)
            try:
                # Get session data
                preview_data = session.get('preview_data', [])
                semester = session.get('semester')
                tahun_awal = session.get('tahun_awal')
                tahun_ajaran = f"{tahun_awal}/{session.get('tahun_akhir')}"
                id_ta = f"TA{tahun_awal}{session.get('tahun_akhir')}"
                kelas = session.get('kelas')
                
                # Get id_kelas and id_jurusan
                id_kelas = kelas.split()[0]
                id_jurusan = kelas.split()[1]
                id_mapel = f"{id_kelas} {id_jurusan}"
                
                # Insert tahun_ajaran if not exists
                cursor.execute("INSERT IGNORE INTO tahun_ajaran (id_ta, tahun_ajaran) VALUES (%s, %s)", 
                            (id_ta, tahun_ajaran))
                
                # Get nama_jurusan from jurusan table
                cursor.execute('SELECT nama_jurusan FROM jurusan WHERE id = %s', (id_jurusan,))
                jurusan_info = cursor.fetchone()
                if not jurusan_info:
                    raise Exception(f"Jurusan with id {id_jurusan} not found")
                nama_jurusan = jurusan_info['nama_jurusan']
                
                print(f"Debug - kelas: {kelas}")
                print(f"Debug - id_kelas: {id_kelas}")
                print(f"Debug - id_jurusan: {id_jurusan}")
                print(f"Debug - nama_jurusan: {nama_jurusan}")
                print(f"Debug - id_mapel: {id_mapel}")
                print(f"Debug - id_ta: {id_ta}")

                # Process clustering...
                mapel_data_for_clustering = []
                for data in preview_data:
                    mapel_data_for_clustering.append([
                        float(data['mapel1']), 
                        float(data['mapel2']), 
                        float(data['mapel3']), 
                        float(data['mapel4'])
                    ])

                X = np.array(mapel_data_for_clustering)
                kmeans = KMeans(n_clusters=3, n_init=10, max_iter=300, random_state=123)
                clusters = kmeans.fit_predict(X)

                # Insert data
                for idx, data in enumerate(preview_data):
                    # Insert into data_siswa if not exists
                    cursor.execute("SELECT nis FROM data_siswa WHERE nis = %s", (data['nis'],))
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO data_siswa (nip, nis, nama_siswa, kelas, jurusan, id_kelas) 
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (
                            session['nip'],
                            data['nis'],
                            data['nama_siswa'],
                            kelas,
                            nama_jurusan,
                            id_kelas
                        ))
                        print(f"Debug - Inserted student: {data['nis']}")

                    # Insert into nilai_siswa
                    cursor.execute("""
                        INSERT INTO nilai_siswa 
                        (nis, id_mapel, nilai_mapel1, nilai_mapel2, nilai_mapel3, nilai_mapel4, 
                        cluster, semester, id_ta) 
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (
                        data['nis'],
                        id_mapel,
                        float(data['mapel1']),
                        float(data['mapel2']),
                        float(data['mapel3']),
                        float(data['mapel4']),
                        int(clusters[idx]) + 1,
                        semester,
                        id_ta
                    ))
                    print(f"Debug - Inserted nilai: {data['nis']}")

                db.commit()
                flash('Data berhasil disimpan!', 'success')
                return redirect(url_for('hasil_analisis'))

            except Exception as e:
                db.rollback()
                flash(f'Error: {str(e)}', 'error')
                print(f"Debug - Final error: {str(e)}")
                return redirect(url_for('home'))
            finally:
                cursor.close()
    
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
    
    cursor = db.cursor(dictionary=True)
    role = session.get('role')
    user_id = session['nip']
    
    # Get user's class if role is user
    user_kelas = None
    if role == 'user':
        cursor.execute('SELECT kelas FROM users WHERE nip = %s', (user_id,))
        user_info = cursor.fetchone()
        if user_info:
            user_kelas = user_info['kelas']
    
    # Get filter parameters
    selected_kelas = request.args.get('kelas', '')
    selected_jurusan = request.args.get('jurusan', '')
    selected_semester = request.args.get('semester', '')
    selected_tahun = request.args.get('tahun_ajaran', '')
    
    # Get unique kelas (X, XI, XII) for dropdown
    kelas_list = [
        {'id_kelas': 'X'},
        {'id_kelas': 'XI'},
        {'id_kelas': 'XII'}
    ]

    semester_list = [
        {'semester': 'Ganjil'},
        {'semester': 'Genap'}
    ]
    
    # Get unique jurusan and tahun_ajaran
    cursor.execute('SELECT DISTINCT jurusan FROM data_siswa ORDER BY jurusan')
    jurusan_list = cursor.fetchall()
    
    cursor.execute('SELECT DISTINCT tahun_ajaran FROM tahun_ajaran ORDER BY tahun_ajaran DESC')
    tahun_list = cursor.fetchall()
    
    # Base query
    base_sql = '''SELECT ds.kelas, ds.jurusan, ns.semester, ta.tahun_ajaran 
                  FROM data_siswa ds
                  JOIN nilai_siswa ns ON ds.nis = ns.nis
                  JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta'''
    params = []

    # Add filters
    where_clauses = []
    
    # If user role, restrict to user's class
    if role == 'user':
        where_clauses.append('ds.kelas = %s')
        params.append(user_kelas)
    else:
        # Admin can filter by class
        if selected_kelas:
            where_clauses.append('ds.id_kelas = %s')
            params.append(selected_kelas)
    
    if selected_jurusan:
        where_clauses.append('ds.jurusan = %s')
        params.append(selected_jurusan)
    if selected_semester:
        where_clauses.append('ns.semester = %s')
        params.append(selected_semester)
    if selected_tahun:
        where_clauses.append('ta.tahun_ajaran = %s')
        params.append(selected_tahun)
        
    if where_clauses:
        base_sql += ' WHERE ' + ' AND '.join(where_clauses)
        
    base_sql += ' GROUP BY ds.kelas, ds.jurusan, ns.semester, ta.tahun_ajaran ORDER BY ds.kelas ASC, ds.jurusan ASC, ta.tahun_ajaran ASC'
    
    cursor.execute(base_sql, tuple(params))
    results = cursor.fetchall()
    cursor.close()

    return render_template('pages/hasil_analisis.html', 
                         data=results, 
                         kelas_list=kelas_list if role == 'admin' else [],  # Only show kelas filter for admin
                         jurusan_list=jurusan_list,
                         semester_list=semester_list,
                         tahun_list=tahun_list,
                         selected_kelas=selected_kelas,
                         selected_jurusan=selected_jurusan,
                         selected_semester=selected_semester,
                         selected_tahun=selected_tahun,
                         role=role,  # Pass role to template
                         enumerate=enumerate)

@app.route('/delete_hasil_analisis', methods=['POST'])
def delete_hasil_analisis():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    cursor = db.cursor()
    try:
        # Get form data
        nip = request.form.get('nip')
        kelas = request.form.get('kelas')
        jurusan = request.form.get('jurusan')
        semester = request.form.get('semester')
        tahun_ajaran = request.form.get('tahun_ajaran')
        id_ta = f"TA{tahun_ajaran.replace('/', '')}"

        print(f"Debug - Delete params: nip={nip}, kelas={kelas}, jurusan={jurusan}, semester={semester}, tahun_ajaran={tahun_ajaran}")

        # Delete only from nilai_siswa
        cursor.execute("""
            DELETE ns FROM nilai_siswa ns
            INNER JOIN data_siswa ds ON ns.nis = ds.nis
            WHERE ds.nip = %s 
            AND ds.kelas = %s 
            AND ds.jurusan = %s 
            AND ns.semester = %s 
            AND ns.id_ta = %s
        """, (nip, kelas, jurusan, semester, id_ta))

        db.commit()
        
        if cursor.rowcount > 0:
            flash("Data nilai berhasil dihapus", "success")
        else:
            flash("Tidak ada data nilai yang dihapus", "warning")

    except Exception as e:
        db.rollback()
        print(f"Debug - Delete error: {str(e)}")
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
    sql = '''
        SELECT ds.nis, ds.nama_siswa, ds.kelas, ds.jurusan, ns.nilai_mapel1, ns.nilai_mapel2, ns.nilai_mapel3, ns.nilai_mapel4, ns.cluster, ns.semester, ta.tahun_ajaran
        FROM data_siswa ds
        JOIN nilai_siswa ns ON ds.nis = ns.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
        WHERE ds.kelas = %s AND ds.jurusan = %s AND ns.semester = %s AND ta.tahun_ajaran = %s
    '''
    cursor.execute(sql, (kelas, jurusan, semester, tahun_ajaran))
    hasil_klaster = cursor.fetchall()
    
    # Mengambil data mata pelajaran berdasarkan kelas (sama dengan di home)
    kelas_id = ' '.join(kelas.split()[:-1])  # Menghilangkan angka di akhir kelas
    cursor.execute('SELECT * FROM mata_pelajaran WHERE id = %s', (kelas_id,))
    mapel_data = cursor.fetchone()
    
    cursor.close()

    return render_template('pages/hasil_klastering.html', data=hasil_klaster, kelas=kelas, jurusan=jurusan, semester=semester, tahun_ajaran=tahun_ajaran, mapel=mapel_data)

@app.route('/jumlah_klaster', methods=['GET'])
def jumlah_klaster():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    kelas = request.args.get('kelas')
    jurusan = request.args.get('jurusan')
    semester = request.args.get('semester')
    tahun_ajaran = request.args.get('tahun_ajaran')

    sql_query = '''
        SELECT ns.cluster, COUNT(*) AS jumlah, 
               AVG(ns.nilai_mapel1) AS rata_rata_mapel1, 
               AVG(ns.nilai_mapel2) AS rata_rata_mapel2, 
               AVG(ns.nilai_mapel3) AS rata_rata_mapel3, 
               AVG(ns.nilai_mapel4) AS rata_rata_mapel4
        FROM nilai_siswa ns
        JOIN data_siswa ds ON ns.nis = ds.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
        WHERE ds.kelas = %s AND ds.jurusan = %s AND ns.semester = %s AND ta.tahun_ajaran = %s
        GROUP BY ns.cluster
    '''
    cursor.execute(sql_query, (kelas, jurusan, semester, tahun_ajaran))
    jumlah_klaster_data = cursor.fetchall()
    cursor.close()

    return jsonify({
        'label': [row['cluster'] for row in jumlah_klaster_data],
        'jumlah': [row['jumlah'] for row in jumlah_klaster_data],
        'rata_rata_mapel1': [float(row['rata_rata_mapel1']) for row in jumlah_klaster_data],
        'rata_rata_mapel2': [float(row['rata_rata_mapel2']) for row in jumlah_klaster_data],
        'rata_rata_mapel3': [float(row['rata_rata_mapel3']) for row in jumlah_klaster_data],
        'rata_rata_mapel4': [float(row['rata_rata_mapel4']) for row in jumlah_klaster_data],
    })

@app.route('/download_pdf', methods=['GET'])
def download_pdf():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    nip = session.get('nip')
    
    # Get user info
    cursor.execute('SELECT * FROM users WHERE nip = %s', (nip,))
    user_info = cursor.fetchone()
    if not user_info:
        return "User not found", 404

    kelas = user_info['kelas']
    id_jurusan = kelas.split()[1]

    # Get jurusan name
    cursor.execute('SELECT nama_jurusan FROM jurusan WHERE id_jurusan = %s', (id_jurusan,))  # Changed from id to id_jurusan
    jurusan_info = cursor.fetchone()
    nama_jurusan = jurusan_info['nama_jurusan'] if jurusan_info else 'Unknown Jurusan'

    # Get data for PDF
    cursor.execute("""
        SELECT ds.nis, ds.nama_siswa, ds.kelas, ns.nilai_mapel1, ns.nilai_mapel2, ns.nilai_mapel3, ns.nilai_mapel4, ns.cluster, ns.semester, ta.tahun_ajaran
        FROM data_siswa ds
        JOIN nilai_siswa ns ON ds.nis = ns.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
        WHERE ds.kelas = %s AND ds.jurusan = %s
    """, (kelas, nama_jurusan))
    pdf_data = cursor.fetchall()
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
    pdf.cell(200, 10, txt=f"Jurusan: {nama_jurusan}", ln=True)
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
    pdf.cell(20, 10, 'Rata-rata', 1)  # Kolom Rata-rata langsung dari data_siswa
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

    pdf = generate_pdf(pdf_data)
    response = make_response(pdf.output(dest='S').encode('latin1'))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'attachment; filename=hasil_klastering.pdf'
    return response

@app.route('/anggota_klaster', methods=['GET'])
def anggota_klaster():
    if not session.get('sudah_login'):
        return redirect(url_for('login'))

    cursor = db.cursor(dictionary=True)
    kelas = request.args.get('kelas')
    jurusan = request.args.get('jurusan')
    semester = request.args.get('semester')
    tahun_ajaran = request.args.get('tahun_ajaran')
    cluster = request.args.get('cluster')

    # Get anggota klaster data
    cursor.execute("""
        SELECT ds.nis, ds.nama_siswa, ds.kelas, ns.nilai_mapel1, ns.nilai_mapel2, ns.nilai_mapel3, ns.nilai_mapel4, ns.cluster, ns.semester, ta.tahun_ajaran
        FROM data_siswa ds
        JOIN nilai_siswa ns ON ds.nis = ns.nis
        JOIN tahun_ajaran ta ON ns.id_ta = ta.id_ta
        WHERE ds.kelas = %s AND ds.jurusan = %s AND ns.semester = %s AND ta.tahun_ajaran = %s AND ns.cluster = %s
    """, (kelas, jurusan, semester, tahun_ajaran, cluster))
    anggota_klaster_data = cursor.fetchall()
    cursor.close()

    for row in anggota_klaster_data:
        print(f"Debug - NIS: {row['nis']}, Nama: {row['nama_siswa']}, Mapel1: {row['nilai_mapel1']}, Mapel2: {row['nilai_mapel2']}, Mapel3: {row['nilai_mapel3']}, Mapel4: {row['nilai_mapel4']}")
    return jsonify(anggota_klaster_data)

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
    app.run(port=8000, debug=True)