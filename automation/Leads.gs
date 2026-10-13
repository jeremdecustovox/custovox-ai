/**
 * CustoVox - leads database: signups from the custovox.ai form (all languages).
 *
 * Lives in the Google Workspace spreadsheet "CustoVox Leads" (personal data), with Web.gs.
 * The website case-study form posts { app: 'custovox-lead', email, industry, volume, lang,
 * page, consent, newsletter, website }; doPost (Web.gs) hands it to handleLead_. Each valid
 * signup becomes a row in the "Leads" sheet and an email to NOTIFY_LEADS_TO.
 */

const LEADS_SHEET = 'Leads';
const NOTIFY_LEADS_TO = 'jeremie@custovox.ai';
const LEAD_HEADERS = ['date', 'email', 'industry', 'conversations / month', 'language', 'page',
  'consent', 'newsletter', 'status', 'notes'];

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
    'yes', p.newsletter === true ? 'yes' : 'no', existing ? 'duplicate' : 'new', ''];
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
      'Actualités (newsletter) : ' + (row[7] === 'yes' ? 'oui' : 'non'),
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

/** Run once from the editor to create the "Leads" and "Contacts" sheets. */
function setupLeads() {
  leadsSheet_();
  contactsSheet_();
}

// ---------------------------------------------------------------------------
// Contact form ("Nous contacter" on the landing page): { app: 'custovox-contact',
// name, email, company, message, lang, page, website }.
// ---------------------------------------------------------------------------

const CONTACTS_SHEET = 'Contacts';
const CONTACT_HEADERS = ['date', 'name', 'email', 'company', 'message', 'language', 'page', 'status'];

function handleContact_(p) {
  const email = String(p.email || '').trim().toLowerCase().slice(0, 200);
  const name = String(p.name || '').trim();
  const message = String(p.message || '').trim();
  if (p.website || !name || !message || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
    return ContentService.createTextOutput('ignored');
  }
  const clean = (v, max) => String(v || '').trim().replace(/^[=+\-@]/, "'").slice(0, max);
  const row = [new Date(), clean(name, 100), email, clean(p.company, 100), clean(message, 5000),
    clean(p.lang, 10), clean(p.page, 100), 'to answer'];
  contactsSheet_().appendRow(row);

  MailApp.sendEmail(NOTIFY_LEADS_TO, '✉️ Nouveau message de contact : ' + row[1], [
    'Nouveau message via le formulaire de contact de custovox.ai :',
    '',
    'Nom : ' + row[1],
    'E-mail : ' + email,
    'Entreprise : ' + (row[3] || '-'),
    'Page : https://custovox.ai' + row[6],
    '',
    'Message :',
    row[4],
    '',
    'Promesse faite : réponse sous 48 h.',
    'Tous les messages : ' + SpreadsheetApp.getActiveSpreadsheet().getUrl()
  ].join('\n'), { replyTo: email });
  return ContentService.createTextOutput('ok');
}

function contactsSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(CONTACTS_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(CONTACTS_SHEET);
    sheet.appendRow(CONTACT_HEADERS);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, CONTACT_HEADERS.length).setFontWeight('bold');
  }
  return sheet;
}
