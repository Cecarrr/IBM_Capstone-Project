# Verified Test Case Generator (tcgen)

Agen pembuat unit test Python (pytest) yang **kualitas hasilnya diukur, bukan dipercaya begitu saja**.

Capstone Project Hacktiv8 x IBM, Track **IBM Bob**, kelas *IT - AI Agent for Programming*, topik **Test Case Generator**.

---

## Ringkasan

tcgen terdiri dari dua bagian yang bekerja berpasangan:

1. **Agen (prompt berlapis + LLM).** `tcgen build-prompt` merakit prompt tiga layer
   (*Role & Context*, *Task & Requirements*, *Constraints & Output*) bersama source modul Python.
   Prompt itu ditempel ke LLM mana pun (misalnya IBM Bob) dan LLM menghasilkan satu file
   `test_<modul>.py`. Nilai yang diharapkan di setiap assertion wajib diturunkan dari
   **docstring (spesifikasi)**, bukan dari menjalankan atau menyalin perilaku kode.
2. **Verifikator.** `tcgen check` menjalankan test tersebut, lalu melakukan **mutation testing**:
   kode sumber sengaja diubah dengan bug kecil, satu per satu, dan alat menghitung berapa persen
   bug yang tertangkap test (*mutation score*). Hasilnya ukuran objektif kualitas test.

Langkah LLM dilakukan **manual** (copy-paste). Alat ini tidak memanggil API apa pun dan tidak
membutuhkan API key.

## Masalah yang diselesaikan

Menulis unit test sering tertunda atau hanya mencakup skenario normal, karena kasus batas,
input tidak valid, dan kondisi error butuh kebiasaan berpikir seperti penguji. Banyak
pengembang kini meminta AI membuat test, tetapi test hasil AI terlihat meyakinkan dan lolos
semua tanpa tentu bermakna. AI bisa menulis assertion berdasarkan perilaku kode yang sedang
berjalan, termasuk perilaku yang keliru, sehingga bug ikut "disahkan". Tanpa pengukuran,
pengembang mendapat rasa aman yang palsu.

tcgen menjawabnya dengan dua hal: prompt yang memaksa test diturunkan dari spesifikasi,
dan pengukuran mutation score yang menunjukkan perilaku mana yang **belum** dijaga test.

**Pengguna sasaran:** mahasiswa informatika dan developer junior yang menulis kode Python
dan butuh test yang bisa dipercaya.

---

## Cara kerja

```
build-prompt:
  prompts/layer1_role.md + layer2_task.md + layer3_output.md + module.py
        -> prompt_out.md  --(tempel ke LLM, langkah manual)-->  test_<modul>.py

check <module.py> <test_file.py>:
  1. BASELINE  : pytest pada modul asli. Gagal atau 0 test -> berhenti.
  2. CONTROL   : pytest pada ast.unparse(modul). Harus lulus.
  3. MUTASI    : untuk setiap titik mutasi, buat 1 mutant, jalankan pytest di sandbox.
  4. LAPORAN   : skor mutasi + daftar mutant yang selamat (gap pada test).
```

---

## Instalasi

Persyaratan:

- Python 3.10 atau lebih baru (memakai `ast.unparse` dan type hint union)
- `pytest` (satu-satunya dependensi di luar stdlib)

```powershell
pip install pytest
```

Tidak ada `setup.py` atau `pyproject.toml`. Salin atau clone folder proyek ke mana saja.
Dikembangkan dan diuji di Windows (PowerShell) dengan Python 3.13.

---

## Cara pakai

### 1. Buat prompt

```powershell
python tcgen.py build-prompt examples\grade_calculator.py
```

Menulis `prompt_out.md` di direktori kerja saat ini (ditimpa setiap kali dijalankan).
Isinya tiga layer instruksi diikuti source modul dalam code fence. Panjang fence otomatis
menyesuaikan jika source berisi backtick.

### 2. Tempel ke LLM

Salin seluruh isi `prompt_out.md` ke IBM Bob atau LLM lain. Minta LLM menghasilkan
satu file test.

