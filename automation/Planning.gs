/**
 * CustoVox - editorial planning: a few Google Calendar events, emails for everything else,
 * and the daily blog publication.
 *
 * Google Calendar only keeps (every day at 7:00 Paris, `syncCalendar`):
 *  - the "📦 Publier ... sur PyPI" tasks of automation/planning.json (ids "pypi-...");
 *  - a "⚠️ Attention : prévoir ..." alert when nothing is planned after a date
 *    (blog articles, MCP on PyPI).
 *
 * Everything else is an email to NOTIFY_EMAIL, when it happens (`notifyPlanned`, every 15 min):
 *  - "📰 Article en ligne" once the planned blog article answers on custovox.ai
 *    (or a warning if it is still missing 3 hours after its time);
 *  - "✍️ Post LinkedIn FR à publier" for the posts that are not in Buffer;
 *  - "⚠️ Plus de post LinkedIn planifié" when nothing is planned on LinkedIn anymore.
 * The "✅ Post LinkedIn publié" email (with the first comment to add) is sent by
 * checkBufferPosts in BufferNotify.gs.
 *
 * Needs BufferNotify.gs in the same project (NOTIFY_EMAIL, BUFFER_* ids).
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

// The list of items lives in automation/planning.json on GitHub, so it can be
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
  linkedin: { label: 'LinkedIn', calendar: false, todo: 'Préparez de nouveaux posts et programmez-les dans Buffer.\n' +
    'Dans Claude Code : « prépare les posts LinkedIn des prochaines semaines et programme-les dans Buffer ».' },
  mcp: { label: 'MCP', calendar: true, todo: 'Choisissez le prochain serveur MCP à publier sur PyPI et ajoutez son rappel.\n' +
    'Dans Claude Code : « planifie les prochains MCP à publier ».' },
  blog: { label: 'article de blog', calendar: true, todo: 'Préparez les prochains articles de blog.\n' +
    'Dans Claude Code : « prépare les prochains articles de blog ».' }
};

function setupPlanning() {
  const handlers = ['dailyBlogBuild', 'syncCalendar', 'notifyPlanned', 'checkBufferPosts'];
  ScriptApp.getProjectTriggers()
    .filter(t => handlers.indexOf(t.getHandlerFunction()) !== -1)
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('dailyBlogBuild').timeBased().everyDays(1).atHour(6).inTimezone(TZ).create();
  ScriptApp.newTrigger('syncCalendar').timeBased().everyDays(1).atHour(7).inTimezone(TZ).create();
  ScriptApp.newTrigger('notifyPlanned').timeBased().everyMinutes(15).create();
  ScriptApp.newTrigger('checkBufferPosts').timeBased().everyMinutes(15).create();
  removeReminders_();
  syncCalendar();
}

// Titles of the reminders an earlier version of this script put in the calendar (now emails).
const OLD_REMINDERS = ['📣 LinkedIn publié', '✍️ Post LinkedIn FR à publier', '📰 Article de blog en ligne',
  '⚠️ Attention : prévoir LinkedIn'];

/** Deletes the future LinkedIn / blog reminders from the calendar. Safe to run again. */
function removeReminders_() {
  const now = new Date();
  const events = CalendarApp.getDefaultCalendar().getEvents(now, new Date(now.getTime() + 400 * 864e5));
  let removed = 0;
  events.filter(e => OLD_REMINDERS.some(t => e.getTitle().indexOf(t) === 0)).forEach(e => {
    e.deleteEvent();
    removed++;
  });
  console.log(removed + ' reminder(s) removed from the calendar');
}

/** Creates the PyPI events and the "prévoir" alerts. Safe to run again. */
function syncCalendar() {
  const cal = CalendarApp.getDefaultCalendar();
  const props = PropertiesService.getScriptProperties();
  const created = JSON.parse(props.getProperty('CALENDAR_EVENTS') || '{}');
  const data = loadPlanning_();
  const PLANNING = data.planning || [];
  const TASKS = data.tasks || [];

  TASKS.filter(t => t.id.indexOf('pypi-') === 0).forEach(task => {
    if (created[task.id]) return;
    created[task.id] = createEvent_(cal, task.title, parse_(task.date), task.minutes, task.description).getId();
  });
  props.setProperty('CALENDAR_EVENTS', JSON.stringify(created));

  let bufferDates = [], bufferError = null;
  try {
    bufferDates = scheduledBufferDates_();
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

/** Dates of the LinkedIn posts scheduled in Buffer. */
function scheduledBufferDates_() {
  const token = PropertiesService.getScriptProperties().getProperty('BUFFER_TOKEN');
  if (!token) return [];
  const query = '{ posts(input:{organizationId:"' + BUFFER_ORG_ID + '", filter:{channelIds:["' +
    BUFFER_CHANNEL_ID + '"], status:[scheduled]}}){ edges{ node{ id dueAt } } } }';
  const res = UrlFetchApp.fetch('https://api.buffer.com', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + token }, payload: JSON.stringify({ query: query })
  });
  const data = JSON.parse(res.getContentText());
  if (data.errors) throw new Error(JSON.stringify(data.errors));
  return data.data.posts.edges.map(e => new Date(e.node.dueAt));
}

