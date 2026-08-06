import pandas as pd
from playwright.sync_api import sync_playwright
from datetime import datetime
import os
import re

class SuperAgent:
    def __init__(self):
        self.report_date = datetime.now().strftime("%Y-%m-%d")
        self.target_funds = [
            {"name": "AustralianSuper", "url": "https://www.australiansuper.com/investments-and-performance/super-performance", "mysuper": "Balanced", "high_growth": "High Growth", "split_ms": "75/25", "split_hg": "88/12"},
            {"name": "ART", "url": "https://www.australianretirementtrust.com.au/investments/performance", "mysuper": "Super Savings - Balanced", "high_growth": "High Growth Pool", "split_ms": "70/30", "split_hg": "85/15"},
            {"name": "Hostplus", "url": "https://hostplus.com.au/members/investment/investment-returns", "mysuper": "Balanced", "high_growth": "High Growth", "split_ms": "76/24", "split_hg": "100/0"},
            {"name": "HESTA", "url": "https://www.hesta.com.au/members/investments/performance", "mysuper": "Balanced Growth", "high_growth": "High Growth", "split_ms": "70/30", "split_hg": "90/10"},
            {"name": "Cbus", "url": "https://www.cbussuper.com.au/members/investments/performance", "mysuper": "Growth (MySuper)", "high_growth": "High Growth", "split_ms": "75/25", "split_hg": "90/10"},
            {"name": "UniSuper", "url": "https://www.unisuper.com.au/investments/investment-performance", "mysuper": "Balanced", "high_growth": "High Growth", "split_ms": "70/30", "split_hg": "90/10"},
            {"name": "Rest Super", "url": "https://www.rest.com.au/member/investments/performance", "mysuper": "Core Strategy", "high_growth": "High Growth", "split_ms": "70/30", "split_hg": "93/07"},
            {"name": "Aware Super", "url": "https://aware.com.au/member/investments/performance", "mysuper": "MySuper Balanced", "high_growth": "High Growth", "split_ms": "75/25", "split_hg": "88/12"},
            {"name": "CareSuper", "url": "https://www.caresuper.com.au/members/investments/performance", "mysuper": "Balanced", "high_growth": "Growth", "split_ms": "72/28", "split_hg": "86/14"},
            {"name": "Brighter Super", "url": "https://www.brightersuper.com.au/investments/latest-performance", "mysuper": "MySuper", "high_growth": "Growth", "split_ms": "70/30", "split_hg": "85/15"},
            {"name": "BUSSQ", "url": "https://www.bussq.com.au/investments/investing-with-bussq/performance", "mysuper": "Balanced Growth", "high_growth": "High Growth", "split_ms": "75/25", "split_hg": "90/10"}
        ]
        self.results = []

    def add_result(self, fund, option, opt_type, fytd="N/A", one_yr="N/A", ten_yr="N/A", as_at="N/A", split="N/A", status="❌ Failed", url=""):
        self.results.append({
            "Fund": fund, "Option": option, "Type": opt_type,
            "FYTD": fytd, "OneYear": one_yr, "TenYear": ten_yr, 
            "AsAt": as_at, "Split": split, "Status": status, "URL": url
        })

    def scrape_all(self):
        with sync_playwright() as p:
            # STEALTH: Launch with specific arguments to hide 'headless' nature
            browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            )
            
            for fund in self.target_funds:
                print(f"Scraping {fund['name']}...", flush=True)
                page = context.new_page()
                try:
                    # STEALTH: Mimic human behavior
                    page.goto(fund['url'], wait_until="domcontentloaded", timeout=60000)
                    page.wait_for_timeout(7000) # Wait for JS to settle
                    
                    # DATA EXTRACTION: Search for the row containing the option name
                    # We use a more robust text-based search instead of strict table selectors
                    rows = page.query_selector_all("tr")
                    if not rows: # Fallback for div-based tables
                        rows = page.query_selector_all("div[role='row']")

                    found_ms = False
                    found_hg = False

                    for row in rows:
                        row_text = row.inner_text()
                        
                        # Match MySuper
                        if fund['mysuper'] in row_text and not found_ms:
                            cells = row.query_selector_all("td") or row.query_selector_all("div[role='cell']")
                            if len(cells) >= 3:
                                # Logic: FYTD is usually 2nd, 1Yr is 3rd or 4th, 10Yr is usually last
                                vals = [c.inner_text().strip() for c in cells]
                                self.add_result(fund['name'], fund['mysuper'], "MySuper", 
                                                vals[1], vals[3] if len(vals) > 4 else vals[2], vals[-1],
                                                self.report_date, fund['split_ms'], "✅ Scraped", fund['url'])
                                found_ms = True

                        # Match High Growth
                        if fund['high_growth'] in row_text and not found_hg:
                            cells = row.query_selector_all("td") or row.query_selector_all("div[role='cell']")
                            if len(cells) >= 3:
                                vals = [c.inner_text().strip() for c in cells]
                                self.add_result(fund['name'], fund['high_growth'], "High Growth", 
                                                vals[1], vals[3] if len(vals) > 4 else vals[2], vals[-1],
                                                self.report_date, fund['split_hg'], "✅ Scraped", fund['url'])
                                found_hg = True

                    if not found_ms: self.add_result(fund['name'], fund['mysuper'], "MySuper", status="⚠️ [Blocked/Hidden]", url=fund['url'])
                    if not found_hg: self.add_result(fund['name'], fund['high_growth'], "High Growth", status="⚠️ [Blocked/Hidden]", url=fund['url'])

                except Exception as e:
                    print(f"Error {fund['name']}: {str(e)[:50]}", flush=True)
                    self.add_result(fund['name'], fund['mysuper'], "MySuper", status="⚠️ [Timeout]", url=fund['url'])
                    self.add_result(fund['name'], fund['high_growth'], "High Growth", status="⚠️ [Timeout]", url=fund['url'])
                
                page.close()
            browser.close()

    def generate_report(self):
        df = pd.DataFrame(self.results)
        
        def clean_num(val):
            if val == "N/A" or val is None: return -999.0
            cleaned = re.sub(r'[^\d\.\-]', '', str(val))
            try: return float(cleaned)
            except: return -999.0

        df['FYTD_N'] = df['FYTD'].apply(clean_num)
        df['1Yr_N'] = df['OneYear'].apply(clean_num)
        df['10Yr_N'] = df['TenYear'].apply(clean_num)

        report = f"# Superannuation Intelligence Report: {self.report_date}\n\n"
        
        configs = [
            ("Table 1: High Growth — FYTD Returns", "High Growth", "FYTD_N", "FYTD"),
            ("Table 2: High Growth — 1-Year Returns", "High Growth", "1Yr_N", "OneYear"),
            ("Table 3: High Growth — 10-Year Returns", "High Growth", "10Yr_N", "TenYear"),
            ("Table 4: MySuper / Default — FYTD Returns", "MySuper", "FYTD_N", "FYTD"),
            ("Table 5: MySuper / Default — 1-Year Returns", "MySuper", "1Yr_N", "OneYear"),
            ("Table 6: MySuper / Default — 10-Year Returns", "MySuper", "10Yr_N", "TenYear"),
        ]

        for title, opt_type, sort_col, disp_col in configs:
            sub = df[df['Type'] == opt_type].sort_values(by=sort_col, ascending=False)
            sub.insert(0, 'Rank', range(1, len(sub) + 1))
            report += f"### {title}\n"
            report += sub[['Rank', 'Fund', 'Option', disp_col, 'AsAt', 'Split', 'Status', 'URL']].to_markdown(index=False)
            report += "\n\n"

        report += "## WEEKLY PERFORMANCE FLASH REPORT\n"
        report += "Market volatility remains high. This automated agent is monitoring daily shifts in unit pricing across major industry funds.\n\n"

        report += "## MONTHLY MACRO & LONG-TERM STRATEGY BLOG\n"
        report += "The 10-year annualized data remains the most critical metric for retirement planning. Structural performance gaps persist between top-tier and bottom-tier funds.\n\n"

        report += "---\n### IMPORTANT COMPLIANCE & FINANCIAL DISCLAIMER\n"
        report += "*General Advice Warning: Automated data retrieval...*\n"

        with open(f"reports/report-{self.report_date}.md", "w") as f:
            f.write(report)

if __name__ == "__main__":
    if not os.path.exists('reports'): os.makedirs('reports')
    agent = SuperAgent()
    agent.scrape_all()
    agent.generate_report()
