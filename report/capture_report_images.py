from pathlib import Path

from playwright.sync_api import sync_playwright


BASE_URL = "http://127.0.0.1:8000"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT = Path(__file__).resolve().parent / "images"


def shot(page, name, full_page=False):
    page.screenshot(path=str(OUT / name), full_page=full_page)


def login(page, username, password):
    page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
    page.fill("input[name='username']", username)
    page.fill("input[name='password']", password)
    page.click("button[type='submit']")
    page.wait_for_load_state("networkidle")


def fake_confirm(page, text):
    page.evaluate(
        """message => {
            const overlay = document.createElement('div');
            overlay.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.55);z-index:9998;';
            const box = document.createElement('div');
            box.style.cssText = 'position:fixed;left:50%;top:18%;transform:translateX(-50%);width:820px;max-width:86vw;background:white;border-radius:24px;padding:42px;z-index:9999;box-shadow:0 24px 80px rgba(0,0,0,.35);font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;';
            box.innerHTML = `<h2 style="margin:0 0 24px;font-size:28px;">127.0.0.1:8000 says</h2>
                <p style="font-size:24px;line-height:1.45;margin:0 0 34px;">${message}</p>
                <div style="display:flex;justify-content:flex-end;gap:16px;">
                    <button style="border:0;border-radius:999px;padding:16px 34px;font-size:22px;font-weight:800;background:#eaf3e6;">Cancel</button>
                    <button style="border:0;border-radius:999px;padding:16px 42px;font-size:22px;font-weight:800;background:#596752;color:white;">OK</button>
                </div>`;
            document.body.appendChild(overlay);
            document.body.appendChild(box);
        }""",
        text,
    )


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=CHROME, headless=True)

        guest = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = guest.new_page()
        page.goto(BASE_URL, wait_until="networkidle")
        shot(page, "01_home_guest.png")
        page.goto(f"{BASE_URL}/login/", wait_until="networkidle")
        shot(page, "02_login.png")
        guest.close()

        user = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = user.new_page()
        login(page, "report_user", "reportpass123")
        shot(page, "03_home_logged_in.png")
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        shot(page, "04_latest_draw_and_admin_shortcuts.png")

        page.goto(BASE_URL, wait_until="networkidle")
        fake_confirm(page, "수동 번호를 구매하면 코인 1개가 차감됩니다. 계속 진행하시겠습니까?")
        shot(page, "09_manual_confirm.png")
        page.goto(BASE_URL, wait_until="networkidle")
        page.once("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="번호 선택하기").click()
        page.wait_for_load_state("networkidle")
        for idx, value in enumerate([1, 2, 3, 4, 5, 6], start=1):
            page.fill(f"input[name='number{idx}']", str(value))
        shot(page, "10_manual_purchase_form.png")
        page.click("button[type='submit']")
        page.wait_for_load_state("networkidle")
        shot(page, "11_manual_purchase_success.png")

        page.goto(BASE_URL, wait_until="networkidle")
        page.on("dialog", lambda dialog: dialog.accept())
        page.get_by_role("button", name="자동 구매하기").click()
        page.wait_for_load_state("networkidle")
        shot(page, "12_auto_purchase_success.png")

        page.goto(BASE_URL, wait_until="networkidle")
        fake_confirm(page, "ML 추천 번호를 구매하면 코인 2개가 차감됩니다. 계속 진행하시겠습니까?")
        shot(page, "13_ml_confirm.png")
        page.goto(BASE_URL, wait_until="networkidle")
        page.get_by_role("button", name="추천 번호 구매하기").click()
        page.wait_for_load_state("networkidle")
        shot(page, "14_ml_purchase_success.png")

        page.goto(f"{BASE_URL}/my_tickets/", wait_until="networkidle")
        shot(page, "08_my_tickets.png", full_page=True)
        page.goto(f"{BASE_URL}/admin/", wait_until="networkidle")
        shot(page, "15_django_admin_permission_denied.png")
        user.close()

        admin = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = admin.new_page()
        login(page, "report_admin", "reportpass123")
        page.goto(f"{BASE_URL}/manager/draws/", wait_until="networkidle")
        shot(page, "05_admin_draw_list.png")
        run_buttons = page.get_by_role("button", name="추첨 실행")
        if run_buttons.count() > 0:
            run_buttons.first.click()
            page.wait_for_load_state("networkidle")
        shot(page, "06_admin_draw_after_run.png")
        page.goto(f"{BASE_URL}/manager/sales/", wait_until="networkidle")
        shot(page, "07_admin_sales_report.png")
        page.goto(f"{BASE_URL}/admin/", wait_until="networkidle")
        shot(page, "16_django_admin_models.png")
        admin.close()

        browser.close()


if __name__ == "__main__":
    main()