### 3. Simpan file test

Simpan jawaban LLM sebagai `test_<modul>.py`. File test mengimpor modul dengan nama biasa
(`from grade_calculator import ...`).

### 4. Verifikasi

```powershell
python tcgen.py check examples\grade_calculator.py examples\test_grade_calculator.py
```

Opsi: `--timeout N` (detik per proses pytest, bawaan 10), berlaku untuk baseline, control,
dan setiap mutant.

Kode keluar: `0` bila pipeline selesai (apa pun skornya), `1` bila berhenti karena
input salah, test gagal pada kode asli, atau tidak ada test yang terkumpul.

Selain `python tcgen.py ...`, perintah `python -m tcgen ...` juga bisa dipakai dari
direktori proyek.

---

## Membaca laporan

Contoh untuk test yang kuat:

```
============================================================
VERIFIED TEST CASE GENERATOR - Mutation Report
============================================================

[BASELINE] pytest on original source
  exit code  : 0
  collected  : 32
  passed     : 32
  failed     : 0
  verdict    : PASSED

[CONTROL]  pytest on ast.unparse(original source)
  exit code  : 0
  collected  : 32
  passed     : 32
  failed     : 0
  verdict    : PASSED

[MUTANTS]
  total generated : 22
  killed          : 22
  survived        : 0
  timeout (killed): 0
  error (excluded): 0

  mutation score  : 22/22  (100.0%)

  All mutants killed (or errored). No survivors.
============================================================
```

Contoh untuk test yang lemah (hanya titik tengah tiap nilai). Mutant yang selamat menunjuk
persis perilaku yang tidak dijaga, yaitu semua batas nilai:

```
[MUTANTS]
  total generated : 22
  killed          : 8
  survived        : 14
  timeout (killed): 0
  error (excluded): 0

  mutation score  : 8/22  (36.4%)

------------------------------------------------------------
SURVIVING MUTANTS (14) - behaviors not caught by the tests:
------------------------------------------------------------
  [1] line 59: `if score < 0 or score > 100:`  (boolean or -> and)
  [2] line 59: `if score < 0 or score > 100:`  (comparison op[0] < -> <=)
  ...
  [6] line 61: `if score >= 90:`  (comparison op[0] >= -> >)
  [7] line 61: `if score >= 90:`  (constant 90 -> 91)
  ...
  [14] line 103: `if len(scores) == 0:`  (constant 0 -> 1)
```

| Bagian | Arti |
|---|---|
| BASELINE | Test dijalankan pada modul asli. Harus lulus sebelum mutasi dimulai. |
| CONTROL | Test dijalankan pada `ast.unparse(modul)`. Memastikan proses unparse tidak mengubah perilaku. |
| killed | Mutant yang membuat minimal satu test gagal (exit code 1). |
| survived | Mutant yang lolos semua test. Ini celah pada test. |
| timeout | Mutant yang melewati `--timeout` (misalnya loop tak berujung). Dihitung killed. |
| error | Mutant dengan exit code selain 0 dan 1 (misalnya error impor). Dikeluarkan dari skor. |
| score | `(killed + timeout) / (killed + timeout + survived)` |

Seluruh laporan berupa teks ASCII agar aman di konsol Windows.

---

## Arsitektur prompt (prompt layering)

Prompt agen disimpan sebagai tiga file Markdown terpisah di `prompts/`, masing-masing
menjawab satu pertanyaan. Pemisahan ini membuat revisi bisa terarah: satu masalah pada
hasil berarti revisi satu layer saja.

| Layer | File | Pertanyaan yang dijawab |
|---|---|---|
| 1. Role & Context | `prompts/layer1_role.md` | Agen berperan sebagai siapa, menerima apa, dan batasan apa yang tidak boleh dilanggar? |
| 2. Task & Requirements | `prompts/layer2_task.md` | Apa yang harus dihasilkan dan bagaimana menurunkan nilai yang diharapkan? |
| 3. Constraints & Output | `prompts/layer3_output.md` | Bagaimana bentuk akhir file agar langsung bisa dijalankan dan diperiksa? |

