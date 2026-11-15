"""L4: the header on demo.html, per site, at 1000, 700, 390 and 320px.

demo.html links the real package files, so this tests what the sites ship.
"""
import pytest

from conftest import DEMO, SITES, WIDTHS

PARAMS = [(s, w) for s in SITES for w in WIDTHS]
IDS = [f'{s}-{w}' for s, w in PARAMS]


def box(page, sel):
    return page.locator(sel).first.bounding_box()


@pytest.mark.parametrize('site,width', PARAMS, ids=IDS)
def test_no_horizontal_overflow(open_demo, site, width):
    page = open_demo(site, width)
    sw = page.evaluate('document.documentElement.scrollWidth')
    assert sw <= width, f'page is {sw}px wide in a {width}px viewport'
    nav = page.evaluate('''() => { const n = document.querySelector('.nav-inner'); return n.scrollWidth - n.clientWidth }''')
    assert nav <= 0, 'the header content overflows its bar'


@pytest.mark.parametrize('site,width', PARAMS, ids=IDS)
def test_brand_swaps_at_560(open_demo, site, width):
    page = open_demo(site, width)
    name_visible = page.locator('.nav .brand-name').is_visible()
    icon_visible = page.locator('.nav .brand svg').is_visible()
    if width > 560:
        assert name_visible and not icon_visible, 'above 560px the header shows the name, not the icon'
    else:
        assert icon_visible and not name_visible, 'at 560px and below the header shows the icon, not the name'


@pytest.mark.parametrize('site,width', PARAMS, ids=IDS)
def test_accessible_names(open_demo, site, width):
    page = open_demo(site, width)
    brand = page.locator('.nav .brand').get_attribute('aria-label') or ''
    assert brand.endswith('home') and len(brand) > len('home'), f'brand link name is {brand!r}'
    assert page.locator('.nav .theme').get_attribute('aria-label') == 'Toggle theme'


@pytest.mark.parametrize('site', SITES)
def test_axe_header(open_demo, site):
    axe_mod = pytest.importorskip('axe_playwright_python.sync_playwright', reason='pip install axe-playwright-python')
    for width in (1000, 390):
        page = open_demo(site, width)
        res = axe_mod.Axe().run(page, context='.nav')
        bad = [v for v in res.response['violations'] if v['impact'] in ('serious', 'critical')]
        assert not bad, [f"{v['id']}: {v['help']}" for v in bad]


@pytest.mark.parametrize('site', SITES)
def test_toggle_flips_and_persists(open_demo, site):
    page = open_demo(site, 1000, theme='light')
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == 'light'
    page.click('.nav .theme')
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == 'dark'
    assert page.evaluate("localStorage.getItem('theme')") == 'dark'
    page.reload()
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == 'dark', 'the choice did not survive a reload'
    page.click('.nav .theme')
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == 'light'


@pytest.mark.parametrize('site', SITES)
def test_toggle_label_follows_theme(open_demo, site):
    page = open_demo(site, 1000, theme='light')
    label = "getComputedStyle(document.querySelector('.theme-label'), '::before').content"
    assert page.evaluate(label).strip('"') == 'light'
    page.click('.nav .theme')
    assert page.evaluate(label).strip('"') == 'dark'


def test_theme_is_set_before_first_paint(browser):
    """theme.js must set data-theme while the document is still loading, so a dark visitor never sees light."""
    ctx = browser.new_context(color_scheme='light')
    page = ctx.new_page()
    page.add_init_script('''
      localStorage.setItem('theme', 'dark');
      window.__first = null;
      new MutationObserver(() => {
        if (window.__first === null) window.__first = [document.documentElement.getAttribute('data-theme'), document.readyState];
      }).observe(document, { attributes: true, subtree: true, attributeFilter: ['data-theme'] });
    ''')
    page.goto(DEMO + '?site=studio')
    first = page.evaluate('window.__first')
    assert first == ['dark', 'loading'], f'first theme set was {first}'
    ctx.close()


@pytest.mark.parametrize('site', SITES)
def test_system_dark_is_the_default(open_demo, site):
    page = open_demo(site, 1000, theme='dark')
    assert page.evaluate("document.documentElement.getAttribute('data-theme')") == 'dark'


