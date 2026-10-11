/**
 * CustoVox - leads database: signups from the custovox.ai form (all languages).
 *
 * The website form posts { app: 'custovox-lead', email, industry, volume, lang, page,
 * consent, website } to the same web app URL as the usage statistics; doPost in Code.gs
 * hands it to handleLead_. Each valid signup becomes a row in the "Leads" sheet and an
 * email to NOTIFY_LEADS_TO.
 */

const LEADS_SHEET = 'Leads';
const NOTIFY_LEADS_TO = 'jeremie@custovox.ai';
const LEAD_HEADERS = ['date', 'email', 'industry', 'conversations / month', 'language', 'page',
  'consent', 'status', 'notes'];

function handleLead_(p) {
  const email = String(p.email || '').trim().toLowerCase().slice(0, 200);
  // "website" is a hidden field: only bots fill it in.
  if (p.website || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || p.consent !== true) {
    return ContentService.createTextOutput('ignored');
  }
  const clean = v => String(v || '').replace(/^[=+\-@]/, "'").slice(0, 100);  // no formulas in the sheet
  const sheet = leadsSheet_();
  const existing = sheet.getRange(2, 2, Math.max(sheet.getLastRow() - 1, 1), 1).getValues()
    .some(r => r[0] === email);
  const row = [new Date(), email, clean(p.industry), clean(p.volume), clean(p.lang), clean(p.page),
    'yes', existing ? 'duplicate' : 'new', ''];
  sheet.appendRow(row);

  if (!existing) {
    MailApp.sendEmail(NOTIFY_LEADS_TO, '🎯 Nouveau prospect : ' + email, [
      'Nouvelle inscription sur custovox.ai :',
      '',
      'E-mail : ' + email,
      'Secteur : ' + row[2],
      'Conversations / mois : ' + row[3],
      'Langue : ' + row[4],
      'Page : https://custovox.ai' + row[5],
      '',
      'Promesse faite : étude de cas NLP gratuite sous 48 h.',
      'Base de données : ' + SpreadsheetApp.getActiveSpreadsheet().getUrl()
    ].join('\n'));
  }
  return ContentService.createTextOutput('ok');
}

function leadsSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(LEADS_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(LEADS_SHEET);
    sheet.appendRow(LEAD_HEADERS);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, LEAD_HEADERS.length).setFontWeight('bold');
  }
  return sheet;
}

/** Run once from the editor to create the "Leads" sheet and check the setup. */
function setupLeads() {
  leadsSheet_();
}
