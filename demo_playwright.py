"""
JCW Estimator Demo Simulation for Lynn Blueprint
------------------------------------------------

This Playwright script automates the estimator UI, uploads a blueprint,
waits for AI takeoff, runs the cost calculation, and captures screenshots.

Update PDF_PATH below with the absolute path to your Lynn blueprint.
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

# EDIT THIS: set to the full path of your Lynn blueprint PDF
PDF_PATH = r"C:\\Users\\natha\\OneDrive\\Aquisition Lab\\Deals\\JC Welton\\Post Day 1 Ops\\Estimating\\Lynn\\251020_291 SOD - Building Permit Set.pdf"
ESTIMATOR_URL = "http://localhost:8000"  # use your local server URL here

async def run_demo():
    pdf_file = Path(PDF_PATH)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_file}")

    async with async_playwright() as p:
        # Launch a visible browser window
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        # 1. Load the estimator interface
        await page.goto(ESTIMATOR_URL)
        await page.screenshot(path="01_landing.png")
        
        # 2. Switch to AI Blueprint Analysis tab
        await page.click("text=AI Blueprint Analysis")
        
        # 3. Upload the PDF
        await page.set_input_files("input[type=file]", pdf_file)
        await page.screenshot(path="02_uploaded.png")
        
        # 4. Wait for AI analysis to complete (progress bar disappears)
        await page.wait_for_selector("text=AI Takeoff Complete", timeout=120000)
        await page.screenshot(path="03_takeoff_complete.png")
        
        # 5. Trigger cost calculation
        await page.click("button:has-text('Calculate Estimate')")
        await page.wait_for_selector("text=Cost Breakdown", timeout=60000)
        await page.screenshot(path="04_final_estimate.png")
        
        print("Demo complete – screenshots saved.")
        await asyncio.sleep(30)  # leave browser open for manual review
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_demo())
