/**
 * CustoVox - editorial planning in Google Calendar + daily blog publication.
 *
 * Every day at 7:00 (Paris) `syncCalendar`:
 *  - adds a reminder at publication time for EVERY LinkedIn post scheduled in Buffer
 *    ("add the link as first comment"), and moves it if the post is rescheduled;
 *  - adds the reminders listed in PLANNING and TASKS below;
 *  - adds a "⚠️ Attention : prévoir ..." alert when nothing is planned after a date
 *    (LinkedIn, MCP on PyPI, blog articles).
 *
 * Needs BufferNotify.gs in the same project (BUFFER_* ids, COMMENTS, DEFAULT_COMMENT).
 *
 * Setup (once):
 * 1. Project Settings > Script Properties: NETLIFY_BUILD_HOOK and BUFFER_TOKEN.
 * 2. Run `setupPlanning` and accept the permissions.
 * To add an item later: add a line to PLANNING or TASKS, then run `syncCalendar`.
 */

const BLOG = 'https://custovox.ai/blog/';
const ALERT_DAYS_BEFORE = 7;   // "prévoir" alert this many days before the last planned item
const TZ = 'Europe/Paris';

// type: linkedin = scheduled in Buffer (comment to add) | linkedin-fr = not scheduled, to post by hand
//       blog = goes live automatically that morning (just check it)
const PLANNING = [
  { id: 'li-2026-10-12', date: '2026-10-12 18:00', type: 'linkedin', title: 'G2 reviews (EN)', link: BLOG + 'g2-reviews-nlp-analysis' },
  { id: 'li-2026-10-21', date: '2026-10-21 18:00', type: 'linkedin', title: 'Churn — 3 conversations (EN)', link: BLOG + 'how-nlp-reduces-customer-churn' },
  { id: 'li-2026-10-25', date: '2026-10-25 18:00', type: 'linkedin-fr', title: 'Churn — 3 conversations (FR)', link: BLOG + 'how-nlp-reduces-customer-churn' },
  { id: 'li-2026-10-28', date: '2026-10-28 18:00', type: 'linkedin', title: 'Ratings hide (EN)', link: BLOG + 'g2-reviews-nlp-analysis' },
  { id: 'li-2026-11-01', date: '2026-11-01 18:00', type: 'linkedin-fr', title: 'Les notes cachent (FR)', link: BLOG + 'g2-reviews-nlp-analysis' },
  { id: 'li-2026-11-04', date: '2026-11-04 18:00', type: 'linkedin', title: 'TripAdvisor hotels (EN)', link: BLOG + 'g2-reviews-nlp-analysis' },
  { id: 'li-2026-11-08', date: '2026-11-08 18:00', type: 'linkedin-fr', title: 'Avis hôteliers (FR)', link: BLOG + 'g2-reviews-nlp-analysis' },
  { id: 'li-2026-11-11', date: '2026-11-11 18:00', type: 'linkedin', title: '5 churn signals (EN)', link: BLOG + 'how-nlp-reduces-customer-churn' },
  { id: 'li-2026-11-15', date: '2026-11-15 18:00', type: 'linkedin-fr', title: '5 signaux de churn (FR)', link: BLOG + 'how-nlp-reduces-customer-churn' },
  { id: 'li-2026-11-18', date: '2026-11-18 18:00', type: 'linkedin', title: '5 languages (EN)', link: BLOG + 'top-5-sentiment-analysis-tools' },
  { id: 'li-2026-11-22', date: '2026-11-22 18:00', type: 'linkedin-fr', title: '5 langues (FR)', link: BLOG + 'top-5-sentiment-analysis-tools' },
  { id: 'blog-2026-10-21', date: '2026-10-21 09:00', type: 'blog', title: 'How NLP Reduces Customer Churn', link: BLOG + 'how-nlp-reduces-customer-churn' },
  { id: 'blog-2026-11-11', date: '2026-11-11 09:00', type: 'blog', title: 'Top 5 Sentiment Analysis Tools', link: BLOG + 'top-5-sentiment-analysis-tools' },
  { id: 'blog-2026-12-09', date: '2026-12-09 09:00', type: 'blog', title: 'What Is an MCP Server', link: BLOG + 'what-is-mcp-server-cx-teams' },
  { id: 'blog-2026-12-23', date: '2026-12-23 09:00', type: 'blog', title: '2026 CX Year in Review', link: BLOG + '2026-cx-nlp-year-in-review' }
];

const PYPI_STEPS = 'Dans Claude Code, dites : « publie {mcp} sur PyPI ».\n' +
  'Claude prépare le paquet, vous l\'envoyez avec twine (jeton PyPI), puis Claude le publie dans le registre MCP.';