**Layer 1: Role & Context.** Agen bertindak sebagai senior QA engineer Python yang menerima
satu file berisi fungsi dengan docstring (docstring = spesifikasi). Batasan keras: tidak
mengubah source, hanya `pytest`, nilai harapan diturunkan dari docstring (bukan dari
menjalankan atau menyalin kode), perilaku yang tidak terdokumentasi tidak boleh ditebak diam-diam,
dan tes harus deterministik (tanpa jaringan, file, atau angka acak).

**Layer 2: Task & Requirements.** Untuk setiap fungsi dibuat test dalam empat kategori:
*happy path*, *boundary values*, *invalid input / exceptions*, dan *equivalence partitions*.
Nilai harapan tidak boleh didapat dengan menjalankan, menelusuri, atau menyalin rumus fungsi.
Bila spesifikasi ambigu, test ditulis dengan penanda `# ASSUMPTION [A1]: ...` dan dikumpulkan
di ringkasan. Penanganan error yang tidak dispesifikasikan **tidak** dites dan hanya dicatat
sebagai asumsi.

**Layer 3: Constraints & Output.** Satu file `test_<modul>.py` di direktori yang sama dengan
modul, mengimpor modul dengan nama biasa. Urutan isi: docstring modul, import, test yang
dikelompokkan per fungsi dan per kategori, lalu blok komentar `COVERAGE SUMMARY` dan
`ASSUMPTIONS`. Penamaan `test_<fungsi>__<skenario>` huruf kecil, satu perilaku per test.

**Verifikasi di luar prompt.** Kualitas hasil tidak diserahkan pada kepercayaan terhadap
model. Test dijalankan lewat baseline gate, control run, lalu mutation testing (bagian berikut).

---

## Detail verifikasi

### Mutator (`tcgen/mutator.py`)

Mutator berbasis AST (`ast`), tanpa library eksternal, dengan satu mutasi per mutant:

| Keluarga | Mutasi |
|---|---|
| Aritmetika | `+` <-> `-`, `*` <-> `/` |
| Perbandingan | `<` <-> `<=`, `>` <-> `>=`, `==` <-> `!=` |
| Boolean | `and` <-> `or` |
| Konstanta | literal numerik `n` -> `n + 1` (konstanta `bool` dilewati) |
| Nilai kembali | `return <ekspresi>` -> `return None` (`return None` dilewati) |
| Augmented assignment | `+=` <-> `-=`, `*=` <-> `/=` |

Desainnya dua tahap: pertama semua titik mutasi dienumerasi secara deterministik
(depth-first, kiri ke kanan), lalu untuk titik ke-*i* source diparse ulang dan **hanya**
mutasi ke-*i* yang diterapkan. Daftar mutant selalu sama untuk source yang sama.

### Sandbox (`tcgen/runner.py`)

Untuk setiap run dibuat `TemporaryDirectory` baru berisi: modul (atau mutant) dengan
**nama file asli**, salinan file test, dan salinan semua file `.py` yang sejajar dengan modul.
pytest dijalankan dengan `cwd` sandbox, sehingga Python mengimpor mutant, bukan file asli.
File asli tidak pernah diubah. Setiap run punya timeout dan prosesnya dimatikan bila lewat.
Pengaturan untuk Windows: output UTF-8 (`PYTHONUTF8`, `encoding="utf-8"`) dan
`ignore_cleanup_errors=True` agar kunci file setelah proses dimatikan tidak membuat alat crash.
pytest dijalankan dengan `-x -q -p no:cacheprovider`.

### Klasifikasi exit code

| Hasil pytest | Klasifikasi |
|---|---|
| exit 0 | SURVIVED (semua test lulus, mutant tidak tertangkap) |
| exit 1 | KILLED (minimal satu test gagal) |
| timeout | TIMEOUT (dihitung killed) |
| lainnya | ERROR (dikeluarkan dari skor) |

