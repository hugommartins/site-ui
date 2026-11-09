(function () {
  var KEY = 'theme';   // use the key studio uses today (check Base.astro)
  var root = document.documentElement, saved;
  try { saved = localStorage.getItem(KEY); } catch (e) {}
  var dark = saved ? saved === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  root.setAttribute('data-theme', dark ? 'dark' : 'light');
  document.addEventListener('click', function (e) {
    if (!(e.target.closest && e.target.closest('.theme'))) return;
    var next = root.getAttribute('data-theme') === 'dark' ? 'light' : 'dark';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem(KEY, next); } catch (err) {}
  });
})();