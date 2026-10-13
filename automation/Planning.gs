/**
 * CustoVox - editorial planning in Google Calendar + daily blog publication.
 *
 * Every day at 7:00 (Paris) `syncCalendar`:
 *  - adds a reminder at publication time for EVERY LinkedIn post scheduled in Buffer
 *    ("add the link as first comment"), and moves it if the post is rescheduled;
 *  - adds the reminders listed in automation/planning.json (GitHub);
 *  - adds a "⚠️ Attention : prévoir ..." alert when nothing is planned after a date
 *    (LinkedIn, MCP on PyPI, blog articles).
 *
 * Needs BufferNotify.gs in the same project (BUFFER_* ids, COMMENTS, DEFAULT_COMMENT).
 *
 * Setup (once):
 * 1. Project Settings > Script Properties: NETLIFY_BUILD_HOOK and BUFFER_TOKEN.
 * 2. Run `setupPlanning` and accept the permissions.
 * To add an item later: edit automation/planning.json on GitHub (picked up the next morning,
 * or run `syncCalendar` to apply it now).
 */

const BLOG = 'https://custovox.ai/blog/';
const ALERT_DAYS_BEFORE = 7;   // "prévoir" alert this many days before the last planned item
const TZ = 'Europe/Paris';

// The list of reminders lives in automation/planning.json on GitHub, so it can be
// updated without pasting this script again:
//  planning: { id, date 'yyyy-MM-dd HH:mm', type linkedin | linkedin-fr | blog, title, link }
//  tasks:    { id, date, minutes, title, description }   (ids "pypi-..." = planned MCP publications)
const PLANNING_URL = 'https://raw.githubusercontent.com/jeremdecustovox/custovox-ai/main/automation/planning.json';

function loadPlanning_() {
  const res = UrlFetchApp.fetch(PLANNING_URL + '?t=' + Date.now(), { muteHttpExceptions: true });
  if (res.getResponseCode() !== 200) throw new Error('planning.json unreachable: HTTP ' + res.getResponseCode());
  return JSON.parse(res.getContentText());
}

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
  const data = loadPlanning_();
  const PLANNING = data.planning || [];
  const TASKS = data.tasks || [];

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
  props.setProperty('CALENDAR_EVENTS', JSON.stringify(created));

  let bufferDates = [], bufferError = null;
  try {
    bufferDates = syncBufferPosts_(cal, created, PLANNING);
    props.setProperty('CALENDAR_EVENTS', JSON.stringify(created));
  } catch (e) {
    bufferError = e;   // still create the "prévoir" alerts below
  }

  const dates = item => parse_(item.date);
  gapAlerts_(cal, {
    linkedin: bufferDates.concat(PLANNING.filter(p => p.type.indexOf('linkedin') === 0).map(dates)),
    mcp: TASKS.filter(t => t.id.indexOf('pypi-') === 0).map(dates),
    blog: PLANNING.filter(p => p.type === 'blog').map(dates)
  });
  if (bufferError) throw bufferError;
}

/** One reminder per LinkedIn post scheduled in Buffer. Returns the scheduled dates. */
function syncBufferPosts_(cal, created, PLANNING) {
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

/** Rebuilds the site only on mornings when a blog article is due (saves Netlify credits). */
function dailyBlogBuild() {
  const hook = PropertiesService.getScriptProperties().getProperty('NETLIFY_BUILD_HOOK');
  if (!hook) throw new Error('NETLIFY_BUILD_HOOK is missing in Script Properties');
  const today = Utilities.formatDate(new Date(), TZ, 'yyyy-MM-dd');
  const due = (loadPlanning_().planning || []).some(p => p.type === 'blog' && p.date.indexOf(today) === 0);
  if (!due) return;
  UrlFetchApp.fetch(hook, { method: 'post', payload: '{}', contentType: 'application/json' });
}

function createEvent_(cal, title, start, minutes, description) {
  const end = new Date(start.getTime() + minutes * 60000);
  // Reuse an identical event (e.g. created by an interrupted run) instead of duplicating it.
  const same = cal.getEvents(start, end).find(e => e.getTitle() === title && e.getStartTime().getTime() === start.getTime());
  if (same) return same;
  const event = cal.createEvent(title, start, end, { description: description });
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
