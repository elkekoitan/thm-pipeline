#!/usr/bin/env python3
"""Read Kontrol Paneli tab rows."""
import sys, json, subprocess
SID = sys.argv[1] if len(sys.argv) > 1 else '1n1Kto56FSLpMvnvTb3gSMza23l4sn82fxC9Fyw6q4Ic'
cmd = ['gws', 'sheets', 'spreadsheets', 'values', 'get',
       '--params', json.dumps({'spreadsheetId': SID, 'range': "'Kontrol Paneli'!A1:E12"})]
r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
d = json.loads(r.stdout)
for row in d.get('values', []):
    print(' | '.join(row))
