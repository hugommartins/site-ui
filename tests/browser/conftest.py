"""Playwright fixtures for the L4 tests. Run pytest from the repo root: the tests open demo.html from disk."""
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
DEMO = (ROOT / 'demo.html').as_uri()

# demo.html ?site= value -> the site it stands for
SITES = ['garden', 'bookshelf', 'studio']
WIDTHS = [1000, 700, 390, 320]


@pytest.fixture(scope='session')
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


@pytest.fixture
def open_demo(browser):
    """open_demo(site, width, theme=None, storage=None) -> page. Closes every page it made."""
    pages = []

    def go(site, width, theme=None, height=800):
        ctx = browser.new_context(viewport={'width': width, 'height': height},
                                  color_scheme='dark' if theme == 'dark' else 'light')
        pages.append(ctx)
        page = ctx.new_page()
        page.goto(f'{DEMO}?site={site}')
        return page

    yield go
    for c in pages:
        c.close()
