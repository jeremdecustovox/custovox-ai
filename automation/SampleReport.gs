/**
 * CustoVox - "Get a full sample report by email" form (/demo and /fr/demo).
 *
 * The page posts { app: 'custovox-sample-report', email, first_name, sector, lang, page,
 * utm_source, consent, news, website }; doPost (Web.gs) hands it to handleSampleReport_.
 * Each valid request becomes a row in the "Exemples de rapport" sheet, and the script emails
 * the link to the (100 % fictional) sample report. No commercial follow-up is sent.
 *
 * Sender: never the personal address of the account that owns the script. Set the Script
 * Property SAMPLE_FROM (Project settings > Script properties) to a CustoVox address that is
 * configured as a "Send mail as" alias of this Gmail account. Until it is set (or if it is not
 * a valid alias), nothing is sent: the row is saved with the status "not sent: no sender".
 *
 * Unsubscribe / deletion: every email carries a personal link (doGet ?unsub=<id>) that marks
 * the row "unsubscribed"; deletion requests go to privacy@custovox.ai (privacy policy).
 */

const SAMPLE_SHEET = 'Exemples de rapport';
const SAMPLE_HEADERS = ['date', 'email', 'first name', 'sector', 'language', 'utm source', 'page',
  'consent', 'consent date', 'news', 'status', 'unsubscribe id'];
const SAMPLE_DAILY_CAP = 50;   // anti-abuse: at most 50 automatic emails per day
const SAMPLE_LINKS = { en: 'https://custovox.ai/sample-report', fr: 'https://custovox.ai/fr/exemple-de-rapport' };

function handleSampleReport_(p) {
  const email = String(p.email || '').trim().toLowerCase().slice(0, 200);
  // "website" is a hidden field: only bots fill it in. Consent box is required.
  if (p.website || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || p.consent !== true) {
    return ContentService.createTextOutput('ignored');
  }
  const clean = (v, n) => String(v || '').replace(/^[=+\-@]/, "'").slice(0, n || 100);  // no formulas in the sheet
  const lang = p.lang === 'fr' ? 'fr' : 'en';
  const sheet = sampleSheet_();
  const rows = sheet.getLastRow() > 1 ? sheet.getRange(2, 1, sheet.getLastRow() - 1, SAMPLE_HEADERS.length).getValues() : [];
  const dayAgo = Date.now() - 864e5;
  const recent = rows.some(r => r[1] === email && new Date(r[0]).getTime() > dayAgo);
  const unsubscribed = rows.some(r => r[1] === email && r[10] === 'unsubscribed');
  const now = new Date();
  const id = Utilities.getUuid();
  const row = [now, email, clean(p.first_name, 60), clean(p.sector), lang, clean(p.utm_source, 40), clean(p.page),
    'yes', now, p.news === true ? 'yes' : 'no', '', id];

  let status;
  if (recent) status = 'duplicate (24 h)';
  else if (unsubscribed) status = 'not sent: unsubscribed before';
  else status = sendSampleReport_(email, row[2], lang, id);
  row[10] = status;
  sheet.appendRow(row);

  if (!recent) {
    MailApp.sendEmail(NOTIFY_LEADS_TO, '📄 Demande d\'exemple de rapport : ' + email, [
      'Nouvelle demande d\'exemple de rapport sur custovox.ai :',
      '',
      'E-mail : ' + email,
      'Prénom : ' + (row[2] || '—'),
      'Secteur : ' + (row[3] || '—'),
      'Langue : ' + lang,
      'Source (utm_source) : ' + (row[5] || '—'),
      'Page : https://custovox.ai' + row[6],
      'Nouvelles CustoVox : ' + (row[9] === 'yes' ? 'oui' : 'non'),
      'Envoi automatique : ' + status,
      '',
      'Rappel : pas de relance commerciale ; ajouter ce contact à la blocklist de prospection.',
      'Base de données : ' + SpreadsheetApp.getActiveSpreadsheet().getUrl()
    ].join('\n'));
  }
  return ContentService.createTextOutput('ok');
}

