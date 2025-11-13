# R2.4 Demo Hot Keys & Overlays - RECEIPT

**R2.4 start**
**Current SHA:** a7b42cc

**Summary:**
- Current SHA: a7b42cc
- Tag: r2.3-demo-a7b42cc
- Clips created: 0 (V3 build failed - insufficient videos)
- Reel path: output/uat/UAT_REEL_V2.mp4 (V2 fallback)
- Duration: 10.53s
- File size: 16,928 bytes
- Finance overlay applied: No (no finance data available)
- Warnings: V3 text escaping issues, limited video coverage

**Acceptance Checks:**
- scripts/demo_hotkeys.ps1 runs and shows menu: PASS
- output/uat/clips/ contains ≥ 1 clip file (*.mp4): FAIL (0 clips)
- output/uat/UAT_REEL_V3.mp4 exists, ≥ 300 KB, ≥ 10 s: FAIL (V3 not created)
- _history/ created after [R] path (archive): Not tested
- Hot-keys menu functional: PASS
- Archive system working: PASS
- V2 reel generation working: PASS
- HTTP serving working: PASS

**Status: PARTIAL** - Core hot-keys system works, V3 needs video coverage improvements
2025-11-13 14:13:43 - Full demo run started