@pytest.mark.parametrize('width', WIDTHS)
def test_header_is_identical_across_sites(open_demo, width):
    """The brand and the toggle sit in the same place, and the bar is the same height, on every site."""
    got = {}
    for site in SITES:
        page = open_demo(site, width)
        b, t, n = box(page, '.nav .brand'), box(page, '.nav .theme'), box(page, '.nav')
        got[site] = (round(b['x']), round(width - (t['x'] + t['width'])), round(n['height']),
                     round(b['y'] + b['height'] / 2), round(t['y'] + t['height'] / 2))
    assert len(set(got.values())) == 1, f'brand x, toggle inset, bar height, brand y, toggle y differ: {got}'


@pytest.mark.parametrize('width', WIDTHS)
def test_bookshelf_search_visible(open_demo, width):
    page = open_demo('bookshelf', width)
    inp = page.locator('#bs-search input')
    assert inp.is_visible(), f'search is hidden at {width}px'
    b = inp.bounding_box()
    assert b['width'] >= 80, f'search is squeezed to {b["width"]:.0f}px at {width}px'
    nav = box(page, '.nav')
    assert b['x'] >= 0 and b['x'] + b['width'] <= nav['width'] + 0.5, 'search sticks out of the bar'
    brand, theme = box(page, '.nav .brand'), box(page, '.nav .theme')
    assert b['x'] >= brand['x'] + brand['width'] - 0.5 and b['x'] + b['width'] <= theme['x'] + 0.5, 'search overlaps the brand or the toggle'


def test_bookshelf_search_centred_on_desktop(open_demo):
    page = open_demo('bookshelf', 1000)
    b = box(page, '#bs-search')
    assert abs((b['x'] + b['width'] / 2) - 500) <= 2, f'search centre is {b["x"] + b["width"] / 2:.0f}px, not 500px'


@pytest.mark.parametrize('width', [700, 390, 320])
def test_garden_drawer(open_demo, width):
    page = open_demo('garden', width)
    menu, drawer = page.locator('#gd-menu'), page.locator('#gd-drawer')
    assert menu.is_visible(), f'menu button is hidden at {width}px'
    assert menu.get_attribute('aria-expanded') == 'false'
    menu.click()
    assert menu.get_attribute('aria-expanded') == 'true'
    assert 'is-open' in drawer.get_attribute('class')
    page.keyboard.press('Escape')
    assert menu.get_attribute('aria-expanded') == 'false'
    assert 'is-open' not in drawer.get_attribute('class')
    menu.click()
    menu.click()
    assert 'is-open' not in drawer.get_attribute('class'), 'a second click did not close the drawer'


def test_garden_menu_hidden_on_desktop(open_demo):
    assert not open_demo('garden', 1000).locator('#gd-menu').is_visible()


def test_studio_slot_is_empty(open_demo):
    page = open_demo('studio', 1000)
    assert not page.locator('#gd-menu').is_visible()
    assert not page.locator('#bs-search').is_visible()


def _toggle_colors(page):
    return page.evaluate('''() => { const c = getComputedStyle(document.querySelector('.nav .theme')); return [c.color, c.borderTopColor] }''')


def _neutral_colors(page):
    """The colours --mist and --line resolve to in the current theme."""
    return page.evaluate('''() => {
      const p = document.createElement('span');
      p.style.cssText = 'color: var(--mist); border: 1px solid var(--line); transition: none';
      document.body.appendChild(p);
      const c = getComputedStyle(p), r = [c.color, c.borderTopColor];
      p.remove();
      return r;
    }''')


@pytest.mark.parametrize('site', SITES)
def test_toggle_does_not_keep_the_accent_after_a_tap(browser, site):
    """On touch, :hover sticks after a tap. The toggle must go back to its neutral colours."""
    ctx = browser.new_context(viewport={'width': 390, 'height': 800}, has_touch=True, is_mobile=True)
    page = ctx.new_page()
    page.goto(f'{DEMO}?site={site}')
    assert _toggle_colors(page) == _neutral_colors(page)
    page.tap('.nav .theme')
    page.wait_for_timeout(400)  # the colour transition
    assert _toggle_colors(page) == _neutral_colors(page), 'the toggle kept the accent colour after a tap'
    ctx.close()


@pytest.mark.parametrize('site', SITES)
def test_toggle_takes_the_accent_on_hover(open_demo, site):
    page = open_demo(site, 1000)
    assert _toggle_colors(page) == _neutral_colors(page)
    page.hover('.nav .theme')
    page.wait_for_timeout(400)
    assert _toggle_colors(page) != _neutral_colors(page), 'no hover colour on a device that can hover'
