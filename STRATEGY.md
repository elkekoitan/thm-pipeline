# THM Instrumental — Master Strategy (v2)

Upgraded synthesis of the client's strategy document + THM BATCH 1-11 research + 36-channel benchmark.
Where research contradicted the doc, research wins (upgraded entries marked [UPGRADED]).

## 1. Channel Architecture (20 playlist matrix — client doc, upgraded)
4 focus axes: Work/Study, Sleep/Healing, Atmosphere/Venue, Nature/Frequency.
Winner categories for first 60 days (research-backed): Deep Focus/Coding, Sleep+Rain, Coffee Shop/Boutique, Car/Deep Bass, 432Hz Relief, Lofi, Jazz, Ambient Electronic, Cinematic, World Music (blue ocean: sitar/viking/celtic/guzheng/oud/acem/savanna — <1K subs incumbents).

## 2. Format Rules (research-backed)
- Long videos: 1h+ single uploads (phone verified Aug 18). Ideal loop-friendly formats [DOC said 3-8h].
- Crossfade >= 5-8s between tracks (continuous mix, no audible seams).
- Cinemagraph motion (micro-movement: rain drops, steam, flame, swaying) — our 7-technique pipeline covers this [UPGRADED: no static images].
- Mastering per category: sleep/meditation -17 LUFS + lowpass 6.5kHz + fade-in 8s; focus/lofi/nature -14 LUFS + compressor; first-30s hook mandatory (BATCH 8).
- Foley layer (-16 to -24 dB): rain, cafe cups, fireplace, wind — protects against "repetitive content" filter [DOC].
- Loop point: end matches start (same chord + foley) for loop-button watch-time stacking [DOC].
- Black screen rule: sleep/rain videos go to 100% black after ~3min for 8h versions (OLED friendly, 90%+ AVD) [DOC].
- Audio stacking 3 layers: music bed + foley + frequency layer (alpha/delta/binaural -22dB) [DOC].

## 3. SEO Templates (client doc + geo-SEO BATCH 8)
- Title: [Mood/Activity] + [Target] + [Length] + [Benefit] + [NO ADS/432Hz badge]
  e.g. "Deep Focus for Coding & Tech — 1 Hour Cyberpunk Rain & Synthwave | Alpha Waves 10Hz [No Mid-Roll Ads]"
- Description (standard): Spotify/Apple deep links line 1-2, welcome paragraph, Pomodoro chapters (25/5 timestamps), About visuals & music (royalty-free claim), Instagram + Submit, 7-language sleep line (睡眠導入/수면음악/...), No mid-roll ads line, hashtags.
- Tags clusters per category (focus/cafe/algorithm/geo).
- Localization: YouTube auto-translate metadata to JA/ZH/KO/AR/DE/FR/ES/HI (Geo-SEO agent job).
- Tier-1 targeting: English-only metadata, US/UK/DE search trends (BATCH 8: JP market 5分で寝落ち/自律神経/広告なし patterns).
- Chapters for Google key-moments indexing [DOC].

## 4. Monetization Funnel
- YouTube = traffic funnel; Spotify/Apple Music deep links (URLgenius-style app deep links) in description + pinned comment + end screen [DOC].
- B2B license certificate page ($9-10/mo, Google Form/Stripe placeholder until assets exist).
- Shorts bridge: 15s best moments, Related Video -> full mix [DOC + our shorts pipeline].
- SubmitHub/Groover curator listing once Spotify list 1K followers [DOC].
- Community polls (2x/week aesthetic GIF + poll) when eligible [DOC].

## 5. Growth Hacks Implemented
1. Loop-point algorithm trick (end=start).
2. Mobile Spotify deep linking.
3. Chapters -> Google key moments.
4. B2B license certificate CTA.
5. Curator listing revenue path.
6. Shorts bridge to long video.
7. Multilingual metadata localization.
8. Tier-1 targeted English SEO.
9. Community polls.
10. Foley layering (repetitive-content shield).
11. Live radio chatbot (bot message every 15 min in live chat).
12. Study-with-me trend tag.

## 6. Publishing Schedule (30-day calendar, upgraded to daily)
Daily 19:00 GMT+3 upload (user requirement). Week pattern (doc): 3 long + 3 shorts/week minimum.
Target: week 4 start 24/7 live radios (Radio 1: Lofi & Chill Study; Radio 2: Deep House & Car — upgraded: Radio 1 = THM Sleep & Study, Radio 2 = THM World Lounge, matching our catalog).
30-40 videos before live radio launch [DOC condition].

## 7. Production Pipeline (VPS Coolify: elkekoitan/thm-pipeline)
Services: orchestrator (cron loop), build_worker, gods_eye (QC), uploader, research_engine, control_panel, live_radio (RTMP guardian), web_api (dashboard :8000).
God's Eye QC: PASS>=75, REVIEW>=55, FAIL<55 — every mix scored before upload.

## 8. Cleanup
- Delete old 14-min part videos (replaced by full 1h uploads).
- Keep only: Fuego en la Calle, new shorts (high performers), full 1h mixes.
- 3 shorts rule: keep top 2 performers per category, delete rest.
