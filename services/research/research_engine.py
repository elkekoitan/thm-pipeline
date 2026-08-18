#!/usr/bin/env python3
"""THM Perpetual Research Engine.

Bir oturum içinde arka planda koşar; kategori rotasyonuna göre araştırma
gündemi çıkarır, her taramayı dosyaya kaydeder ve Kontrol Paneli'ne işler.
Kullanım: python3 research_engine.py --plan        (bugünkü rotasyon planı)
          python3 research_engine.py --next         (bir sonraki kategoriyi yaz)
          python3 research_engine.py --status       (durum özeti)
"""
import json, os, datetime, sys, subprocess

BASE = "/home/ubuntu/muzik/research"
CAT_DIR = os.path.join(BASE, "category")
STATE = os.path.join(BASE, "research_engine_state.json")
CATALOG = os.path.join(BASE, "GENRE_CATALOG_100.md")

LAYERS = {
    "A_producing": ["01_cinematic", "02_lofi", "03_jazz", "04_classical_piano",
                    "05_ambient_electronic", "06_deep_bass", "07_sleep_healing",
                    "08_nature", "09_epic_fantasy", "10_meditation", "11_chinese_guzheng",
                    "12_incense_ambient", "14_indian_sitar", "16_arabic_oud",
                    "17_acem_ottoman", "19_african_savanna", "22_celtic_harp",
                    "23_viking_nordic", "27_turkish_instrumental"],
    "B_sleep_study": [f"{n:02d}_{s}" for n, s in [(28, "deep_dream"), (29, "rain_storm"),
        (30, "ocean_waves"), (31, "thunder_calming"), (32, "delta_waves"),
        (33, "432hz_healing"), (34, "528hz_love"), (35, "forest_sounds"),
        (36, "night_garden"), (37, "cave_drip"), (38, "campfire"), (39, "tibetan_bowl"),
        (40, "singing_bowl_chakra"), (41, "reiki_energy"), (42, "pregnancy_relax"),
        (43, "chillhop"), (44, "jazzhop"), (45, "late_night_coding"),
        (46, "library_study"), (47, "rainy_window_study"), (48, "cafe_morning"),
        (49, "train_journey"), (50, "anime_lofi"), (51, "focus_pomodoro"),
        (52, "morning_productivity")]],
    "C_cinematic_world": [f"{n:02d}_{s}" for n, s in [(53, "trailer_cinematic"),
        (54, "space_ambient"), (55, "neo_noir"), (56, "post_rock"),
        (57, "interstellar_organic"), (58, "ancient_ruins"), (59, "fantasy_forest"),
        (60, "dragon_epic"), (61, "dark_fantasy"), (62, "medieval_tavern"),
        (63, "japanese_shakuhachi"), (64, "japanese_koto"), (65, "korean_gayageum"),
        (66, "mongolian_komuz"), (67, "mongolian_throat"), (68, "thai_ranat"),
        (69, "balinese_gamelan"), (70, "indonesian_angklung"), (71, "persian_santur"),
        (72, "persian_kamancheh"), (73, "armenian_duduk"), (74, "georgian_panduri"),
        (75, "andean_panflute"), (76, "andean_charango"), (77, "native_american_flute"),
        (78, "aboriginal_didgeridoo"), (79, "brazilian_bossa"), (80, "latin_flamenco_guitar")]],
    "D_electronic_tr": [f"{n:02d}_{s}" for n, s in [(81, "deep_house_chill"),
        (82, "synthwave"), (83, "retrowave_night_drive"), (84, "downtempo"),
        (85, "liquid_dnb"), (86, "electric_chillwave"), (87, "vaporwave_aesthetic"),
        (88, "guitar_house"), (89, "future_funk"), (90, "solar_flare_ambient"),
        (91, "ney_sufi"), (92, "kanun"), (93, "bendir_zikir"), (94, "balans_piyano"),
        (95, "balkan_gypsy"), (96, "anatolian_rock_instrumental"),
        (97, "autumn_cozy"), (98, "winter_cabin"), (99, "spring_garden"),
        (100, "summer_beach"), (101, "christmas_instrumental"), (102, "rainy_season_asia")]],
}

def load_state():
    if os.path.exists(STATE):
        return json.load(open(STATE))
    return {"order": [], "scanned": {}, "last_run": None}

def save_state(st):
    json.dump(st, open(STATE, "w"), indent=2, ensure_ascii=False)

def build_order():
    order = []
    for layer in ["A_producing", "B_sleep_study", "C_cinematic_world", "D_electronic_tr"]:
        order.extend([(layer, s) for s in LAYERS[layer]])
    return order

def cmd_plan():
    st = load_state()
    order = build_order()
    print(f"Rotasyon sırası: {len(order)} kategori (A=üretim {len(LAYERS['A_producing'])}, "
          f"B=uyku/çalışma {len(LAYERS['B_sleep_study'])}, "
          f"C=sinematik/dünya {len(LAYERS['C_cinematic_world'])}, "
          f"D=elektronik/TR {len(LAYERS['D_electronic_tr'])})")
    print("İlerleme:")
    for (layer, slug) in order:
        scanned = st["scanned"].get(slug)
        mark = scanned if scanned else "bekliyor"
        print(f"  [{layer}] {slug}: {mark}")

def cmd_next():
    st = load_state()
    for (layer, slug) in build_order():
        if slug not in st["scanned"]:
            # 30 günde bir rescan: scanned değeri tarihsel dizgi ise kontrol et
            if isinstance(st["scanned"].get(slug), str):
                try:
                    last = datetime.datetime.fromisoformat(st["scanned"][slug])
                    if (datetime.datetime.now() - last).days < 30:
                        continue
                except ValueError:
                    pass
            st["scanned"][slug] = "planned_" + datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
            save_state(st)
            os.makedirs(os.path.join(CAT_DIR, slug), exist_ok=True)
            print(json.dumps({"next": slug, "layer": layer,
                              "module": f"/home/ubuntu/muzik/research/category/{slug}/",
                              "protocol": "per_category_research.md (5 katman: rakip haritası, metrik kıyaslama, hook tersine mühendisliği, kitle coğrafyası, müzik-psikoloji kanıtı)"}))
            return
    print("Tüm kategoriler tarandı; rotasyon sıfırlanıyor ve baştan başlıyor.")
    st["scanned"] = {}
    save_state(st)
    cmd_next()

def cmd_status():
    st = load_state()
    scanned = [s for s, v in st["scanned"].items() if v and not v.startswith("planned_")]
    pending = len(build_order()) - len(st["scanned"])
    print(json.dumps({"scanned": len(scanned), "planned": len(st["scanned"]) - len(scanned),
                      "pending": pending, "last_run": st.get("last_run")}, ensure_ascii=False))

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "--status"
    {"--plan": cmd_plan, "--next": cmd_next, "--status": cmd_status}[mode]()
