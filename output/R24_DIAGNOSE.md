# R2.4 Demo Hot Keys & Overlays - Diagnostics

## Issues Found

### V3 Reel Build Issues
- **Text escaping failure**: ffmpeg drawtext filter failed to parse complex text with newlines and special characters in intro slate
- **Insufficient videos**: Only 2 videos found out of 15 tests (most API tests don't record videos)
- **Font path issues**: Windows path escaping in ffmpeg commands

### Finance Overlay
- **Missing finance data**: `output/finance/forecast.json` not found
- **Non-fatal**: Overlay correctly skips when data unavailable

### Test Results
- **7 failed tests**: Backend API issues (expected for demo environment)
- **13 passed tests**: Core functionality working
- **Real UI videos**: 2 videos captured from story tests

## Next Actions
1. **Fix ffmpeg text escaping**: Use simpler text or pre-render text overlays as PNG
2. **Increase video coverage**: Configure more tests to record videos or use synthetic clips
3. **Font fallback**: Implement better font detection and fallback to no-font mode
4. **Finance data**: Generate sample forecast.json for demo purposes
5. **Test reliability**: Fix backend API issues causing test failures

## Current Status
- ✅ Hot-keys menu functional
- ✅ Archive system working
- ✅ V2 reel generation working
- ✅ HTTP serving working
- ⚠️ V3 clips need video coverage improvement
- ⚠️ Finance overlay needs data source