/** Sends the sample-report link. Returns the status written in the sheet. */
function sendSampleReport_(email, firstName, lang, id) {
  const from = PropertiesService.getScriptProperties().getProperty('SAMPLE_FROM');
  if (!from) return 'not sent: no sender';
  if (GmailApp.getAliases().indexOf(from) === -1) return 'not sent: sender is not a Gmail alias';
  const props = PropertiesService.getScriptProperties();
  const today = Utilities.formatDate(new Date(), 'Europe/Paris', 'yyyy-MM-dd');
  const count = props.getProperty('SAMPLE_COUNT_' + today) | 0;
  if (count >= SAMPLE_DAILY_CAP) return 'not sent: daily cap';

  const unsub = ScriptApp.getService().getUrl() + '?unsub=' + id;
  const hi = firstName ? (lang === 'fr' ? 'Bonjour ' + firstName + ',' : 'Hello ' + firstName + ',')
    : (lang === 'fr' ? 'Bonjour,' : 'Hello,');
  const body = lang === 'fr' ? [
    hi, '',
    'Voici l\'exemple de rapport que vous avez demandé sur custovox.ai :',
    SAMPLE_LINKS.fr, '',
    'Toutes les données de ce rapport sont fictives (« Maison Verveine » est un hôtel-boutique imaginaire).', '',
    'Vous recevez cet email parce que vous l\'avez demandé sur custovox.ai. Nous ne vous enverrons pas d\'autre message,',
    'sauf si vous avez coché la case « nouvelles de CustoVox ».',
    'Se désinscrire : ' + unsub,
    'Supprimer vos données : privacy@custovox.ai', '',
    'CustoVox.ai — https://custovox.ai'
  ] : [
    hi, '',
    'Here is the sample report you asked for on custovox.ai:',
    SAMPLE_LINKS.en, '',
    'All data in this report is fictional ("Maison Verveine" is an imaginary hotel and shop).', '',
    'You receive this email because you asked for it on custovox.ai. We will not send you anything else',
    'unless you ticked the "news from CustoVox" box.',
    'Unsubscribe: ' + unsub,
    'Delete your data: privacy@custovox.ai', '',
    'CustoVox.ai — https://custovox.ai'
  ];
  GmailApp.sendEmail(email, lang === 'fr' ? 'Votre exemple de rapport custovox.ai' : 'Your custovox.ai sample report',
    body.join('\n'), { from: from, name: 'CustoVox.ai', replyTo: from });
  props.setProperty('SAMPLE_COUNT_' + today, String(count + 1));
  return 'sent';
}

/** Unsubscribe link (doGet in Web.gs): marks every row of that email "unsubscribed", news "no". */
function handleUnsubscribe_(id) {
  const sheet = sampleSheet_();
  const n = sheet.getLastRow() - 1;
  let email = '';
  if (n > 0 && /^[0-9a-f-]{36}$/i.test(id)) {
    const values = sheet.getRange(2, 1, n, SAMPLE_HEADERS.length).getValues();
    const hit = values.find(r => r[11] === id);
    if (hit) email = hit[1];
    if (email) values.forEach((r, i) => {
      if (r[1] === email) sheet.getRange(i + 2, 10, 1, 2).setValues([['no', 'unsubscribed']]);
    });
  }
  const msg = email ? 'Vous êtes désinscrit(e). You are unsubscribed.' : 'Lien inconnu ou expiré. Unknown or expired link.';
  return HtmlService.createHtmlOutput('<p style="font-family:sans-serif;padding:2rem">' + msg +
    '<br>privacy@custovox.ai — <a href="https://custovox.ai">custovox.ai</a></p>').setTitle('CustoVox.ai');
}

function sampleSheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(SAMPLE_SHEET);
  if (!sheet) {
    sheet = ss.insertSheet(SAMPLE_SHEET);
    sheet.appendRow(SAMPLE_HEADERS);
    sheet.setFrozenRows(1);
    sheet.getRange(1, 1, 1, SAMPLE_HEADERS.length).setFontWeight('bold');
  }
  return sheet;
}

/** Run once from the editor: creates the sheet and shows whether the sender alias is ready. */
function setupSampleReport() {
  sampleSheet_();
  const from = PropertiesService.getScriptProperties().getProperty('SAMPLE_FROM');
  Logger.log(!from ? 'SAMPLE_FROM is not set: nothing will be sent.'
    : GmailApp.getAliases().indexOf(from) === -1 ? 'SAMPLE_FROM is not a "Send mail as" alias of this account.'
    : 'Ready: emails will be sent from the CustoVox alias.');
}