`ZeroDivisionError` yang terjadi di dalam test membuat test itu gagal, sehingga mutant
dihitung KILLED, bukan ERROR.

### Baseline gate dan control run

Sebelum mutasi, test harus lulus pada modul asli dan terkumpul minimal satu test. Jika tidak,
alat berhenti dengan pesan jelas, karena pada baseline yang gagal semua mutant akan tampak
"terbunuh" dan skor tidak bermakna. Control run menjalankan test pada
`ast.unparse(ast.parse(source))` untuk memastikan proses unparse tidak mengubah perilaku.

---

## Contoh dan hasil pengukuran

Folder `examples/` berisi tiga modul stdlib-only dengan docstring yang presisi (batas
inklusif/eksklusif dan setiap error ditulis eksplisit):

- `grade_calculator.py`: `score_to_grade`, `average`
- `password_checker.py`: `check_strength`
- `date_overlap.py`: `ranges_overlap`

`examples/buggy/` berisi salinan tiap modul dengan **tepat satu bug** yang sengaja ditanam
(lihat `examples/buggy/BUGS.md`). Docstring tidak berubah, sehingga test yang dibuat dari
spesifikasi seharusnya gagal pada versi buggy.

`examples/sample_tests/` berisi dua suite referensi untuk `grade_calculator` yang
**ditulis tangan (bukan keluaran agen)**: satu kuat, satu lemah.

Hasil pengukuran pada `examples/grade_calculator.py` (22 mutant):

| Suite test | Asal | Jumlah test | Skor mutasi |
|---|---|---|---|
| Referensi kuat | tulisan tangan | 32 | 22/22 (100%) |
| Referensi lemah | tulisan tangan | 6 | 8/22 (36,4%) |
| Hasil LLM (IBM Bob, run 1) | dihasilkan dari `prompt_out.md` | 44 | 22/22 (100%) |
| Hasil LLM pada modul buggy | file test yang sama | gagal di baseline | `boundary_90_is_a` gagal (bug `> 90` tertangkap) |

Perlu dicatat dengan jujur:

- Run 1 dengan Bob dilakukan **sekali** dan di sesi yang sama dengan pembuatan alat, sehingga
  konteks tidak bersih (Bob bisa membaca file referensi di workspace). Hasilnya dilaporkan
  apa adanya dan tidak dianggap bukti generalisasi.
- Evaluasi pada `password_checker` dan `date_overlap` dengan test hasil LLM **belum
  dijalankan** karena keterbatasan kuota dan waktu. Modul dan prompt-nya sudah siap.
- Suite referensi membuktikan bahwa **alat ukurnya bekerja** (kuat 100% vs lemah 36,4%).
  Itu bukan bukti kualitas keluaran agen.

---

## Struktur proyek

```
tcgen.py                  titik masuk CLI
tcgen/
  __init__.py
  __main__.py             subcommand build-prompt dan check
  prompt_builder.py       merakit tiga layer + source menjadi prompt_out.md
  mutator.py              enumerasi dan penerapan mutasi (AST)
  runner.py               sandbox + pytest subprocess + klasifikasi
  reporter.py             laporan teks dan skor
prompts/
  layer1_role.md          Layer 1: Role & Context
  layer2_task.md          Layer 2: Task & Requirements
  layer3_output.md        Layer 3: Constraints & Output
examples/
  grade_calculator.py     modul contoh
  password_checker.py
  date_overlap.py
  test_grade_calculator.py   hasil LLM (Bob) run 1
  buggy/                  salinan dengan satu bug + BUGS.md
  sample_tests/           suite referensi tulisan tangan (kuat dan lemah)
tests/                    test untuk alat itu sendiri
  test_mutator.py   test_runner.py
  test_reporter.py  test_cli.py  test_examples.py
prompt_out.md             contoh keluaran build-prompt (grade_calculator)
```

## Pengujian alat sendiri

```powershell
python -m pytest tests -q
```

Tes memakai pytest asli dan subprocess sungguhan, tanpa mock pada runner. Karena dua tes
end-to-end menjalankan `check` penuh (22 mutant), seluruh suite membutuhkan sekitar 2 menit.
Cakupan utama:

