import streamlit as st
from pyzbar.pyzbar import decode
from PIL import Image, ImageEnhance, ImageFilter
import pandas as pd
import re
import base64

#-- PENGATURAN HALAMAN --
st.set_page_config(page_title="Baggage Check", page_icon="📷", layout="centered")

# ✅ PENJERNIHAN FOTO
def perbaiki_foto(gambar):
    foto = gambar.convert('L')
    foto = ImageEnhance.Contrast(foto).enhance(2.5)
    foto = ImageEnhance.Sharpness(foto).enhance(2.0)
    return foto

# ✅ PEMINDAIAN QR CODE LENGKAP
def baca_semua_qr(gambar_asli):
    hasil_list = []

    def tambah(data):
        data = data.strip()
        if data and data not in hasil_list:
            hasil_list.append(data)

    w, h = gambar_asli.size

    # Scan foto utuh berbagai versi
    foto1 = gambar_asli
    foto2 = perbaiki_foto(gambar_asli)
    foto3 = perbaiki_foto(gambar_asli.resize((w*2, h*2), Image.LANCZOS))

    for foto in [foto1, foto2, foto3]:
        for sudut in [0, 90, -90, 180]:
            f = foto.rotate(sudut, expand=True)
            hasil = decode(f)
            for k in hasil:
                tambah(k.data.decode("utf-8"))

    # Scan dipotong 3 bagian
    bagian = w // 3
    for i in range(3):
        potong = gambar_asli.crop((i*bagian, 0, (i+1)*bagian, h))
        potong = perbaiki_foto(potong)
        potong = potong.resize((potong.width*2, potong.height*2), Image.LANCZOS)
        for sudut in [0, 90, -90, 180]:
            f = potong.rotate(sudut, expand=True)
            hasil = decode(f)
            for k in hasil:
                tambah(k.data.decode("utf-8"))

    # Scan khusus area kanan diperbesar
    potong_kanan = gambar_asli.crop((w*2//3 - 20, 0, w, h))
    potong_kanan = perbaiki_foto(potong_kanan)
    potong_kanan = potong_kanan.resize((potong_kanan.width*4, potong_kanan.height*4), Image.LANCZOS)
    for sudut in [0, 90, -90, 180, 5, -5]:
        f = potong_kanan.rotate(sudut, expand=True)
        hasil = decode(f)
        for k in hasil:
            tambah(k.data.decode("utf-8"))

    return hasil_list

# ✅ FUNGSI LATAR BELAKANG
def pasang_latar(foto_path):
    try:
        with open(foto_path, "rb") as f:
            data_foto = base64.b64encode(f.read()).decode()
        st.markdown(
            f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{data_foto}");
                background-size: cover;
                background-position: center;
                background-attachment: fixed;
                filter: brightness(55%);
            }}
            .block-container {{
                background-color: rgba(0, 0, 0, 0.85);
                padding: 30px;
                border-radius: 15px;
                max-width: 1000px;
            }}
            h1, h2, h3, p, label {{ color: #ffffff !important; }}
            </style>
            """,
            unsafe_allow_html=True
        )
    except:
        st.markdown("<style>.stApp { background-color: #1a1a2e; }</style>", unsafe_allow_html=True)

pasang_latar("lion.pnsg")

# judul program
st.markdown("<h1 style='text-align: center;'>📷 Baggage Check Program V1</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>Program check data stowing, dibuat oleh abdul basit maulana/ABM</p>", unsafe_allow_html=True)
st.divider()

# --- Siapkan tempat simpan data ---
if "daftar_barcode" not in st.session_state:
    st.session_state.daftar_barcode = []
if "pilihan_terakhir" not in st.session_state:
    st.session_state.pilihan_terakhir = "halaman_depan"

st.subheader("MAIN MENU")

# TOMBOL MENU
kolom1, kolom2, kolom3 = st.columns(3)
with kolom1:
    menu_unggah = st.button("📷 1. Unggah Foto", use_container_width=True)
with kolom2:
    menu_lihat = st.button("📊 2. Lihat Semua", use_container_width=True)
with kolom3:
    menu_ringkas = st.button("📋 3. Ringkasan", use_container_width=True)

st.markdown("")

kolom4, kolom5, kosong = st.columns(3)
with kolom4:
    menu_hapus_satu = st.button("🗑️ 4. Hapus Data", use_container_width=True)
with kolom5:
    menu_hapus_semua = st.button("⚠️ 5. Hapus Semua", use_container_width=True)

# PILIH MENU
if menu_unggah:
    pilihan_menu = "menu_unggah"
    st.session_state.pilihan_terakhir = "menu_unggah"
elif menu_lihat:
    pilihan_menu = "menu_lihat"
    st.session_state.pilihan_terakhir = "menu_lihat"
elif menu_ringkas:
    pilihan_menu = "menu_ringkas"
    st.session_state.pilihan_terakhir = "menu_ringkas"
elif menu_hapus_satu:
    pilihan_menu = "menu_hapus_satu"
    st.session_state.pilihan_terakhir = "menu_hapus_satu"
elif menu_hapus_semua:
    pilihan_menu = "menu_hapus_semua"
    st.session_state.pilihan_terakhir = "menu_hapus_semua"
else:
    pilihan_menu = st.session_state.pilihan_terakhir

st.divider()

# --- ✅ MENU 1: UNGGAH FOTO QR CODE ---
if pilihan_menu == "menu_unggah":
    st.subheader("📷 Unggah Foto Stowing")
    foto_barcode = st.file_uploader("Pilih Foto Stowing", type=["jpg","jpeg","png"])

    if foto_barcode:
        gambar_asli = Image.open(foto_barcode)
        
        with st.spinner("🔄 Memindai..."):
            semua_data = baca_semua_qr(gambar_asli)
        
        if semua_data:
            st.success(f"✅ Ditemukan {len(semua_data)} QR Code!")
            
            for data_barcode in semua_data:
                data_sudah_ada = False
                for item in st.session_state.daftar_barcode:
                    isi = item["Data"].replace("🔴 ", "").replace(" [DUPLIKAT]", "")
                    if isi == data_barcode:
                        data_sudah_ada = True
                        break

                nomor = len(st.session_state.daftar_barcode) + 1
                
                if data_sudah_ada:
                    st.session_state.daftar_barcode.append({
                        "No": nomor,
                        "Data": f"🔴 {data_barcode} [DUPLIKAT]",
                        "Jenis": "⚠️ DUPLIKAT"
                    })
                    st.warning(f"⚠️ Data: {data_barcode} → DUPLIKAT")
                else:
                    st.session_state.daftar_barcode.append({
                        "No": nomor,
                        "Data": data_barcode,
                        "Jenis": "Dibaca"
                    })
                    st.success(f"✅ Data: {data_barcode} → disimpan!")
        else:
            st.warning("⚠️ Tidak ada QR Code yang terbaca!")

# --- ✅ MENU 2: LIHAT DATA ---
elif pilihan_menu == "menu_lihat":
    st.subheader("📊 Semua Data yang Tersimpan")
    if st.session_state.daftar_barcode:
        tabel = pd.DataFrame(st.session_state.daftar_barcode)
        st.dataframe(tabel, use_container_width=True, hide_index=True)
        st.info(f"Jumlah total data: {len(st.session_state.daftar_barcode)}")
    else:
        st.info("Belum ada data yang tersimpan.")

# --- ✅ MENU 3: RINGKASAN DATA (FORMAT SESUAI PERMINTAAN) ---
elif pilihan_menu == "menu_ringkas":
    st.subheader("📋 Ringkasan Data Stowing")
    if st.session_state.daftar_barcode:
        daftar_ringkas = []
        for item in st.session_state.daftar_barcode:
            data_asli = item["Data"]
            adalah_duplikat = "[DUPLIKAT]" in data_asli
            data_bersih = data_asli
            if adalah_duplikat:
                data_bersih = data_asli.replace("🔴 ", "").replace(" [DUPLIKAT]", "")
            
            # === AMBIL 4 ANGKA TERAKHIR DARI DERET ANGKA TERPANJANG ===
            semua_deret_angka = re.findall(r'\d+', data_bersih)
            if semua_deret_angka:
                deret_terpanjang = max(semua_deret_angka, key=len)
                empat_angka_terakhir = deret_terpanjang[-4:]
            else:
                empat_angka_terakhir = "—"
            
            # === FORMAT: [Kode Bandara];[Kode Maskapai] [Nomor Penerbangan] ===
            pola = re.search(r'([A-Z]{2,3});([A-Z]{2,3})\s*(\d{3,4})', data_bersih)
            if pola:
                kode_bandara = pola.group(1)
                kode_maskapai = pola.group(2)
                nomor_penerbangan = pola.group(3)
                ringkas = f"{kode_bandara};{kode_maskapai} {nomor_penerbangan}"
            else:
                ringkas = "—"
            
            # TANDA DUPLIKAT JIKA ADA
            if adalah_duplikat:
                empat_angka_terakhir = "🔴 " + empat_angka_terakhir
                ringkas = "🔴 " + ringkas
            
            daftar_ringkas.append({
                "No": item["No"],
                "4 Angka Terakhir": empat_angka_terakhir,
                "Kode Penerbangan": ringkas
            })
        
        # === TAMPILAN TABEL ===
        baris_tabel = ""
        for b in daftar_ringkas:
            baris_tabel += f"<tr><td>{b['No']}</td><td>{b['4 Angka Terakhir']}</td><td>{b['Kode Penerbangan']}</td></tr>"
        
        tabel_html = f"""
        <style>
        .tabelku {{ width: 100%; border-collapse: collapse; }}
        .tabelku th, .tabelku td {{ 
            padding: 10px; 
            text-align: center; 
            border: 1px solid #444;
            color: white;
        }}
        .tabelku th {{ background-color: rgba(38, 39, 48, 0.9); }}
        .tabelku td:first-child {{ width: 70px; }}
        </style>
        <table class="tabelku">
            <tr>
                <th>No</th>
                <th>4 Angka Terakhir</th>
                <th>Kode Penerbangan</th>
            </tr>
            {baris_tabel}
        </table>
        """
        st.markdown(tabel_html, unsafe_allow_html=True)
        st.info(f"Jumlah data: {len(daftar_ringkas)}")
    else:
        st.info("Belum ada data yang tersimpan.")

# --- ✅ MENU 4: HAPUS SATU DATA ---
elif pilihan_menu == "menu_hapus_satu":
    st.subheader("🗑️ Hapus Data Tertentu")
    if not st.session_state.daftar_barcode:
        st.info("Belum ada data yang bisa dihapus.")
    else:
        st.warning("Pilih nomor urut data yang ingin dihapus:")
        daftar_pilihan = []
        for item in st.session_state.daftar_barcode:
            no = item["No"]
            data = item["Data"]
            if "[DUPLIKAT]" in data:
                tampil = f"No. {no} — {data.replace('🔴 ', '').replace(' [DUPLIKAT]', '')} 🔴 DUPLIKAT"
            else:
                tampil = f"No. {no} — {data[:50]}..." if len(data) > 50 else f"No. {no} — {data}"
            daftar_pilihan.append(tampil)
        
        pilihan = st.selectbox("Pilih data yang akan dihapus", daftar_pilihan)
        nomor_dihapus = int(pilihan.split("No. ")[1].split(" —")[0])
        konfirmasi = st.button("✅ KLIK DI SINI UNTUK MENGHAPUS", type="primary")
        
        if konfirmasi:
            st.session_state.daftar_barcode = [d for d in st.session_state.daftar_barcode if d["No"] != nomor_dihapus]
            for indeks, item in enumerate(st.session_state.daftar_barcode, start=1):
                item["No"] = indeks
            st.success(f"✅ Data nomor {nomor_dihapus} BERHASIL dihapus!")

# --- ✅ MENU 5: HAPUS SEMUA DATA ---
elif pilihan_menu == "menu_hapus_semua":
    st.subheader("⚠️ Hapus SEMUA Data")
    if not st.session_state.daftar_barcode:
        st.info("Belum ada data yang tersimpan.")
    else:
        jumlah = len(st.session_state.daftar_barcode)
        st.warning(f"⚠️ Anda akan MENGHAPUS SEMUA {jumlah} data yang tersimpan!")
        st.write("Data yang dihapus TIDAK BISA dikembalikan lagi!")
        konfirmasi_semua = st.button("🗑️ HAPUS SEMUA DATA SEKARANG", type="primary")
        if konfirmasi_semua:
            st.session_state.daftar_barcode = []
            st.success("✅ SEMUA DATA BERHASIL DIHAPUS!")