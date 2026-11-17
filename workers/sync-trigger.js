// Cloudflare Worker: starts the "Daily lessons sync" GitHub Action on time.
// GitHub's own schedule often runs hours late; a Worker Cron Trigger fires on the minute.
//
// Settings → Variables and Secrets (type Secret):
//   GITHUB_TOKEN  fine-grained token, repository omaralharkan only, permission "Actions: Read and write"
//   RUN_KEY       any long random word; lets you start a sync by opening  https://<worker>/run?key=<RUN_KEY>
// Settings → Triggers → Cron Triggers: the times to sync (UTC), see README.

const REPO = 'Mohamed-AH/omaralharkan';
const WORKFLOW = 'sync.yml';

async function startSync(env) {
  const r = await fetch(`https://api.github.com/repos/${REPO}/actions/workflows/${WORKFLOW}/dispatches`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${env.GITHUB_TOKEN}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'lessons-sync-trigger',
    },
    body: JSON.stringify({ ref: 'main' }),
  });
  // GitHub answers 204 No Content when the run is queued.
  return { ok: r.status === 204, status: r.status, text: r.status === 204 ? '' : await r.text() };
}

export default {
  async scheduled(event, env, ctx) {
    const res = await startSync(env);
    if (!res.ok) console.log('sync not started', res.status, res.text);
  },

  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname !== '/run') return new Response('Not found', { status: 404 });
    if (!env.RUN_KEY || url.searchParams.get('key') !== env.RUN_KEY) return new Response('Forbidden', { status: 403 });
    const res = await startSync(env);
    return new Response(res.ok ? 'تم طلب التحديث. تظهر الدروس الجديدة خلال دقائق.' : `لم يبدأ التحديث (${res.status})\n${res.text}`,
      { status: res.ok ? 200 : 502, headers: { 'content-type': 'text/plain; charset=utf-8' } });
  },
};
