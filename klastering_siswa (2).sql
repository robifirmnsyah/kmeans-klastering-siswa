-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: db
-- Waktu pembuatan: 29 Nov 2024 pada 14.07
-- Versi server: 8.0.39
-- Versi PHP: 8.2.23

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `klastering_siswa`
--

-- --------------------------------------------------------

--
-- Struktur dari tabel `data_siswa`
--

CREATE TABLE `data_siswa` (
  `nip` int DEFAULT NULL,
  `nis` varchar(10) NOT NULL,
  `nama_siswa` varchar(225) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci DEFAULT NULL,
  `kelas` varchar(255) DEFAULT NULL,
  `jurusan` varchar(255) DEFAULT NULL,
  `id_kelas` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `jurusan`
--

CREATE TABLE `jurusan` (
  `id` varchar(5) NOT NULL,
  `nama_jurusan` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `jurusan`
--

INSERT INTO `jurusan` (`id`, `nama_jurusan`) VALUES
('DKV', 'Desain Komunikasi Visual'),
('HR', 'Hotel dan Restoran'),
('OTKP', 'Otomatisasi dan Tata Kelola Perkantoran'),
('RPL', 'Rekayasa Perangkat Lunak'),
('TBSM', 'Teknik dan Bisnis Sepeda Motor'),
('TITL', 'Teknik Instalasi Tenaga Listrik'),
('TKJ', 'Teknik Jaringan Komputer Dan Jaringan'),
('TKRO', 'Teknik Kendaraan Ringan Otomotif');

-- --------------------------------------------------------

--
-- Struktur dari tabel `mata_pelajaran`
--

CREATE TABLE `mata_pelajaran` (
  `id` varchar(20) NOT NULL,
  `mapel1` varchar(255) DEFAULT NULL,
  `mapel2` varchar(255) DEFAULT NULL,
  `mapel3` varchar(255) DEFAULT NULL,
  `mapel4` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `mata_pelajaran`
--

INSERT INTO `mata_pelajaran` (`id`, `mapel1`, `mapel2`, `mapel3`, `mapel4`) VALUES
('X DKV', 'Dasar Dasar Seni Rupa', 'Gambar', 'Sketsa', NULL),
('X HR', 'Pelayanan Prima', 'Kesehatan dan Keselamatan Kerja', 'Industri Perhotelan', 'Klerikal dan Komunikasi Industri Perhotelan'),
('X OTKP', 'Administrasi Umum', 'Teknologi Perkantoran', 'Korespondensi', 'Kearsipan'),
('X RPL', 'Sistem Komputer', 'Komputer dan Jaringan Dasar', 'Pemograman Dasar', 'Desain Grafis'),
('X TBSM', 'Gambar Teknik Otomotif', 'Teknologi Dasar Otomotif', 'Pekerjaan Dasar Otomotif', NULL),
('X TITL', 'Gambar Teknik Listrik', 'Dasar Listrik dan Elektronika', 'Pekerjaan Dasar Elektromekanik', NULL),
('X TKJ', 'Komputer dan Jaringan Dasar', 'Sistem Komputer', 'Pemograman Dasar', 'Desain Grafis'),
('X TKRO', 'Gambar Teknik Otomotif', 'Teknologi Dasar Otomotif', 'Pekerjaan Dasar Otomotif', NULL),
('XI DKV', 'Desain Publikasi', 'Komputer Grafis', 'Fotografi', 'Videografi'),
('XI HR', 'Front Office', 'Housekeeping', 'Laundry', 'Food and Beverage Service'),
('XI OTKP', 'Otomatisasi Tata Kelola Kepegawaian', 'Otomatisasi Tata Kelola Keuangan', 'Otomatisasi Tata Kelola Sarana dan Prasarana', 'Otomatisasi Tata Kelola Humas dan Keprotokolan'),
('XI RPL', 'Pemodelan Perangkat Lunak', 'Basis Data', 'Pemograman Berorientasi Objek', 'Pemograman Web dan Perangkat Bergerak'),
('XI TBSM', 'Pemeliharaan Mesin Sepeda Motor', 'Pemeliharaan Sasis Sepeda Motor', 'Pemeliharaan Kelistrikan Sepeda Motor', 'Produk Kreatif dan Kewirausahaan'),
('XI TITL', 'Instalasi Penerangan Listrik', 'Instalasi Tenaga Listrik', 'Instalasi Motor Listrik', 'Perbaikan Peralatan Listrik'),
('XI TKJ', 'Teknologi WAN', 'Teknologi WAN', 'Teknologi Layanan Jaringan', 'Administrasi Sistem Jaringan'),
('XI TKRO', 'Pemeliharaan Mesin Kendaraan Ringan', 'Pemeliharaan Sasis dan Pemindah Tenaga Kendaraan Ringan', 'Pemeliharaan Kelistrikan Kendaraan Ringan', 'Produk Kreatif dan Kewirausahaan'),
('XII DKV', 'Desain Publikasi', 'Komputer Grafis', 'Fotografi', 'Videografi'),
('XII HR', 'Food and Beverage Service', 'Banquet Management', 'Rooms Division Management', 'Produk Kreatif dan Kewirausahaan'),
('XII OTKP', 'Otomatisasi Tata Kelola Kepegawaian', 'Otomatisasi Tata Kelola Keuangan', 'Otomatisasi Tata Kelola Sarana dan Prasarana', 'Otomatisasi Tata Kelola Humas dan Keprotokolan'),
('XII RPL', 'Pemodelan Perangkat Lunak', 'Basis Data', 'Pemograman Berorientasi Objek', 'Pemograman Web dan Perangkat Bergerak'),
('XII TBSM', 'Pemeliharaan Mesin Sepeda Motor', 'Pemeliharaan Sasis Sepeda Motor', 'Pemeliharaan Kelistrikan Sepeda Motor', 'Produk Kreatif dan Kewirausahaan'),
('XII TITL', 'Instalasi Penerangan Listrik', 'Instalasi Tenaga Listrik', 'Instalasi Motor Listrik', 'Perbaikan Peralatan Listrik'),
('XII TKJ', 'Teknologi Layanan Jaringan', 'Administrasi Infrastruktur Jaringan', 'Administrasi Sistem Jaringan', 'Produk Kreatif dan Kewirausahaan'),
('XII TKRO', 'Pemeliharaan Mesin Kendaraan Ringan', 'Pemeliharaan Sasis dan Pemindah Tenaga Kendaraan Ringan', 'Pemeliharaan Kelistrikan Kendaraan Ringan', 'Produk Kreatif dan Kewirausahaan');

-- --------------------------------------------------------

--
-- Struktur dari tabel `nilai_siswa`
--

CREATE TABLE `nilai_siswa` (
  `id` int NOT NULL,
  `nis` varchar(10) NOT NULL,
  `id_mapel` varchar(10) NOT NULL,
  `nilai_mapel1` int NOT NULL,
  `nilai_mapel2` int NOT NULL,
  `nilai_mapel3` int NOT NULL,
  `nilai_mapel4` int NOT NULL,
  `cluster` int NOT NULL,
  `semester` varchar(10) NOT NULL,
  `id_ta` varchar(10) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `tahun_ajaran`
--

CREATE TABLE `tahun_ajaran` (
  `id_ta` varchar(10) NOT NULL,
  `tahun_ajaran` varchar(10) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- --------------------------------------------------------

--
-- Struktur dari tabel `users`
--

CREATE TABLE `users` (
  `nama` varchar(255) DEFAULT NULL,
  `username` varchar(100) NOT NULL,
  `email` varchar(120) NOT NULL,
  `password` varchar(128) NOT NULL,
  `kelas` varchar(255) DEFAULT NULL,
  `role` varchar(20) NOT NULL,
  `nip` int NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Dumping data untuk tabel `users`
--

INSERT INTO `users` (`nama`, `username`, `email`, `password`, `kelas`, `role`, `nip`) VALUES
('Wali Kelas X TKJ 1', 'walasxtkj1', 'walasxtkj1@gmail.com', '123123', 'X TKJ 1', 'user', 20110201),
('Wali Kelas X TKJ 2', 'walasxtkj2', 'walasxtkj2@gmail.com', '123123', 'X TKJ 2', 'user', 20110202),
('Wali Kelas X TKJ 3', 'walasxtkj3', 'walasxtkj3@gmail.com', '123123', 'X TKJ 3', 'user', 20110203),
('Wali Kelas X RPL 1', 'walasxrpl1', 'walasxrpl1@gmail.com', '123123', 'X RPL 1', 'user', 20110204),
('Wali Kelas X RPL 2', 'walasxrpl2', 'walasxrpl2@gmail.com', '123123', 'X RPL 2', 'user', 20110205),
('Wali Kelas X RPL 3', 'walasxrpl3', 'walasxrpl3@gmail.com', '123123', 'X RPL 3', 'user', 20110206),
('Wali Kelas X TKRO 1', 'walasxtkro1', 'walasxtkro1@gmail.com', '123123', 'X TKRO 1', 'user', 20110207),
('Wali Kelas X TKRO 2', 'walasxtkro2', 'walasxtkro2@gmail.com', '123123', 'X TKRO 2', 'user', 20110208),
('Wali Kelas X TKRO 3', 'walasxtkro3', 'walasxtkro3@gmail.com', '123123', 'X TKRO 3', 'user', 20110209),
('Wali Kelas X TBSM 1', 'walasxtbsm1', 'walasxtbsm1@gmail.com', '123123', 'X TBSM 1', 'user', 20110210),
('Wali Kelas X TBSM 2', 'walasxtbsm2', 'walasxtbsm2@gmail.com', '123123', 'X TBSM 2', 'user', 20110211),
('Wali Kelas X TBSM 3', 'walasxtbsm3', 'walasxtbsm3@gmail.com', '123123', 'X TBSM 3', 'user', 20110212),
('Wali Kelas X TITL 1', 'walasxtitl1', 'walasxtitl1@gmail.com', '123123', 'X TITL 1', 'user', 20110213),
('Wali Kelas X TITL 2', 'walasxtitl2', 'walasxtitl2@gmail.com', '123123', 'X TITL 2', 'user', 20110214),
('Wali Kelas X TITL 3', 'walasxtitl3', 'walasxtitl3@gmail.com', '123123', 'X TITL 3', 'user', 20110215),
('Wali Kelas X OTKP 1', 'walasxotkp1', 'walasxotkp1@gmail.com', '123123', 'X OTKP 1', 'user', 20110216),
('Wali Kelas X OTKP 2', 'walasxotkp2', 'walasxotkp2@gmail.com', '123123', 'X OTKP 2', 'user', 20110217),
('Wali Kelas X OTKP 3', 'walasxotkp3', 'walasxotkp3@gmail.com', '123123', 'X OTKP 3', 'user', 20110218),
('Wali Kelas X DKV 1', 'walasxdkv1', 'walasxdkv1@gmail.com', '123123', 'X DKV 1', 'user', 20110219),
('Wali Kelas X DKV 2', 'walasxdkv2', 'walasxdkv2@gmail.com', '123123', 'X DKV 2', 'user', 20110220),
('Wali Kelas X DKV 3', 'walasxdkv3', 'walasxdkv3@gmail.com', '123123', 'X DKV 3', 'user', 20110221),
('Wali Kelas X HR 1', 'walasxhr1', 'walasxhr1@gmail.com', '123123', 'X HR 1', 'user', 20110222),
('Wali Kelas X HR 2', 'walasxhr2', 'walasxhr2@gmail.com', '123123', 'X HR 2', 'user', 20110223),
('Wali Kelas X HR 3', 'walasxhr3', 'walasxhr3@gmail.com', '123123', 'X HR 3', 'user', 20110224),
('Indra Gunawan', 'indragnwn', 'robifirmansyah314@gmail.com', '123123', 'XII TKJ 10', 'admin', 20110231),
('Robi Firmansyah', 'robifir', 'robifirmansyah31@gmail.com', '123123', 'XI TKJ 2', 'user', 20110279),
('tetatstfdrfgg', 'indragnwn353', 'robi.firmansyah@aglobal.id', '123123', 'XI MIPA 13', 'user', 2011022334);

--
-- Indexes for dumped tables
--

--
-- Indeks untuk tabel `data_siswa`
--
ALTER TABLE `data_siswa`
  ADD PRIMARY KEY (`nis`);

--
-- Indeks untuk tabel `jurusan`
--
ALTER TABLE `jurusan`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `mata_pelajaran`
--
ALTER TABLE `mata_pelajaran`
  ADD PRIMARY KEY (`id`);

--
-- Indeks untuk tabel `nilai_siswa`
--
ALTER TABLE `nilai_siswa`
  ADD PRIMARY KEY (`id`),
  ADD KEY `nis` (`nis`),
  ADD KEY `id_ta` (`id_ta`);

--
-- Indeks untuk tabel `tahun_ajaran`
--
ALTER TABLE `tahun_ajaran`
  ADD PRIMARY KEY (`id_ta`);

--
-- Indeks untuk tabel `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`nip`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`);

--
-- AUTO_INCREMENT untuk tabel yang dibuang
--

--
-- AUTO_INCREMENT untuk tabel `nilai_siswa`
--
ALTER TABLE `nilai_siswa`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;

--
-- Ketidakleluasaan untuk tabel pelimpahan (Dumped Tables)
--

--
-- Ketidakleluasaan untuk tabel `nilai_siswa`
--
ALTER TABLE `nilai_siswa`
  ADD CONSTRAINT `nilai_siswa_ibfk_1` FOREIGN KEY (`nis`) REFERENCES `data_siswa` (`nis`),
  ADD CONSTRAINT `nilai_siswa_ibfk_2` FOREIGN KEY (`id_ta`) REFERENCES `tahun_ajaran` (`id_ta`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
