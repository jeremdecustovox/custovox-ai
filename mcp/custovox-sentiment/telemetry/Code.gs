/**
 * CustoVox sentiment MCP - anonymous usage telemetry receiver.
 *
 * Paste this file into Extensions > Apps Script of the Google Sheet,
 * run `setup` once, then deploy as a Web app (Execute as: Me, Access: Anyone).
 */

const REPORT_EMAIL = 'jeremie@custovox.ai';
const EVENTS_SHEET = 'Events';
const REPORTS_SHEET = 'Rapports';
const ALLOWED_TOOLS = ['analyze_sentiment', 'analyze_batch'];
const ALLOWED_SENTIMENTS = ['Very Positive', 'Positive', 'Neutral', 'Negative', 'Very Negative'];

/** Run once: creates the sheets and the weekly trigger (Monday 8:00). */
function setup() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let events = ss.getSheetByName(EVENTS_SHEET);
  if (!events) events = ss.insertSheet(EVENTS_SHEET);
  if (events.getLastRow() === 0) {
    events.appendRow(['date', 'tool', 'sentiment', 'count', 'version', 'session']);
    events.setFrozenRows(1);
  }
  let reports = ss.getSheetByName(REPORTS_SHEET);
  if (!reports) reports = ss.insertSheet(REPORTS_SHEET);
  if (reports.getLastRow() === 0) {
    reports.appendRow(['semaine du', 'au', 'appels', 'textes analysés', 'sessions',
      'semaine précédente (textes)', 'évolution', 'par outil', 'par sentiment', 'par version']);
    reports.setFrozenRows(1);
  }
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'weeklyReport')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('weeklyReport')
    .timeBased().onWeekDay(ScriptApp.WeekDay.MONDAY).atHour(8).create();
}

/** Receives one event from the MCP server. Never stores the analyzed text. */
function doPost(e) {
  try {
    const p = JSON.parse(e.postData.contents);
    if (p.app !== 'custovox-sentiment' || ALLOWED_TOOLS.indexOf(p.tool) === -1) {
      return ContentService.createTextOutput('ignored');
    }
    const version = String(p.version || '').slice(0, 20);
    const session = String(p.session || '').slice(0, 40);
    const now = new Date();
    const rows = (p.results || [])
      .filter(r => ALLOWED_SENTIMENTS.indexOf(r.sentiment) !== -1)
      .slice(0, 5)
      .map(r => [now, p.tool, r.sentiment, Math.min(Math.max(parseInt(r.count, 10) || 0, 0), 50), version, session]);
    if (rows.length) {
      const sheet = SpreadsheetApp.getActiveSpreadsheet().getSheetByName(EVENTS_SHEET);
      sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, rows[0].length).setValues(rows);
    }
    return ContentService.createTextOutput('ok');
  } catch (err) {
    return ContentService.createTextOutput('error');
  }
}

/** Summarises the last 7 days, writes it to "Rapports" and emails it. */
function weeklyReport() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const data = ss.getSheetByName(EVENTS_SHEET).getDataRange().getValues().slice(1);
  const end = new Date();
  const start = new Date(end.getTime() - 7 * 864e5);
  const prevStart = new Date(start.getTime() - 7 * 864e5);

  const week = data.filter(r => r[0] >= start && r[0] < end);
  const prevTexts = data.filter(r => r[0] >= prevStart && r[0] < start)
    .reduce((s, r) => s + Number(r[3]), 0);

  const texts = week.reduce((s, r) => s + Number(r[3]), 0);
  const sessions = new Set(week.map(r => r[5])).size;
  // One call = one (session, timestamp) pair, since a batch writes several rows at once.
  const calls = new Set(week.map(r => r[5] + '|' + r[0].getTime())).size;
  const sumBy = col => {
    const m = {};
    week.forEach(r => { m[r[col]] = (m[r[col]] || 0) + Number(r[3]); });
    return Object.keys(m).sort((a, b) => m[b] - m[a]).map(k => k + ': ' + m[k]).join(', ') || '-';
  };
  const byTool = sumBy(1), bySentiment = sumBy(2), byVersion = sumBy(4);
  const change = prevTexts ? Math.round((texts - prevTexts) / prevTexts * 100) + ' %' : 'n/a';

  const fmt = d => Utilities.formatDate(d, Session.getScriptTimeZone(), 'dd/MM/yyyy');
  ss.getSheetByName(REPORTS_SHEET).appendRow([fmt(start), fmt(end), calls, texts, sessions,
    prevTexts, change, byTool, bySentiment, byVersion]);

  const body = [
    'Rapport hebdomadaire custovox-sentiment (MCP)',
    'Du ' + fmt(start) + ' au ' + fmt(end),
    '',
    'Appels : ' + calls,
    'Textes analysés : ' + texts + ' (semaine précédente : ' + prevTexts + ', évolution : ' + change + ')',
    'Sessions distinctes : ' + sessions,
    '',
    'Par outil : ' + byTool,
    'Par sentiment : ' + bySentiment,
    'Par version : ' + byVersion,
    '',
    'Détail : ' + ss.getUrl()
  ].join('\n');
  MailApp.sendEmail(REPORT_EMAIL, 'custovox-sentiment : rapport du ' + fmt(end), body);
}
