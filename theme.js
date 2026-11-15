/* site-ui theme.js: inline in <head> before the stylesheets. One delegated handler for .theme; a site must not add another. */
(function () {
  var KEY = 'theme';
  var root = document.documentElement;
  var saved;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  var dark = saved === 'dark' || saved === 'light'
    ? saved === 'dark'
    : matchMedia('(prefers-color-scheme: dark)').matches;
  root.setAttribute('data-theme', dark ? 'dark' : 'light');

  document.addEventListener('click', function (e) {
    if (!(e.target.closest && e.target.closest('.theme'))) return;
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    /* the switch is instant: transitions are off while the new theme's styles are computed,
       then back on, so hover effects keep working */
    root.classList.add('theme-switching');
    root.setAttribute('data-theme', next);
    void root.offsetWidth; /* force the style recalculation while the class is on */
    root.classList.remove('theme-switching');
    try { localStorage.setItem(KEY, next); } catch (err) {}
  });
})();