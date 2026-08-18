# THM Pipeline — Sessiz Müziğin Tek Adresi

Sürekli üretim / analiz / araştırma / iyileştirme döngüsü (God's Eye sistem).

## Mimari

| Servis | Dizin | Görev |
|---|---|---|
| Orchestrator | `services/orchestrator` | Cron tabanlı ana döngü motoru |
| Build Worker | `services/uploader` | 7-teknik sinematik render + mastering + 1h video üretimi |
| Scorecard (God's Eye) | `services/scorecard` | 5 boyutlu otomatik kalite karnesi (PASS≥75) |
| Uploader | `services/uploader` | YouTube Data API 14-dk part upload + quota retry |
| Research | `services/research` | 93 kategori araştırma rotasyonu, Data API tarama |
| Control Panel | `services/control_panel` | Google Sheets tetikleyici ajan |
| Live Radio | `services/live_radio` | 24/7 RTMP yayın guardian'ı |
| Web API | `services/web_api` | Durum dashboard + komut webhook'u |

## Ortam Değişkenleri

- `YOUTUBE_REFRESH_TOKEN` — YouTube Data API refresh token
- `GOOGLE_CREDS_JSON` — service account credentials (Drive/Sheets)
- `SHEETS_TRACKER_ID` — Google Sheets tracker ID
- `RTMP_KEY_RADIO1`, `RTMP_KEY_RADIO2` — 24/7 canlı yayın anahtarları
- `CHANNEL_ID` — kanal brand account ID

## Veri Dizinleri (`/data`, Docker volume)

`music/ video/ assets/ playlists/ logs/ state/ uploads/ research/ covers/`

## Komutlar

- `UPLOAD_PARTS` — hazır part'ları yükle
- `RUN_STATS` — kanal istatistiklerini topla
- `RUN_SCORECARD` — God's Eye karnesi çalıştır
- `RUN_RESEARCH` — araştırma rotasyonunu ilerlet

## Coolify Deploy

GitHub Source → Dockerfile → env secrets ekle. Port 8000 (web_api ek olarak port 3001 açılabilir).
