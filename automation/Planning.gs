/**
 * CustoVox - editorial planning in Google Calendar + daily blog publication.
 *
 * Setup (once):
 * 1. Project Settings > Script Properties > add NETLIFY_BUILD_HOOK = the Netlify build hook URL.
 * 2. Run `setupPlanning` and accept the permissions.
 * To add an item later: add a line to PLANNING, then run `syncCalendar` again.
 */

const BLOG = 'https://custovox.ai/blog/';

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

// Weekly routines (event series). Removing a line here and running syncCalendar
// deletes that series from the calendar.
const RECURRING = [];
const RECURRING_UNTIL = '2026-12-31';

const PYPI_STEPS = 'Dans Claude Code, dites : « publie {mcp} sur PyPI ».\n' +
  'Claude prépare le paquet, vous l\'envoyez avec twine (jeton PyPI), puis Claude le publie dans le registre MCP.';

// One-off reminders.
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
    title: '📦 Publier custovox-visual sur PyPI', description: PYPI_STEPS.replace('{mcp}', 'custovox-visual') },
  { id: 'plan-2026-11-16', date: '2026-11-16 09:00', minutes: 30,
    title: '🗓️ Préparer les posts LinkedIn après le 18/11',
    description: 'Le dernier post programmé dans Buffer sort le 18/11.\n' +
      'Dans Claude Code, dites : « prépare les posts LinkedIn des prochaines semaines et programme-les dans Buffer ».' }
];

function setupPlanning() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'dailyBlogBuild')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('dailyBlogBuild').timeBased().everyDays(1).atHour(6).inTimezone('Europe/Paris').create();
  syncCalendar();
}

/** Creates the calendar events that don't exist yet. Safe to run again. */
function syncCalendar() {
  const cal = CalendarApp.getDefaultCalendar();
  const props = PropertiesService.getScriptProperties();
  const created = JSON.parse(props.getProperty('CALENDAR_EVENTS') || '{}');

  PLANNING.forEach(item => {
    if (created[item.id]) return;
    const start = Utilities.parseDate(item.date, 'Europe/Paris', 'yyyy-MM-dd HH:mm');
    const end = new Date(start.getTime() + 15 * 60 * 1000);
    let title, description;
    if (item.type === 'linkedin') {
      title = '📣 LinkedIn publié : ajouter le commentaire — ' + item.title;
      description = 'Le post est publié automatiquement par Buffer à 18h.\n\n' +
        'Ajoutez ce premier commentaire sous le post :\n' + item.link;
    } else if (item.type === 'linkedin-fr') {
      title = '✍️ Post LinkedIn FR à publier — ' + item.title;
      description = 'Ce post n\'est PAS programmé dans Buffer : publiez-le vous-même ou programmez-le.\n\n' +
        'Lien à mettre en commentaire :\n' + item.link;
    } else {
      title = '📰 Article de blog en ligne — ' + item.title;
      description = 'L\'article est publié automatiquement ce matin. Vérifiez qu\'il s\'affiche bien :\n' + item.link;
    }
    const event = cal.createEvent(title, start, end, { description: description });
    event.removeAllReminders();
    event.addPopupReminder(0);
    if (item.type !== 'linkedin') event.addPopupReminder(60 * 24); // the day before
    created[item.id] = event.getId();
  });

  TASKS.forEach(task => {
    if (created[task.id]) return;
    const start = Utilities.parseDate(task.date, 'Europe/Paris', 'yyyy-MM-dd HH:mm');
    const event = cal.createEvent(task.title, start, new Date(start.getTime() + task.minutes * 60000),
      { description: task.description });
    event.removeAllReminders();
    event.addPopupReminder(0);
    created[task.id] = event.getId();
  });

  // Delete series that were removed from RECURRING.
  Object.keys(created).filter(id => id.indexOf('weekly-') === 0 && !RECURRING.some(r => r.id === id))
    .forEach(id => {
      const series = cal.getEventSeriesById(created[id]);
      if (series) series.deleteEventSeries();
      delete created[id];
    });

  const until = Utilities.parseDate(RECURRING_UNTIL + ' 23:59', 'Europe/Paris', 'yyyy-MM-dd HH:mm');
  RECURRING.forEach(r => {
    if (created[r.id]) return;
    // First occurrence: the next matching weekday from today.
    const day = CalendarApp.Weekday[r.weekday];
    const start = Utilities.parseDate(
      Utilities.formatDate(new Date(), 'Europe/Paris', 'yyyy-MM-dd') + ' ' + r.time, 'Europe/Paris', 'yyyy-MM-dd HH:mm');
    const jsDay = ['SUNDAY', 'MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY'].indexOf(r.weekday);
    while (start.getDay() !== jsDay || start < new Date()) start.setDate(start.getDate() + 1);
    const recurrence = CalendarApp.newRecurrence().addWeeklyRule().onlyOnWeekday(day).until(until);
    const series = cal.createEventSeries(r.title, start, new Date(start.getTime() + r.minutes * 60000),
      recurrence, { description: r.description });
    series.removeAllReminders();
    series.addPopupReminder(0);
    created[r.id] = series.getId();
  });

  props.setProperty('CALENDAR_EVENTS', JSON.stringify(created));
}

/** Rebuilds the site every morning so scheduled articles go live on their date. */
function dailyBlogBuild() {
  const hook = PropertiesService.getScriptProperties().getProperty('NETLIFY_BUILD_HOOK');
  if (!hook) throw new Error('NETLIFY_BUILD_HOOK is missing in Script Properties');
  UrlFetchApp.fetch(hook, { method: 'post', payload: '{}', contentType: 'application/json' });
}