/** Emails for the planned blog articles and manual LinkedIn posts, when their time comes. */
function notifyPlanned() {
  const props = PropertiesService.getScriptProperties();
  const done = JSON.parse(props.getProperty('PLANNING_NOTIFIED') || '{}');
  const now = Date.now();
  const fmt = d => Utilities.formatDate(d, TZ, "dd/MM/yyyy 'à' HH'h'mm");

  (loadPlanning_().planning || []).forEach(item => {
    if (done[item.id] || (item.type !== 'blog' && item.type !== 'linkedin-fr')) return;
    const due = parse_(item.date);
    const late = now - due.getTime();
    if (late < 0 || late > 24 * 3600e3) return;   // not yet, or too old (first run)

    if (item.type === 'linkedin-fr') {
      MailApp.sendEmail(NOTIFY_EMAIL, '✍️ Post LinkedIn FR à publier : ' + item.title, [
        'Ce post était prévu le ' + fmt(due) + '. Il n\'est PAS programmé dans Buffer : publiez-le vous-même.',
        '',
        'Puis ajoutez ce premier commentaire sous le post :',
        item.link
      ].join('\n'));
    } else {
      const code = UrlFetchApp.fetch(item.link, { muteHttpExceptions: true, followRedirects: true }).getResponseCode();
      if (code !== 200 && late < 3 * 3600e3) return;   // the morning build may still be running: retry later
      MailApp.sendEmail(NOTIFY_EMAIL, (code === 200 ? '📰 Article en ligne : ' : '⚠️ Article introuvable : ') + item.title,
        code === 200
          ? 'L\'article prévu le ' + fmt(due) + ' est en ligne :\n' + item.link
          : 'L\'article prévu le ' + fmt(due) + ' ne s\'affiche pas (HTTP ' + code + ') :\n' + item.link +
            '\n\nVérifiez le déploiement Netlify ou relancez dailyBlogBuild dans Apps Script.');
    }
    done[item.id] = new Date().toISOString();
  });
  props.setProperty('PLANNING_NOTIFIED', JSON.stringify(done));
}

/** First comment of a Buffer post: the link of the planning.json LinkedIn item at the same minute. */
function plannedComment_(dueAt) {
  const minute = Math.round(new Date(dueAt).getTime() / 60000);
  const item = (loadPlanning_().planning || []).find(i =>
    i.type === 'linkedin' && Math.round(parse_(i.date).getTime() / 60000) === minute);
  return item && item.link;
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

    if (alerts[kind] && alerts[kind].eventId) {
      try {
        const old = cal.getEventById(alerts[kind].eventId);
        if (old) old.deleteEvent();
      } catch (e) {
        // already deleted by hand
      }
    }
    const k = GAP_KINDS[kind];
    const description = (last
      ? 'Dernier ' + k.label + ' planifié le ' + Utilities.formatDate(last, TZ, 'dd/MM/yyyy') + '. Rien n\'est prévu après.\n\n'
      : 'Aucun ' + k.label + ' n\'est planifié.\n\n') + k.todo;

    if (!k.calendar) {
      // Email only when the planning is about to run out (or already has).
      if (last && last.getTime() - now.getTime() > ALERT_DAYS_BEFORE * 864e5) return;
      MailApp.sendEmail(NOTIFY_EMAIL, '⚠️ Attention : prévoir ' + k.label, description);
      alerts[kind] = { last: lastKey };
      return;
    }
    let when = tomorrow9;
    if (last) {
      const before = parse_(Utilities.formatDate(new Date(last.getTime() - ALERT_DAYS_BEFORE * 864e5), TZ, 'yyyy-MM-dd') + ' 09:00');
      if (before > when) when = before;
    }
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
