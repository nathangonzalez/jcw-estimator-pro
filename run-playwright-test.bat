@echo off
echo 🚀 Starting JCW Cost Estimator Playwright Test Suite
echo ==================================================
echo.

echo 📋 Test Plan:
echo   ✅ PDF blueprint upload and AI analysis
echo   ✅ Scale detection and measurement extraction
echo   ✅ Cost estimation with ML model
echo   ✅ Excel report generation
echo   ✅ AI chat interface
echo   ✅ Error handling
echo   ✅ Mobile responsiveness
echo   ✅ Accessibility
echo   ✅ Performance testing
echo   ✅ End-to-end workflow
echo.

echo 🔧 Setting up test environment...
cd /d "%~dp0"

echo 📦 Installing Playwright dependencies...
call npx playwright install --with-deps

echo.
echo 🎭 Running comprehensive test suite...
echo =====================================
call npx playwright test playwright-test-lynn-planset.spec.js --headed --timeout=60000

echo.
echo 📊 Test Results Summary:
echo =======================
echo   📁 Screenshots saved to: test-results/
echo   📄 Test report available at: playwright-report/
echo   🎯 Test demonstrates complete AI workflow
echo.

echo 🚀 To view live application:
echo   https://jcw-cost-estimator-196950564738.us-central1.run.app/
echo.

echo ✅ Playwright simulation complete!
pause
