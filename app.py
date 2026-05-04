"""
TaskMate AI — Personal Productivity Assistant
Final Project: AI Chatbot berbasis LLM
"""

import os
import streamlit as st
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# ──────────────────────────────────────────────
# Page configuration
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="TaskMate AI",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ──────────────────────────────────────────────
# API Key — dari Streamlit secrets atau env var
# ──────────────────────────────────────────────
def load_api_key() -> str | None:
    try:
        return st.secrets["GOOGLE_API_KEY"]
    except (KeyError, FileNotFoundError):
        return os.environ.get("GOOGLE_API_KEY")


api_key = load_api_key()
if not api_key:
    st.error(
        "**API Key tidak ditemukan.**\n\n"
        "Tambahkan `GOOGLE_API_KEY` di:\n"
        "- File `.streamlit/secrets.toml` → `GOOGLE_API_KEY = 'key_anda'`\n"
        "- Atau variabel environment: `export GOOGLE_API_KEY='key_anda'`"
    )
    st.stop()

genai.configure(api_key=api_key)

# ──────────────────────────────────────────────
# Sistem prompt berdasarkan gaya bahasa
# ──────────────────────────────────────────────
SYSTEM_PROMPTS = {
    "Formal": """Anda adalah TaskMate AI, asisten produktivitas pribadi profesional untuk pekerja kantoran.

Peran Anda:
- Membantu pengguna merencanakan tugas harian dengan terstruktur
- Memberikan saran prioritisasi pekerjaan berdasarkan urgensi dan dampak
- Merangkum tujuan dan pencapaian secara ringkas
- Memberikan rekomendasi tindakan konkret berikutnya
- Menyarankan strategi produktivitas yang telah terbukti efektif

Panduan komunikasi:
- Gunakan bahasa Indonesia yang formal dan profesional
- Sapa pengguna dengan "Anda"
- Berikan saran dalam format poin-poin yang terstruktur
- Gunakan matriks Eisenhower (urgensi vs. kepentingan) saat memprioritaskan
- Ajukan pertanyaan klarifikasi jika masukan pengguna kurang jelas
- Hindari klaim yang tidak berdasar; fokus pada saran yang dapat ditindaklanjuti

Selalu jawab dalam Bahasa Indonesia.""",

    "Santai": """Kamu adalah TaskMate AI, teman produktivitas yang asik dan helpful buat karyawan kantoran.

Peran kamu:
- Bantu kamu merencanakan tugas-tugas harian dengan cara yang simpel dan efektif
- Kasih saran gimana cara prioritasin kerjaan biar gak overwhelming
- Rangkum tujuan dan progress dengan bahasa yang gampang dipahami
- Rekomendasiin langkah-langkah konkret yang bisa langsung dilakuin
- Share tips produktivitas yang praktis dan bisa langsung dipraktekin

Panduan komunikasi:
- Pakai bahasa Indonesia yang santai dan friendly
- Sapa pengguna dengan "kamu"
- Boleh pakai emoji secukupnya biar lebih ekspresif
- Format saran dalam poin-poin yang simpel dan mudah dibaca
- Tanya balik kalau kurang jelas maksudnya apa
- Tetap helpful dan to-the-point

Selalu jawab dalam Bahasa Indonesia.""",

    "Motivasional": """Kamu adalah TaskMate AI, asisten produktivitas yang super energik dan selalu memotivasi para pekerja kantoran!

Peran kamu:
- Membantu merencanakan tugas harian dengan semangat dan antusias
- Memberikan saran prioritisasi yang membangkitkan kepercayaan diri
- Merangkum tujuan dengan cara yang inspiratif dan memotivasi
- Memberikan rekomendasi tindakan yang disertai dorongan semangat
- Mengingatkan pengguna akan potensi luar biasa yang mereka miliki

Panduan komunikasi:
- Gunakan bahasa Indonesia yang penuh semangat dan positif
- Mulai respon dengan afirmasi atau kata-kata motivasi
- Sapa pengguna dengan "kamu" dan tunjukkan kepercayaan pada kemampuan mereka
- Gunakan kata-kata yang memberdayakan: "Kamu pasti bisa!", "Luar biasa!", dll
- Format saran dalam poin-poin yang actionable dan inspiring
- Ubah tantangan menjadi peluang dalam setiap respons
- Gunakan emoji untuk menambah energi positif 🚀✨💪

Selalu jawab dalam Bahasa Indonesia dengan penuh semangat!""",
}

