/**
 * CustoVox - email when a scheduled Buffer post goes live on LinkedIn.
 *
 * Setup (once):
 * 1. Project Settings > Script Properties > add BUFFER_TOKEN = your Buffer API token.
 * 2. Run `setupBufferNotify` and accept the permissions.
 */

const NOTIFY_EMAIL = 'jeremie@custovox.ai';
const BUFFER_ORG_ID = '6ac9d163391fa2035024ebfb';
const BUFFER_CHANNEL_ID = '6ac9d1ec6a5c39ccb66d8b21';
const DEFAULT_COMMENT = 'Learn more → https://custovox.ai';
// First comment to add by hand, per post (Buffer free plan can't post it automatically).
const COMMENTS = {
  '6ac9e59fd9cab260a7b6a4b5': 'Read the full analysis → https://custovox.ai/blog/g2-reviews-nlp-analysis',     // 12/10 G2
  '6ac9e8cfd9cab260a7b707c0': 'Full guide → https://custovox.ai/blog/how-nlp-reduces-customer-churn',           // 21/10 churn
  '6ac9e8cfb07d37ac97649be2': 'Read the full analysis → https://custovox.ai/blog/g2-reviews-nlp-analysis',     // 28/10 ratings
  '6ac9e8d0b07d37ac97649c20': 'Read the full analysis → https://custovox.ai/blog/g2-reviews-nlp-analysis',     // 04/11 hotels
  '6ac9e8d1f91f772d45855d34': 'Full guide → https://custovox.ai/blog/how-nlp-reduces-customer-churn',           // 11/11 signals
  '6ac9e8d1b07d37ac97649c4a': 'Tools compared → https://custovox.ai/blog/top-5-sentiment-analysis-tools'        // 18/11 languages
};

/** Creates the 15-minute check. Run once. */
function setupBufferNotify() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'checkBufferPosts')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('checkBufferPosts').timeBased().everyMinutes(15).create();
  checkBufferPosts();
}

function checkBufferPosts() {
  const token = PropertiesService.getScriptProperties().getProperty('BUFFER_TOKEN');
  if (!token) throw new Error('BUFFER_TOKEN is missing in Script Properties');

  const query = '{ posts(input:{organizationId:"' + BUFFER_ORG_ID + '", filter:{channelIds:["' +
    BUFFER_CHANNEL_ID + '"], status:[sent, error]}}){ edges{ node{ id status text sentAt dueAt externalLink error{ message } } } } }';
  const res = UrlFetchApp.fetch('https://api.buffer.com', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' + token },
    payload: JSON.stringify({ query: query }),
    muteHttpExceptions: true
  });
  const data = JSON.parse(res.getContentText());
  if (data.errors) throw new Error(JSON.stringify(data.errors));

  const props = PropertiesService.getScriptProperties();
  const done = JSON.parse(props.getProperty('NOTIFIED') || '{}');
  const tz = 'Europe/Paris';

  data.data.posts.edges.map(e => e.node).forEach(p => {
    const key = p.id + ':' + p.status;
    if (done[key]) return;
    const firstLine = (p.text || '').split('\n')[0];
    const when = Utilities.formatDate(new Date(p.sentAt || p.dueAt), tz, "dd/MM/yyyy 'à' HH:mm");
    let subject, body;
    if (p.status === 'sent') {
      const comment = COMMENTS[p.id] || DEFAULT_COMMENT;
      subject = '✅ Post LinkedIn publié : ' + firstLine.slice(0, 60);
      body = [
        'Votre post LinkedIn a été publié le ' + when + ' (heure de Paris).',
        '',
        'Début du post : ' + firstLine,
        'Voir le post : ' + (p.externalLink || 'https://www.linkedin.com/company/custovox-ai/'),
        '',
        'À FAIRE MAINTENANT : ajoutez ce premier commentaire sous le post :',
        comment
      ].join('\n');
    } else {
      subject = '❌ Échec de publication LinkedIn : ' + firstLine.slice(0, 60);
      body = [
        'Buffer n\'a pas pu publier le post prévu le ' + when + '.',
        'Erreur : ' + ((p.error && p.error.message) || 'inconnue'),
        '',
        'Début du post : ' + firstLine,
        'Ouvrez Buffer pour le republier : https://publish.buffer.com'
      ].join('\n');
    }
    MailApp.sendEmail(NOTIFY_EMAIL, subject, body);
    done[key] = new Date().toISOString();
  });
  props.setProperty('NOTIFIED', JSON.stringify(done));
}
