#Python'ın sistemle yani bilgisayarın kendisiyle iletişim kurmasını sağlayan kütüphane import edildi.
import sys
#Python'da input/output işlemlerini yönetmek için kullanılan kütüphane import edildi.
import io
#GUI,MAVLınk ve harita işlemleri için gerekli modüller import edildi.
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QThread, pyqtSignal
from pymavlink import mavutil
import folium


#MAVLink telemetri verilerinin arayüzü dondurmadan arka planda sürekli okunmasını sağlayan bir sınıf yaratıldı.
class MAVLinkVeriIsleyici(QThread):
    telemetri_sinyali = pyqtSignal(dict)

    def run(self):
        baglanti_adresi = 'tcp:127.0.0.1:5762'
        try:
            iha = mavutil.mavlink_connection(baglanti_adresi)
        except Exception as e:
            print(f"Hata: {e}")
            return

        while True:
            msg = iha.recv_match(blocking=True)
            if not msg: continue

            veri = {}
            
            if msg.get_type() == 'VFR_HUD':
                veri['yer_hizi'] = msg.groundspeed
                veri['yon'] = msg.heading
                veri['dikey_hiz'] = msg.climb

            elif msg.get_type() == 'GLOBAL_POSITION_INT':
                #değer mm'den m'ye çevrildi.
                veri['irtifa'] = msg.relative_alt / 1000.0

                #enlem ve boylam ölçeklendirilerek derece formatına çevrildi.
                veri['lat'] = msg.lat / 1.0e7
                veri['lon'] = msg.lon / 1.0e7
                
            elif msg.get_type() == 'SYS_STATUS':
                veri['batarya'] = msg.battery_remaining

            elif msg.get_type() == 'HEARTBEAT':
                #uçuş modu kodlanmış bit halinden okunabilir string haline getirildi.
                veri['mod'] = mavutil.mode_string_v10(msg)
            
            #hazırlanan veri arayüze gönderildi.
            if veri:
                self.telemetri_sinyali.emit(veri)

#Ana pencere yapısını oluşturan sınıf yaratıldı.
class YerControlPenceresi(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("POYRAZ TAKIMI - Optimize YKİ")
        self.setGeometry(100, 100, 1000, 700)
        
        # Harita yenileme sıklığını kontrol etmek için değişkenler yaratıldı.
        self.son_lat = 0
        self.son_lon = 0

        self.irtifa_yazisi = QLabel("İrtifa: -- m")
        self.yer_hizi_yazisi = QLabel("Yere Göre Hız: -- m/s")
        self.mod_yazisi = QLabel("Mod: --")
        self.batarya_yazisi = QLabel("Batarya: %--")
        self.yon_yazisi = QLabel("Yön: --°")
        self.dikey_hiz_yazisi = QLabel("Dikey Hız: -- m/s")
        self.harita_kutusu = QWebEngineView()

        #Yatay bir düzen oluşturuldu.w değişkeni veriler içinde gezdirildi ve bu yatay düzene veriler eklendi.
        ust_panel = QHBoxLayout()
        for w in [self.irtifa_yazisi, self.yer_hizi_yazisi, self.mod_yazisi, self.batarya_yazisi,self.yon_yazisi,self.dikey_hiz_yazisi]:
            ust_panel.addWidget(w)

        #Dikey bir düzen oluşturuldu.
        ana_duzen = QVBoxLayout()
        ana_duzen.addLayout(ust_panel)
        ana_duzen.addWidget(self.harita_kutusu)
        
        merkez = QWidget()
        merkez.setLayout(ana_duzen)
        self.setCentralWidget(merkez)

        #Arka planda çalışacak veri motoru hazırlandı.Bu veri ile ekrandaki güncelleme burada bağlandı.
        self.isleyici = MAVLinkVeriIsleyici()
        self.isleyici.telemetri_sinyali.connect(self.arayuzu_guncelle)
        self.isleyici.start()

    #Arka plandan gelen veriyi alıp ekrana yansıtan bir fonksiyon oluşturuldu.
    def arayuzu_guncelle(self, gelen_veri):

        # Ekrandaki yazıyı canlı olarak güncelleyen ifadeler yazıldı.
        if 'irtifa' in gelen_veri:
            self.irtifa_yazisi.setText(f"İrtifa: {gelen_veri['irtifa']:.2f} m")
        if 'yer_hizi' in gelen_veri:
            self.yer_hizi_yazisi.setText(f"Yere Göre Hız: {gelen_veri['yer_hizi']:.2f} m/s")
        if 'mod' in gelen_veri:
            self.mod_yazisi.setText(f"Mod: {gelen_veri['mod']}")
        if 'batarya' in gelen_veri:
            self.batarya_yazisi.setText(f"Batarya: %{gelen_veri['batarya']}")
        if 'yon' in gelen_veri:
            self.yon_yazisi.setText(f"Yön: {gelen_veri['yon']}°")
        if 'dikey_hiz' in gelen_veri:
            self.dikey_hiz_yazisi.setText(f"Dikey Hız: {gelen_veri['dikey_hiz']:.2f} m/s")
        # Yeni gelen konumun eski gelen konumdan gerçekten farklı olup olmadığı kontrol edildi.
        if 'lat' in gelen_veri:
            # Harita yalnızca konum anlamlı şekilde değiştiği zaman güncellendi.
            if round(gelen_veri['lat'], 4) != round(self.son_lat, 4) or \
               round(gelen_veri['lon'], 4) != round(self.son_lon, 4):
                self.son_lat = gelen_veri['lat']
                self.son_lon = gelen_veri['lon']
                self.haritayi_yenile(self.son_lat, self.son_lon)

    #İHA'nın yeni konumuna göre harita yenilendi, üzerine pin işareti konuldu ve ekranda gösterildi.
    def haritayi_yenile(self, lat, lon):
        harita = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat, lon], popup="İHA").add_to(harita)
        data = io.BytesIO()
        harita.save(data, close_file=False)
        self.harita_kutusu.setHtml(data.getvalue().decode())

#PyQt uygulaması başlatıldı,pencere oluşturuldu-ekranda gösterildi ve program sürekli çalışır halde tutuldu.
if __name__ == "__main__":
    app = QApplication(sys.argv)
    pencere = YerControlPenceresi()
    pencere.show()
    sys.exit(app.exec_())