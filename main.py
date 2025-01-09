import pandas as pd
import mysql.connector

# Konfigurasi koneksi MySQL
db_config = {
    'host': 'localhost',        # Ganti dengan host MySQL Anda
    'user': 'root',             # Ganti dengan user MySQL Anda
    'password': 'admin123',     # Ganti dengan password MySQL Anda
    'database': 'support_ticket_db' # Ganti dengan nama database Anda
}

# Fungsi untuk mengimpor CSV ke MySQL
def import_csv_to_mysql(csv_file, table_name):
    # Membaca data dari file CSV menggunakan pandas
    df = pd.read_csv(csv_file)
    
    # Membuka koneksi ke database MySQL
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    # Mengonversi DataFrame ke bentuk list of tuples
    data = [tuple(row) for row in df.values]

    # Menyiapkan query SQL untuk memasukkan data
    placeholders = ', '.join(['%s'] * len(df.columns))
    columns = ', '.join(df.columns)
    insert_query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
    
    try:
        # Menjalankan query untuk setiap baris data
        cursor.executemany(insert_query, data)
        conn.commit()  # Commit perubahan
        print(f"Data berhasil diimpor ke tabel {table_name}")
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()  # Rollback jika terjadi error
    finally:
        cursor.close()
        conn.close()

# Path ke file CSV yang ingin diimpor
csv_file_path = 'gcp_services.csv'  # Ganti dengan path ke file CSV Anda

# Nama tabel yang ingin diimpor
table_name = 'services'  # Ganti dengan nama tabel Anda

# Memanggil fungsi untuk mengimpor data
import_csv_to_mysql(csv_file_path, table_name)