- mutator: jumlah titik mutasi, `return None` dan konstanta bool tidak dimutasi, invarian
  bahwa setiap mutant bisa dikompilasi, hanya mengubah satu baris, dan deterministik;
- runner: **sandbox benar-benar mengimpor mutant** (tes regresi utama), timeout mematikan proses
  dan tidak meninggalkan folder sementara, path berspasi, modul non-ASCII, modul dan test di
  direktori berbeda;
- reporter: skor menghitung timeout sebagai killed, label PASSED/FAILED, exit code tercetak,
  laporan ASCII-only;
- CLI dan contoh: pesan error, `python -m tcgen`, doctest ketiga contoh lulus, tiap file buggy
  berbeda tepat satu baris, test kuat lulus pada modul benar dan gagal pada modul buggy.

---

## Peran IBM Bob dalam pengembangan

IBM Bob dipakai sebagai alat bantu penulis kode, **bukan sebagai sumber kebenaran**. Setiap
langkah dikerjakan dalam tahap kecil dengan perintah berhenti di akhir tahap, hasilnya ditinjau
(`git diff`), dijalankan sendiri dengan data nyata, dan dibuktikan dengan test. Prompt
pengembangan juga disusun dalam tiga layer: peran dan batasan teknologi, tugas dan urutan
langkah, lalu aturan keluaran dan kriteria penerimaan.

---

## Log iterasi prompt

Prinsip yang dipakai: **satu masalah pada hasil = revisi pada satu layer saja**.

### A. Prompt agen (tiga layer)

**v1 -> v2.** Review sebelum dipakai menemukan empat masalah:

1. *Layer 2, celah aturan utama.* v1 membolehkan nilai harapan dihitung dengan "menjalankan
   kode secara mental" dan tetap menyebutnya berasal dari spesifikasi. Itu bertentangan dengan
   Layer 1 dan membuka jalan bagi test yang menyalin perilaku kode, termasuk yang salah.
   Perubahan: diganti larangan tegas (tidak boleh memperoleh nilai harapan dengan menjalankan,
   menelusuri, atau menyalin rumus fungsi). Dampak: aturan konsisten antarlayer.
2. *Layer 3, kontradiksi impor.* Satu aturan menyuruh impor di bagian atas file, aturan lain
   melarang impor di level modul. Perubahan: aturan kedua dihapus.
3. *Layer 2, konflik kategori 3.* "Jangan membuat test exception bila tidak dispesifikasikan"
   bertabrakan dengan "jangan melewatkan edge case". Perubahan: error handling yang tidak
   dispesifikasikan tidak dites dan hanya dicatat di ASSUMPTIONS.
4. *Hal kecil.* Format asumsi disatukan menjadi `# ASSUMPTION [A1]`, kewajiban "tanggal dibuat"
   dihapus (model akan mengarang), dan judul Layer 1 disamakan menjadi *Role & Context*.

Dampak v2 dinilai lewat review konsistensi, belum diukur dengan skor tersendiri.

**Temuan terbuka (belum direvisi).** Pada run 1, `COVERAGE SUMMARY` yang ditulis model salah
hitung: tertulis 11 test boundary untuk `score_to_grade`, padahal 10, sehingga total tertulis 45
dari 44 test sebenarnya. Angka itu klaim model yang tidak diverifikasi siapa pun. Revisi yang
diusulkan hanya di Layer 3: ganti "N test(s)" dengan daftar nama test per kategori, dan
verifikasi ringkasan secara otomatis oleh `check`.

### B. Prompt pengembangan untuk Bob

- **Plan awal Bob ternyata cacat** dan baru disetujui setelah revisi: mutant ditulis dengan nama
  file acak sehingga test akan mengimpor modul asli (semua mutant lolos, skor mendekati 0%
  tanpa error); definisi "killed" terlalu longgar (exit code apa pun selain 0); tidak ada baseline
  gate; komentar `# BUG:` pada file buggy membocorkan lokasi bug. Revisi hanya pada layer tugas.
  Dampak: skor bisa dipercaya. Kemudian dikunci dengan tes regresi "sandbox mengimpor mutant".
