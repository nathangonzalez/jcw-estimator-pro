# scripts/install_playwright.ps1
# Installs Playwright deps in a supervised way. Do NOT run unless approval is present.
# Safe flags: --no-fund --no-audit to avoid network telemetry noise in CI.

npm install --no-fund --no-audit --save-dev @playwright/test playwright

# Install browser dependencies. On Windows this is harmless; required on CI/Linux.
npx playwright install --with-deps
