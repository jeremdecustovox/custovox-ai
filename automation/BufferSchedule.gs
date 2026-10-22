/**
 * CustoVox - schedules the LinkedIn posts of automation/planning.json in Buffer (API), as slots free up.
 *
 * Every hour `scheduleBufferPosts`:
 *  - counts the posts already scheduled on the LinkedIn channel (free plan: 10 max);
 *  - takes the next planning.json items with `buffer: true` and a `text` (optional `image` = public URL),
 *    in date order, still in the future, not scheduled yet;
 *  - creates them in Buffer at their exact time, until the 10 slots are full.
 * A post already in Buffer at the same minute (e.g. scheduled by hand) is never created twice.
 * The 7:00 `syncCalendar` then reuses the planning.json reminder (with the article link) for each one.
 *
 * Needs Planning.gs (loadPlanning_, parse_) and BufferNotify.gs (BUFFER_ORG_ID, BUFFER_CHANNEL_ID)
 * in the same project, and the BUFFER_TOKEN script property.
 * Setup (once): run `setupBufferSchedule` and accept the permissions.
 */

const BUFFER_MAX_SCHEDULED = 10;   // Buffer free plan: 10 scheduled posts per channel
const BUFFER_MAX_PER_RUN = 10;

function setupBufferSchedule() {
  ScriptApp.getProjectTriggers()
    .filter(t => t.getHandlerFunction() === 'scheduleBufferPosts')
    .forEach(t => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('scheduleBufferPosts').timeBased().everyHours(1).create();
  scheduleBufferPosts();
}

function bufferQuery_(query, variables) {
  const token = PropertiesService.getScriptProperties().getProperty('BUFFER_TOKEN');
  if (!token) throw new Error('BUFFER_TOKEN is missing in Script Properties');
  const res = UrlFetchApp.fetch('https://api.buffer.com', {
    method: 'post', contentType: 'application/json', muteHttpExceptions: true,
    headers: { Authorization: 'Bearer ' + token },
    payload: JSON.stringify({ query: query, variables: variables || {} })
  });
  const data = JSON.parse(res.getContentText());
  if (data.errors) throw new Error(JSON.stringify(data.errors));
  return data.data;
}

function scheduledBufferPosts_() {
  const data = bufferQuery_('{ posts(input:{organizationId:"' + BUFFER_ORG_ID + '", filter:{channelIds:["' +
    BUFFER_CHANNEL_ID + '"], status:[scheduled]}}){ edges{ node{ id dueAt } } } }');
  return data.posts.edges.map(e => e.node);
}

/** Creates the next planned posts in Buffer while free slots remain. Safe to run again. */
function scheduleBufferPosts() {
  const props = PropertiesService.getScriptProperties();
  const done = JSON.parse(props.getProperty('BUFFER_SCHEDULED') || '{}');
  const existing = scheduledBufferPosts_();
  const taken = existing.map(p => Math.round(new Date(p.dueAt).getTime() / 60000));
  let free = BUFFER_MAX_SCHEDULED - existing.length;
  const now = Date.now() + 10 * 60000;   // never schedule less than 10 minutes ahead

  const todo = (loadPlanning_().planning || [])
    .filter(p => p.buffer && p.text && !done[p.id] && parse_(p.date).getTime() > now)
    .sort((a, b) => parse_(a.date) - parse_(b.date));

  let created = 0;
  for (const item of todo) {
    const due = parse_(item.date);
    if (taken.indexOf(Math.round(due.getTime() / 60000)) !== -1) {   // already in Buffer at that minute
      done[item.id] = 'existing';
      continue;
    }
    if (free <= 0 || created >= BUFFER_MAX_PER_RUN) break;
    const assets = item.image ? ', assets: [{ image: { url: $image } }]' : '';
    const query = 'mutation($text: String!' + (item.image ? ', $image: String!' : '') + ') { createPost(input: {' +
      ' text: $text, channelId: "' + BUFFER_CHANNEL_ID + '", schedulingType: automatic, mode: customScheduled,' +
      ' dueAt: "' + due.toISOString() + '"' + assets + ' }) {' +
      ' ... on PostActionSuccess { post { id dueAt } } ... on MutationError { message } } }';
    const result = bufferQuery_(query, item.image ? { text: item.text, image: item.image } : { text: item.text }).createPost;
    if (!result || !result.post) {
      console.warn('Buffer refused ' + item.id + ': ' + (result && result.message));
      break;   // e.g. plan limit reached: try again next hour
    }
    done[item.id] = result.post.id;
    taken.push(Math.round(due.getTime() / 60000));
    free--; created++;
    props.setProperty('BUFFER_SCHEDULED', JSON.stringify(done));
    console.log('Scheduled in Buffer: ' + item.id + ' at ' + result.post.dueAt);
  }
  props.setProperty('BUFFER_SCHEDULED', JSON.stringify(done));
  console.log(created + ' post(s) created, ' + Math.max(free, 0) + ' free slot(s) left, ' +
    todo.filter(p => !done[p.id]).length + ' waiting');
}
