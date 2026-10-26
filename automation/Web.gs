/**
 * CustoVox - web app entry point of the Google Workspace spreadsheet "CustoVox Leads".
 *
 * Receives the custovox.ai forms (case-study requests -> "Leads", contact messages ->
 * "Contacts", see Leads.gs) and emails a weekly digest of new signups.
 *
 * Setup (once): run `setupWorkspace`, then Deploy > New deployment > Web app
 * (Execute as: Me, Who has access: Anyone) and give the web app URL to Claude.
 */

function doPost(e) {
  try {
    const p = JSON.parse(e.postData.contents);
    if (p.app === 'custovox-lead') return handleLead_(p);
    if (p.app === 'custovox-contact') return handleContact_(p);
    return ContentService.createTextOutput('ignored');
  } catch (err) {
    return ContentService.createTextOutput('error');
  }
}

/** Creates the sheets and the Monday 8:00 digest. Run once. */
function setupWorkspace() {
  setupLeads();
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'weeklyLeadsDigest')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('weeklyLeadsDigest').timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(8).inTimezone('Europe/Paris').create();
}

/** Weekly summary of new prospects and contact messages (test rows excluded). */
function weeklyLeadsDigest() {
  const since = new Date(Date.now() - 7 * 864e5);
  const isTest = email => String(email).indexOf('test+') === 0;
  const leads = leadsSheet_().getDataRange().getValues().slice(1)
    .filter(r => r[8] === 'new' && !isTest(r[1]));
  const weekLeads = leads.filter(r => r[0] >= since);
  const contacts = contactsSheet_().getDataRange().getValues().slice(1).filter(r => !isTest(r[2]));
  const weekContacts = contacts.filter(r => r[0] >= since);
  const toAnswer = contacts.filter(r => r[7] === 'to answer').length;

  const fmt = d => Utilities.formatDate(d, 'Europe/Paris', 'dd/MM/yyyy');
  let outreach;
  try {
    outreach = apolloOutreach_(weekLeads.length, leads.length);
  } catch (err) {
    outreach = ['Prospection Apollo : indisponible (' + err.message + ')'];
  }
  const body = [
    'Prospects et messages custovox.ai — semaine du ' + fmt(since) + ' au ' + fmt(new Date()),
    '',
  ].concat(outreach, [
    '',
    'Demandes d\'étude de cas : ' + weekLeads.length + ' cette semaine · ' + leads.length + ' au total',
    'Dont inscrits aux actualités : ' + weekLeads.filter(r => r[7] === 'yes').length + ' cette semaine',
  ], weekLeads.map(r => '  - ' + r[1] + ' · ' + r[2] + ' · ' + r[3] + ' · ' + r[4]), [
    '',
    'Messages de contact : ' + weekContacts.length + ' cette semaine · ' + toAnswer + ' encore marqués « to answer »',
  ], weekContacts.map(r => '  - ' + r[1] + ' (' + r[2] + ')' + (r[3] ? ' · ' + r[3] : '')), [
    '',
    'Base de données : ' + SpreadsheetApp.getActiveSpreadsheet().getUrl()
  ]).join('\n');
  MailApp.sendEmail(NOTIFY_LEADS_TO, 'custovox.ai : prospects de la semaine (' + fmt(new Date()) + ')', body);
}

/**
 * Apollo outreach: prospects contacted this week and since the start, with ratios.
 * Sums the stats of every Apollo sequence whose name starts with "CustoVox" (APOLLO_SEQUENCE_PREFIX).
 * "This week" = difference with the totals saved by the previous digest (script property
 * APOLLO_TOTALS). Needs the APOLLO_API_KEY script property (an Apollo master API key).
 */
const APOLLO_SEQUENCE_PREFIX = 'CustoVox';

function apolloOutreach_(weekLeads, totalLeads) {
  const props = PropertiesService.getScriptProperties();
  const key = props.getProperty('APOLLO_API_KEY');
  if (!key) return ['Prospection Apollo : ajoutez la propriété APOLLO_API_KEY pour voir les chiffres'];

  const res = UrlFetchApp.fetch('https://api.apollo.io/api/v1/emailer_campaigns/search', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { 'X-Api-Key': key, 'Cache-Control': 'no-cache' },
    payload: JSON.stringify({ q_name: APOLLO_SEQUENCE_PREFIX, per_page: 100 })
  });
  if (res.getResponseCode() !== 200) throw new Error('Apollo HTTP ' + res.getResponseCode());
  const n = v => (typeof v === 'number' ? v : 0);   // stats can be "loading"
  const total = { contacted: 0, replied: 0, bounced: 0, clicked: 0, sequences: 0 };
  (JSON.parse(res.getContentText()).emailer_campaigns || [])
    .filter(c => !c.archived && String(c.name).indexOf(APOLLO_SEQUENCE_PREFIX) === 0)
    .forEach(c => {
      total.contacted += n(c.unique_delivered) + n(c.unique_bounced);
      total.replied += n(c.unique_replied);
      total.bounced += n(c.unique_bounced);
      total.clicked += n(c.unique_clicked);
      total.sequences++;
    });

  const last = JSON.parse(props.getProperty('APOLLO_TOTALS') || '{"contacted":0,"replied":0}');
  const week = { contacted: total.contacted - last.contacted, replied: total.replied - last.replied };
  props.setProperty('APOLLO_TOTALS', JSON.stringify(total));

  const pct = (a, b) => (b ? (100 * a / b).toFixed(1).replace('.', ',') + ' %' : '—');
  return [
    'Prospection Apollo (' + total.sequences + ' séquence(s) « ' + APOLLO_SEQUENCE_PREFIX + '… ») :',
    '  Prospects contactés : ' + week.contacted + ' cette semaine · ' + total.contacted + ' depuis le début',
    '  Réponses : ' + week.replied + ' cette semaine · ' + total.replied + ' au total' +
      ' — taux de réponse ' + pct(week.replied, week.contacted) + ' cette semaine · ' + pct(total.replied, total.contacted) + ' au total',
    '  Clics vers le site : ' + total.clicked + ' (' + pct(total.clicked, total.contacted) + ')' +
      ' · Rebonds : ' + total.bounced + ' (' + pct(total.bounced, total.contacted) + ')',
    '  Demandes d\'étude de cas / prospects contactés : ' + pct(weekLeads, week.contacted) + ' cette semaine · ' +
      pct(totalLeads, total.contacted) + ' au total'
  ];
}