// One-off reminders. Ids starting with "pypi-" count as planned MCP publications.
const TASKS = [
  { id: 'task-2026-10-12-prospects', date: '2026-10-12 09:30', minutes: 30,
    title: '📧 Envoyer des mails à 10 nouveaux prospects',
    description: 'Objectif : 10 nouveaux prospects contactés aujourd\'hui.' },
  { id: 'pypi-2026-10-16', date: '2026-10-16 10:00', minutes: 15,
    title: '📦 Publier custovox-emotion sur PyPI', description: PYPI_STEPS.replace('{mcp}', 'custovox-emotion') },
  { id: 'pypi-2026-10-23', date: '2026-10-23 10:00', minutes: 15,
    title: '📦 Publier custovox-ticket-scorer sur PyPI', description: PYPI_STEPS.replace('{mcp}', 'custovox-ticket-scorer') },
  { id: 'pypi-2026-10-30', date: '2026-10-30 10:00', minutes: 15,
    title: '📦 Publier custovox-review-analyzer sur PyPI', description: PYPI_STEPS.replace('{mcp}', 'custovox-review-analyzer') },
  { id: 'pypi-2026-11-06', date: '2026-11-06 10:00', minutes: 15,
    title: '📦 Publier custovox-churn-signal sur PyPI', description: PYPI_STEPS.replace('{mcp}', 'custovox-churn-signal') },
  { id: 'pypi-2026-11-13', date: '2026-11-13 10:00', minutes: 15,
    title: '📦 Publier custovox-visual sur PyPI', description: PYPI_STEPS.replace('{mcp}', 'custovox-visual') }
];

const GAP_KINDS = {
  linkedin: { label: 'LinkedIn', todo: 'Préparez de nouveaux posts et programmez-les dans Buffer.\n' +
    'Dans Claude Code : « prépare les posts LinkedIn des prochaines semaines et programme-les dans Buffer ».' },
  mcp: { label: 'MCP', todo: 'Choisissez le prochain serveur MCP à publier sur PyPI et ajoutez son rappel.\n' +
    'Dans Claude Code : « planifie les prochains MCP à publier ».' },
  blog: { label: 'article de blog', todo: 'Préparez les prochains articles de blog.\n' +
    'Dans Claude Code : « prépare les prochains articles de blog ».' }
};

function setupPlanning() {
  ScriptApp.getProjectTriggers()
    .filter(t => ['dailyBlogBuild', 'syncCalendar'].indexOf(t.getHandlerFunction()) !== -1)
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('dailyBlogBuild').timeBased().everyDays(1).atHour(6).inTimezone(TZ).create();
  ScriptApp.newTrigger('syncCalendar').timeBased().everyDays(1).atHour(7).inTimezone(TZ).create();
  syncCalendar();
}

/** Creates or updates the calendar events. Safe to run again. */
function syncCalendar() {
  const cal = CalendarApp.getDefaultCalendar();
  const props = PropertiesService.getScriptProperties();
  const created = JSON.parse(props.getProperty('CALENDAR_EVENTS') || '{}');

  // Old weekly series from a previous version of this script.
  Object.keys(created).filter(id => id.indexOf('weekly-') === 0).forEach(id => {
    const series = cal.getEventSeriesById(created[id]);
    if (series) series.deleteEventSeries();
    delete created[id];
  });

  PLANNING.forEach(item => {
    if (created[item.id]) return;
    let title, description;
    if (item.type === 'linkedin') {
      title = '📣 LinkedIn publié : ajouter le lien en commentaire — ' + item.title;
      description = 'Le post est publié automatiquement par Buffer à 18h.\n\n' +
        'Ajoutez ce premier commentaire sous le post :\n' + item.link;
    } else if (item.type === 'linkedin-fr') {
      title = '✍️ Post LinkedIn FR à publier + lien en commentaire — ' + item.title;
      description = 'Ce post n\'est PAS programmé dans Buffer : publiez-le vous-même ou programmez-le.\n\n' +
        'Puis ajoutez ce premier commentaire sous le post :\n' + item.link;
    } else {
      title = '📰 Article de blog en ligne — ' + item.title;
      description = 'L\'article est publié automatiquement ce matin. Vérifiez qu\'il s\'affiche bien :\n' + item.link;
    }
    const event = createEvent_(cal, title, parse_(item.date), 15, description);
    if (item.type !== 'linkedin') event.addPopupReminder(60 * 24); // the day before
    created[item.id] = event.getId();
  });

  TASKS.forEach(task => {
    if (created[task.id]) return;
    created[task.id] = createEvent_(cal, task.title, parse_(task.date), task.minutes, task.description).getId();
  });

  const bufferDates = syncBufferPosts_(cal, created);
  props.setProperty('CALENDAR_EVENTS', JSON.stringify(created));

  const dates = item => parse_(item.date);
  gapAlerts_(cal, {
    linkedin: bufferDates.concat(PLANNING.filter(p => p.type.indexOf('linkedin') === 0).map(dates)),
    mcp: TASKS.filter(t => t.id.indexOf('pypi-') === 0).map(dates),
    blog: PLANNING.filter(p => p.type === 'blog').map(dates)
  });
}