# ──────────────────────────────────────────────
# Kata kunci untuk fitur rekomendasi cepat
# ──────────────────────────────────────────────
RECOMMENDATION_KEYWORDS = [
    "bingung", "tidak tahu", "gak tau", "banyak tugas", "prioritas",
    "deadline", "menunda", "procrastinate", "kewalahan", "overwhelmed",
    "burn out", "burnout", "capek", "lelah", "stres", "stress",
    "tidak produktif", "gak produktif", "mulai dari mana", "banyak kerjaan",
]

QUICK_RECOMMENDATIONS = [
    "📋 **Buat daftar tugas** hari ini dan tandai yang paling penting",
    "⏱️ **Gunakan teknik Pomodoro**: fokus 25 menit, istirahat 5 menit",
    "🎯 **Pilih 3 tugas utama** (MIT - Most Important Tasks) untuk diselesaikan hari ini",
    "📊 **Prioritaskan dengan matriks**: mana yang Penting & Mendesak terlebih dahulu",
    "🧘 **Ambil napas dalam** dan mulai dengan tugas terkecil untuk membangun momentum",
    "📱 **Matikan notifikasi** selama sesi kerja fokus berikutnya",
]


def should_show_recommendations(user_input: str) -> bool:
    text = user_input.lower()
    return any(keyword in text for keyword in RECOMMENDATION_KEYWORDS)


def get_recommendations(user_input: str) -> list[str]:
    import random
    text = user_input.lower()
    recs = []
    # Prioritaskan rekomendasi yang relevan
    if any(k in text for k in ["deadline", "besok", "sekarang", "mendesak"]):
        recs.append("🎯 **Fokus sekarang**: Tulis 3 hal yang HARUS selesai hari ini")
        recs.append("⏰ **Time-box**: Alokasikan waktu spesifik untuk setiap tugas")
    if any(k in text for k in ["banyak tugas", "kewalahan", "overwhelmed", "prioritas"]):
        recs.append("📊 **Prioritaskan dengan matriks Eisenhower**: Penting vs Mendesak")
        recs.append("📋 **Delegasikan** tugas yang bisa dikerjakan orang lain")
    if any(k in text for k in ["menunda", "procrastinate", "mulai dari mana"]):
        recs.append("🚀 **Aturan 2 menit**: Jika butuh < 2 menit, lakukan sekarang juga")
        recs.append("🧩 **Pecah tugas besar** menjadi langkah-langkah kecil yang konkret")
    if any(k in text for k in ["burn out", "burnout", "capek", "lelah", "stres"]):
        recs.append("🧘 **Istirahat sejenak**: 10 menit jalan kaki bisa menyegarkan pikiran")
        recs.append("💤 **Tidur cukup**: Produktivitas dimulai dari istirahat yang berkualitas")

    # Tambah rekomendasi umum jika kurang dari 3
    random.shuffle(QUICK_RECOMMENDATIONS)
    for rec in QUICK_RECOMMENDATIONS:
        if rec not in recs and len(recs) < 3:
            recs.append(rec)

    return recs[:3]


# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.title("✅ TaskMate AI")
    st.caption("*Personal Productivity Assistant*")
    st.divider()

    st.subheader("⚙️ Pengaturan")

    gaya_bahasa = st.selectbox(
        "Gaya Bahasa",
        options=["Formal", "Santai", "Motivasional"],
        index=0,
        help="Pilih gaya komunikasi asisten",
    )

    st.divider()
    st.subheader("🔧 Parameter Model")

    temperature = st.slider(
        "Temperature",
        min_value=0.0,
        max_value=1.0,
        value=0.7,
        step=0.05,
        help="Kreativitas respon: lebih tinggi = lebih kreatif, lebih rendah = lebih konsisten",
    )

    top_p = st.slider(
        "Top-P",
        min_value=0.0,
        max_value=1.0,
        value=0.9,
        step=0.05,
        help="Nucleus sampling: mengontrol keragaman token yang dipilih",
    )

    max_output_tokens = st.slider(
        "Max Output Tokens",
        min_value=256,
        max_value=8192,
        value=2048,
        step=256,
        help="Panjang maksimum respons yang dihasilkan",
    )

    st.divider()

    with st.expander("📚 Fitur TaskMate AI", expanded=False):
        st.markdown("""
**TaskMate AI dapat membantu Anda:**

- 📋 **Perencanaan tugas harian** — Susun dan atur prioritas pekerjaan
- 🎯 **Prioritisasi kerja** — Identifikasi tugas terpenting dengan metode terbukti
- 📝 **Ringkasan tujuan** — Rangkum target dan pencapaian secara singkat
- 💡 **Saran produktivitas** — Tips dan strategi kerja efektif
- ➡️ **Rekomendasi langkah berikutnya** — Tindakan konkret yang bisa langsung dilakukan
- 🔄 **Manajemen energi** — Saran menjaga fokus dan menghindari kelelahan

---
**Cara menggunakan:**
1. Pilih gaya bahasa yang Anda suka
2. Ceritakan tugas atau tantangan Anda
3. Tanyakan saran, jadwal, atau strategi
        """)

    st.divider()

    if st.button("🗑️ Reset Percakapan", use_container_width=True, type="secondary"):
        st.session_state.messages = []
        st.rerun()

    st.divider()
    st.caption("Powered by Google Gemini | Built with Streamlit")

