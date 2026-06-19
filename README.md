# EcoVessel.AI - Monolith Maritime Logistics Analytics
**Capstone Project IBM SkillsBuild x Pijak | Kelompok: pjk-gm081**

EcoVessel.AI adalah platform analitik logistik maritim multimodal cerdas yang mengintegrasikan model **Machine Learning (Random Forest Classifier)** dengan backend **FastAPI** dan database **Cloud Firestore NoSQL** untuk memprediksi volatilitas risiko pelayaran global serta kepatuhan dekarbonisasi lingkungan (ESG).

## Frontend UI/UX (Noir Style)
Antarmuka aplikasi ini dirancang menggunakan tema high-contrast black and white dengan tipografi bold (Noir Theme) untuk scannability data yang cepat dan scifi-vibe yang kuat.

### 6 Halaman & Fitur Utama Cloud System:
1. **Fleet Registry & Live Map**: Visualisasi rute pelayaran dunia berbasis peta Leaflet interaktif. Dilengkapi tabel log manifest live dengan aksi **Edit** manifest dan audit trail **Log**.
2. **AI Risk Forecast**: Pusat inferensi model Random Forest. Memilih manifes koridor pelayaran (seperti SS Sunda Strait) secara dinamis untuk menampilkan *Confidence Score* (94.1%) dan *Strategic Advisor Recommendation* otomatis.
3. **Supplier Network**: Fitur *Supplier Eco-Optimizer* untuk mengaudit emisi karbon Scope 3 dan memberikan Rekomendasi Mitra Hijau otomatis (seperti prioritas alokasi muatan ke MV Batam Express).
4. **Sustainability Audit**: Dasbor indikator ESG global untuk memantau volume emisi CO2 accumulator, target pencampuran bahan bakar alternatif, dan sulfur waste threshold compliance demi mempertahankan peringkat A-Grade.
5. **Active Alerts**: Live emergency broadcast broadcast untuk memicu alarm anomali kritis (*Critical Anomaly*) jika ada kapal yang terjebak di kluster risiko tinggi.
6. **Trend Analysis**: Menyajikan *Risk & Sustainability Balancer Matrix* bulanan serta evaluasi metrik makro seperti *Route Bottleneck Density* untuk memicu *Dynamic Rerouting*.

## Tech Stack
* **Frontend**: HTML5, Vanilla JavaScript (app.js rute relatif), TailwindCSS/Custom CSS (Manga-Noir Theme), Leaflet.js (Map Visualizer), live on Vercel.
* **Backend Engine**: Python FastAPI, Joblib Classifier, live on Vercel (Monolith Architecture).
* **Database**: Google Cloud Firestore NoSQL Database.