- **Review hasil kode** menemukan: mutant timeout tidak ikut skor, label baseline tertulis
  `SURVIVED`, exit code error tercetak sebagai nama enum, panah unicode menjadi `?` di konsol,
  dan penanda timeout `exit_code == -1` yang rapuh. Semua diperbaiki dan masing-masing
  diberi tes.
- **Cacat spesifikasi pada contoh `password_checker`:** contoh docstring `"Abcdefgh12!"` hanya
  11 karakter (aturan strong minimal 12), dan implementasi memakai `isprintable()` serta
  `islower()` padahal spesifikasi menyebut `string.punctuation` dan huruf ASCII. Ditemukan lewat
  `doctest` dan probe, lalu spesifikasi dan implementasi diselaraskan.
- **Menguji test dengan menyuntikkan bug kembali ke alat** menemukan dua celah yang tidak
  ditangkap tes awal: konstanta `True`/`False` ikut dihitung di tahap penerapan, dan `return`
  tanpa nilai dianggap titik mutasi.

---

## Keterbatasan

- **Langkah LLM manual.** Tidak ada pemanggilan API otomatis.
- **Prompt memuat seluruh source.** Padahal test seharusnya dari spesifikasi. LLM yang melihat
  badan fungsi bisa tergoda menyalin perilakunya. Mode *spec-only* belum dibuat.
- **Skor mutasi tidak membuktikan kebenaran.** 100% hanya berarti mutant dari keluarga operator
  di atas tertangkap. Spesifikasi yang salah atau bug di luar operator itu tidak terdeteksi.
- **Mutant ekuivalen** (misalnya `x + 0` menjadi `x - 0`) tidak mungkin dibunuh, jadi 100%
  tidak selalu bisa dicapai.
- **Operator yang belum dimutasi:** `//`, `%`, `**`, `in`, `is`, `not in`, `is not`, serta
  operator unary (`-x`, `not x`).
- **Konstanta level modul dan nilai default argumen ikut dimutasi**, sehingga bisa menghasilkan
  survivor bernilai rendah bila konstanta itu tidak terjangkau test.
- **Hanya file `.py` sejajar yang disalin ke sandbox.** Package (subfolder), file data, dan
  konfigurasi tidak ditangani.
- **`ast.unparse` menghilangkan komentar dan sebagian format.** Control run memakai hasil unparse.
- **Mutant dijalankan berurutan**, sehingga modul besar akan lambat.
- **Hanya Python dan pytest.** Pembacaan jumlah test bergantung pada baris ringkasan pytest
  dengan `-q`.
- **Evaluasi LLM masih terbatas** (lihat bagian hasil): satu run dengan konteks tidak bersih.
- **Teruji di Windows.** Perilaku di Linux dan macOS belum diuji langsung.

## Pengembangan lanjutan

- Mode `build-prompt --spec-only` (hanya signature dan docstring) lalu bandingkan skor mutasi
  dengan mode source penuh.
- Verifikasi otomatis `COVERAGE SUMMARY` dan `ASSUMPTIONS` terhadap isi file test.
- **Loop umpan balik survivor:** daftar mutant yang selamat dikirim kembali ke LLM dengan
  instruksi menambah test, lalu `check` diulang sampai skor naik.
- Mode pemanggilan API langsung (agen otomatis penuh).
- Operator mutasi tambahan, eksekusi mutant paralel, dan dukungan modul multi-file.
- Evaluasi lebih luas: banyak modul, beberapa model, dan percobaan dengan konteks bersih.

---

## Catatan

- `examples/sample_tests/` ditulis tangan sebagai referensi alat ukur, bukan keluaran agen.
- `prompt_out.md` di root adalah contoh keluaran `build-prompt` dan akan berubah setiap
  perintah dijalankan.
- Proyek dibuat untuk Capstone Project Hacktiv8 x IBM (Track IBM Bob).
