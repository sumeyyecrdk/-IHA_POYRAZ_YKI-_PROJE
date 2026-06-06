# -IHA_POYRAZ_YK-_PROJE
Bu proje, MAVLink protokolü üzerinden İHA'dan gelen telemetri verilerini alarak gerçek zamanlı bir yer kontrol arayüzü sunar.

# ÖZELLİKLER
- Gerçek zamanlı irtifa,hız,yön ve batarya takibi
- Uçuş modu görüntüleme
- Canlı harita üzerinde İHA konumunu gösterme
- PyQt5 tabanlı grafik arayüz
- MAVLink bağlantısı ile sürekli veri akışı

# KULLANILAN TEKNOLOJİLER
- Python
- PyQt5
- pymavlink
- Folium
- QWebEngineView


# ÇALIŞMA MANTIĞI
İHA'dan gelen MAVLink mesajlari arka planda ayrı bir thread ile okunur ve arayüz anlık olarak güncellenir. Konum verisi değiştiğinde harita otomatik yenilenir.