# ──────────────────────────────────────────────
# Session state — menyimpan riwayat percakapan
# ──────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# ──────────────────────────────────────────────
# Header utama
# ──────────────────────────────────────────────
st.title("✅ TaskMate AI")
st.markdown(
    f"*Asisten produktivitas pribadi Anda — Gaya: **{gaya_bahasa}***"
)

# Pesan sambutan jika percakapan baru
if not st.session_state.messages:
    welcome_messages = {
        "Formal": "Selamat datang di **TaskMate AI**. Saya siap membantu Anda merencanakan tugas, memprioritaskan pekerjaan, dan meningkatkan produktivitas Anda. Apa yang dapat saya bantu hari ini?",
        "Santai": "Hei! Selamat datang di **TaskMate AI** 👋 Gue siap bantu kamu ngatur kerjaan dan bikin hari kamu lebih produktif. Cerita dong, ada apa hari ini?",
        "Motivasional": "Halo, superstar! 🌟 Selamat datang di **TaskMate AI**! Hari ini adalah kesempatan luar biasa untuk mencapai hal-hal menakjubkan! Ayo cerita, apa yang akan kita taklukkan hari ini? 💪🚀",
    }
    with st.chat_message("assistant"):
        st.markdown(welcome_messages[gaya_bahasa])

# ──────────────────────────────────────────────
# Tampilkan riwayat percakapan
# ──────────────────────────────────────────────
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ──────────────────────────────────────────────
# Input chat dan generasi respons
# ──────────────────────────────────────────────
if user_input := st.chat_input("Ceritakan tugas atau tujuan Anda hari ini..."):
    # Tampilkan pesan pengguna
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Bangun history percakapan untuk Gemini
    # Format: alternating user/model, diawali system instruction
    gemini_history = []
    for msg in st.session_state.messages[:-1]:  # semua kecuali pesan terakhir
        role = "user" if msg["role"] == "user" else "model"
        gemini_history.append({"role": role, "parts": [msg["content"]]})

    # Konfigurasi model dan parameter
    generation_config = genai.GenerationConfig(
        temperature=temperature,
        top_p=top_p,
        max_output_tokens=max_output_tokens,
    )

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=generation_config,
        system_instruction=SYSTEM_PROMPTS[gaya_bahasa],
    )

    # Mulai sesi chat dengan history
    chat_session = model.start_chat(history=gemini_history)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        assistant_reply = ""
        try:
            response = chat_session.send_message(user_input, stream=True)
            for chunk in response:
                if chunk.text:
                    assistant_reply += chunk.text
                    placeholder.markdown(assistant_reply + "▌")
            placeholder.markdown(assistant_reply)
        except Exception as e:
            assistant_reply = (
                f"Maaf, terjadi kesalahan saat menghubungi API: `{e}`\n\n"
                "Pastikan API key Anda valid dan kuota masih tersedia."
            )
            placeholder.markdown(assistant_reply)

        # Fitur rekomendasi cepat
        if should_show_recommendations(user_input):
            recommendations = get_recommendations(user_input)
            st.info(
                "**💡 Rekomendasi Cepat untuk Anda:**\n\n"
                + "\n".join(f"- {r}" for r in recommendations)
            )

    # Simpan respons asisten ke history
    st.session_state.messages.append(
        {"role": "assistant", "content": assistant_reply}
    )
