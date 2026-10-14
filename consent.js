/* custovox.ai — cookie consent + Google Analytics 4 (CNIL / GDPR compliant).
 *
 * - Nothing is loaded and no cookie is set before the visitor chooses.
 * - "Refuse" is as visible and easy as "Accept"; the choice is kept 6 months.
 * - Global Privacy Control (GPC) is treated as a refusal.
 * - Adds "Privacy policy" and "Cookie settings" links to the page footer.
 * Audience measurement goes through Google Tag Manager (GTM_ID): the GA4 tag is configured
 * inside the GTM container. GTM is loaded only after consent; empty IDs = no banner.
 */
(function () {
  var GTM_ID = 'GTM-NWDPP27H';              // Google Tag Manager container (contains the GA4 tag)
  var GA_ID = '';                            // optional direct GA4 ID, only if GTM is not used
  var KEY = 'cvx-consent';
  var MAX_AGE = 182 * 24 * 3600 * 1000;      // 6 months

  var fr = (document.documentElement.lang || '').toLowerCase().indexOf('fr') === 0;
  var T = fr ? {
    text: 'Nous utilisons Google Analytics pour mesurer l\'audience du site, uniquement si vous l\'acceptez. Aucun cookie n\'est déposé si vous refusez.',
    accept: 'Accepter', refuse: 'Refuser', more: 'En savoir plus',
    privacy: 'Politique de confidentialité', settings: 'Gérer les cookies',
    policy: '/fr/confidentialite.html'
  } : {
    text: 'We use Google Analytics to measure audience on this site, only if you accept. No cookie is set if you refuse.',
    accept: 'Accept', refuse: 'Refuse', more: 'Learn more',
    privacy: 'Privacy policy', settings: 'Cookie settings',
    policy: '/privacy.html'
  };

  function read() {
    try {
      var v = JSON.parse(localStorage.getItem(KEY) || 'null');
      return v && Date.now() - v.t < MAX_AGE ? v.choice : null;
    } catch (e) { return null; }
  }
  function save(choice) {
    try { localStorage.setItem(KEY, JSON.stringify({ choice: choice, t: Date.now() })); } catch (e) {}
  }

  function loadAnalytics() {
    if (window.__cvxGa || (!GTM_ID && !GA_ID)) return;
    window.__cvxGa = true;
    window.dataLayer = window.dataLayer || [];
    if (GTM_ID) {
      window.dataLayer.push({ 'gtm.start': new Date().getTime(), event: 'gtm.js', analytics_consent: 'granted' });
      var g = document.createElement('script');
      g.async = true;
      g.src = 'https://www.googletagmanager.com/gtm.js?id=' + GTM_ID;
      document.head.appendChild(g);
      return;
    }
    window.gtag = function () { window.dataLayer.push(arguments); };
    window.gtag('js', new Date());
    window.gtag('config', GA_ID, {
      cookie_expires: 13 * 30 * 24 * 3600,   // 13 months (CNIL)
      allow_google_signals: false,
      allow_ad_personalization_signals: false
    });
    var s = document.createElement('script');
    s.async = true;
    s.src = 'https://www.googletagmanager.com/gtag/js?id=' + GA_ID;
    document.head.appendChild(s);
  }

  function deleteAnalyticsCookies() {
    var host = location.hostname;
    var domains = ['', host, '.' + host, '.' + host.split('.').slice(-2).join('.')];
    document.cookie.split(';').forEach(function (c) {
      var name = c.split('=')[0].trim();
      if (name.indexOf('_ga') !== 0) return;
      domains.forEach(function (d) {
        document.cookie = name + '=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/' + (d ? '; domain=' + d : '');
      });
    });
  }

  function addStyles() {
    var css = '.cvx-banner{position:fixed;left:16px;right:16px;bottom:16px;z-index:9999;max-width:760px;margin:0 auto;' +
      'background:#0D2B6B;color:#fff;border-radius:12px;padding:16px 18px;box-shadow:0 10px 40px rgba(13,43,107,.35);' +
      'display:flex;gap:14px;align-items:center;flex-wrap:wrap;font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}' +
      '.cvx-banner p{flex:1 1 320px;margin:0;color:rgba(255,255,255,.9)}' +
      '.cvx-banner a{color:#00C48C}' +
      '.cvx-banner .cvx-btns{display:flex;gap:10px}' +
      '.cvx-banner button{font:inherit;font-weight:700;border-radius:8px;padding:10px 20px;cursor:pointer;border:1.5px solid #00C48C}' +
      '.cvx-banner .cvx-refuse{background:transparent;color:#fff}' +
      '.cvx-banner .cvx-accept{background:#00C48C;color:#0D2B6B}' +
      '.cvx-banner button:focus-visible{outline:2px solid #fff;outline-offset:2px}' +
      '.cvx-legal{display:block;margin-top:6px}' +
      '.cvx-legal a,.cvx-legal button{color:inherit;font:inherit;background:none;border:0;padding:0;cursor:pointer;text-decoration:underline}';
    var st = document.createElement('style');
    st.textContent = css;
    document.head.appendChild(st);
  }

  var banner = null;
  function showBanner() {
    if (banner) return;
    banner = document.createElement('div');
    banner.className = 'cvx-banner';
    banner.setAttribute('role', 'dialog');
    banner.setAttribute('aria-live', 'polite');
    banner.setAttribute('aria-label', T.settings);
    banner.innerHTML = '<p>' + T.text + ' <a href="' + T.policy + '#cookies">' + T.more + '</a></p>' +
      '<div class="cvx-btns"><button type="button" class="cvx-refuse">' + T.refuse + '</button>' +
      '<button type="button" class="cvx-accept">' + T.accept + '</button></div>';
    document.body.appendChild(banner);
    banner.querySelector('.cvx-accept').addEventListener('click', function () { choose('granted'); });
    banner.querySelector('.cvx-refuse').addEventListener('click', function () { choose('denied'); });
  }
  function hideBanner() { if (banner) { banner.remove(); banner = null; } }

  function choose(choice) {
    var before = read();
    save(choice);
    hideBanner();
    if (choice === 'granted') loadAnalytics();
    else {
      deleteAnalyticsCookies();
      if (before === 'granted') location.reload();   // stop Analytics already running on this page
    }
  }

  function addFooterLinks() {
    var footer = document.querySelector('footer');
    if (!footer) return;
    var span = document.createElement('span');
    span.className = 'cvx-legal';
    span.innerHTML = '<a href="' + T.policy + '">' + T.privacy + '</a>' +
      (GTM_ID || GA_ID ? ' · <button type="button" class="cvx-settings">' + T.settings + '</button>' : '');
    footer.appendChild(span);
    var b = span.querySelector('.cvx-settings');
    if (b) b.addEventListener('click', showBanner);
  }

  function init() {
    addStyles();
    addFooterLinks();
    if (!GTM_ID && !GA_ID) return;
    var gpc = navigator.globalPrivacyControl === true;
    var choice = read();
    if (gpc && choice !== 'granted') return;   // GPC = refusal, no banner
    if (choice === 'granted') loadAnalytics();
    else if (choice === null) showBanner();
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