/** One reminder per LinkedIn post scheduled in Buffer. Returns the scheduled dates. */
function syncBufferPosts_(cal, created) {
  const token = PropertiesService.getScriptProperties().getProperty('BUFFER_TOKEN');
  if (!token) return [];
  const query = '{ posts(input:{organizationId:"' + BUFFER_ORG_ID + '", filter:{channelIds:["' +
    BUFFER_CHANNEL_ID + '"], status:[scheduled]}}){ edges{ node{ id text dueAt } } } }';
  const res = UrlFetchApp.fetch('https://api.buffer.com', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + token }, payload: JSON.stringify({ query: query })
  });
  const data = JSON.parse(res.getContentText());
  if (data.errors) throw new Error(JSON.stringify(data.errors));

  const posts = data.data.posts.edges.map(e => e.node);
  posts.forEach(p => {
    const key = 'buffer-' + p.id;
    const due = new Date(p.dueAt);
    // Posts already covered by a PLANNING line at the same time.
    const same = PLANNING.find(i => i.type === 'linkedin' && parse_(i.date).getTime() === due.getTime());
    if (same && created[same.id]) { created[key] = created[same.id]; return; }

    const existing = created[key] && cal.getEventById(created[key]);
    if (existing) {
      if (existing.getStartTime().getTime() !== due.getTime()) existing.setTime(due, new Date(due.getTime() + 15 * 60000));
      return;
    }
    const firstLine = plain_((p.text || '').split('\n')[0]).slice(0, 60);
    const comment = (typeof COMMENTS !== 'undefined' && COMMENTS[p.id]) || DEFAULT_COMMENT;
    created[key] = createEvent_(cal, '📣 LinkedIn publié : ajouter le lien en commentaire — ' + firstLine, due, 15,
      'Le post est publié automatiquement par Buffer.\n\nAjoutez ce premier commentaire sous le post :\n' + comment).getId();
  });
  return posts.map(p => new Date(p.dueAt));
}

/** "⚠️ Attention : prévoir ..." when nothing is planned after the last date of a kind. */
function gapAlerts_(cal, datesByKind) {
  const props = PropertiesService.getScriptProperties();
  const alerts = JSON.parse(props.getProperty('GAP_ALERTS') || '{}');
  const now = new Date();
  const tomorrow9 = parse_(Utilities.formatDate(new Date(now.getTime() + 864e5), TZ, 'yyyy-MM-dd') + ' 09:00');

  Object.keys(GAP_KINDS).forEach(kind => {
    const future = datesByKind[kind].filter(d => d > now);
    const last = future.length ? new Date(Math.max.apply(null, future)) : null;
    const lastKey = last ? Utilities.formatDate(last, TZ, 'yyyy-MM-dd') : 'none';
    if (alerts[kind] && alerts[kind].last === lastKey) return;   // already alerted for this date

    if (alerts[kind]) {
      const old = cal.getEventById(alerts[kind].eventId);
      if (old) old.deleteEvent();
    }
    let when = tomorrow9;
    if (last) {
      const before = parse_(Utilities.formatDate(new Date(last.getTime() - ALERT_DAYS_BEFORE * 864e5), TZ, 'yyyy-MM-dd') + ' 09:00');
      if (before > when) when = before;
    }
    const k = GAP_KINDS[kind];
    const description = (last
      ? 'Dernier ' + k.label + ' planifié le ' + Utilities.formatDate(last, TZ, 'dd/MM/yyyy') + '. Rien n\'est prévu après.\n\n'
      : 'Aucun ' + k.label + ' n\'est planifié.\n\n') + k.todo;
    const event = createEvent_(cal, '⚠️ Attention : prévoir ' + k.label, when, 30, description);
    event.addPopupReminder(60 * 24);
    alerts[kind] = { last: lastKey, eventId: event.getId() };
  });
  props.setProperty('GAP_ALERTS', JSON.stringify(alerts));
}

/** Rebuilds the site every morning so scheduled articles go live on their date. */
function dailyBlogBuild() {
  const hook = PropertiesService.getScriptProperties().getProperty('NETLIFY_BUILD_HOOK');
  if (!hook) throw new Error('NETLIFY_BUILD_HOOK is missing in Script Properties');
  UrlFetchApp.fetch(hook, { method: 'post', payload: '{}', contentType: 'application/json' });
}

function createEvent_(cal, title, start, minutes, description) {
  const event = cal.createEvent(title, start, new Date(start.getTime() + minutes * 60000), { description: description });
  event.removeAllReminders();
  event.addPopupReminder(0);
  return event;
}

function parse_(text) {
  return Utilities.parseDate(text, TZ, 'yyyy-MM-dd HH:mm');
}

/** Turns the Unicode bold letters used on LinkedIn back into plain text. */
function plain_(text) {
  return Array.from(text).map(ch => {
    const c = ch.codePointAt(0);
    if (c >= 0x1D5D4 && c <= 0x1D5ED) return String.fromCharCode(65 + c - 0x1D5D4);
    if (c >= 0x1D5EE && c <= 0x1D607) return String.fromCharCode(97 + c - 0x1D5EE);
    if (c >= 0x1D7EC && c <= 0x1D7F5) return String.fromCharCode(48 + c - 0x1D7EC);
    return ch;
  }).join('');
}
