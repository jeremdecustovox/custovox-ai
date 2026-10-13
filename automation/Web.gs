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
  const body = [
    'Prospects et messages custovox.ai — semaine du ' + fmt(since) + ' au ' + fmt(new Date()),
    '',
    'Demandes d\'étude de cas : ' + weekLeads.length + ' cette semaine · ' + leads.length + ' au total',
    'Dont inscrits aux actualités : ' + weekLeads.filter(r => r[7] === 'yes').length + ' cette semaine',
  ].concat(weekLeads.map(r => '  - ' + r[1] + ' · ' + r[2] + ' · ' + r[3] + ' · ' + r[4]), [
    '',
    'Messages de contact : ' + weekContacts.length + ' cette semaine · ' + toAnswer + ' encore marqués « to answer »',
  ], weekContacts.map(r => '  - ' + r[1] + ' (' + r[2] + ')' + (r[3] ? ' · ' + r[3] : '')), [
    '',
    'Base de données : ' + SpreadsheetApp.getActiveSpreadsheet().getUrl()
  ]).join('\n');
  MailApp.sendEmail(NOTIFY_LEADS_TO, 'custovox.ai : prospects de la semaine (' + fmt(new Date()) + ')', body);
}
