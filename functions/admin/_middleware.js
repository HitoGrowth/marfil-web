/**
 * Cierre de seguridad del panel /admin (Cloudflare Pages Functions).
 *
 * Cloudflare Access es la puerta principal: solo deja pasar los correos de la lista de
 * administradores. Este middleware es la segunda cerradura y falla cerrado: si la
 * petición no trae un token de Access válido (firma, audiencia, emisor y caducidad),
 * responde 404 como si el panel no existiera. Así, aunque Access se desactive o se
 * configure mal, nadie más puede ver /admin.
 *
 * Variables de entorno (Pages → Settings → Variables and Secrets):
 *   ACCESS_TEAM_DOMAIN  p. ej. "marfil.cloudflareaccess.com"
 *   ACCESS_AUD          "Application Audience (AUD) Tag" de la aplicación de Access
 *   ADMIN_EMAILS        opcional: correos permitidos separados por comas
 */

const NOT_FOUND = () =>
  new Response('Not found', {
    status: 404,
    headers: { 'content-type': 'text/plain; charset=utf-8', 'cache-control': 'no-store', 'x-robots-tag': 'noindex' }
  });

let certCache = { url: '', at: 0, keys: [] };

function b64urlToBytes(s) {
  const b64 = s.replace(/-/g, '+').replace(/_/g, '/') + '==='.slice((s.length + 3) % 4);
  const bin = atob(b64);
  const out = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
  return out;
}

function b64urlJson(s) {
  return JSON.parse(new TextDecoder().decode(b64urlToBytes(s)));
}

async function accessKeys(teamDomain, refresh) {
  const url = `https://${teamDomain}/cdn-cgi/access/certs`;
  if (!refresh && certCache.url === url && Date.now() - certCache.at < 10 * 60 * 1000) return certCache.keys;
  const res = await fetch(url, { cf: { cacheTtl: 600 } });
  if (!res.ok) throw new Error('certs ' + res.status);
  const { keys = [] } = await res.json();
  certCache = { url, at: Date.now(), keys };
  return keys;
}

function readToken(request) {
  const header = request.headers.get('cf-access-jwt-assertion');
  if (header) return header;
  const cookie = request.headers.get('cookie') || '';
  const m = cookie.match(/(?:^|;\s*)CF_Authorization=([^;]+)/);
  return m ? m[1] : null;
}

async function verifyAccessJwt(token, env, now = Date.now() / 1000) {
  const team = (env.ACCESS_TEAM_DOMAIN || '').replace(/^https?:\/\//, '').replace(/\/+$/, '');
  const aud = env.ACCESS_AUD || '';
  if (!token || !team || !aud) return null;

  const parts = token.split('.');
  if (parts.length !== 3) return null;
  let header, payload;
  try {
    header = b64urlJson(parts[0]);
    payload = b64urlJson(parts[1]);
  } catch {
    return null;
  }
  if (header.alg !== 'RS256' || !header.kid) return null;

  let keys = await accessKeys(team, false);
  let jwk = keys.find((k) => k.kid === header.kid);
  if (!jwk) {
    keys = await accessKeys(team, true); // rotación de claves
    jwk = keys.find((k) => k.kid === header.kid);
  }
  if (!jwk) return null;

  const key = await crypto.subtle.importKey(
    'jwk',
    { kty: jwk.kty, n: jwk.n, e: jwk.e, alg: 'RS256', ext: true },
    { name: 'RSASSA-PKCS1-v1_5', hash: 'SHA-256' },
    false,
    ['verify']
  );
  const ok = await crypto.subtle.verify(
    'RSASSA-PKCS1-v1_5',
    key,
    b64urlToBytes(parts[2]),
    new TextEncoder().encode(parts[0] + '.' + parts[1])
  );
  if (!ok) return null;

  const auds = Array.isArray(payload.aud) ? payload.aud : [payload.aud];
  if (!auds.includes(aud)) return null;
  if (payload.iss !== `https://${team}`) return null;
  if (typeof payload.exp !== 'number' || payload.exp < now) return null;
  if (typeof payload.nbf === 'number' && payload.nbf > now + 60) return null;

  const allow = (env.ADMIN_EMAILS || '')
    .split(',')
    .map((e) => e.trim().toLowerCase())
    .filter(Boolean);
  if (allow.length && !allow.includes(String(payload.email || '').toLowerCase())) return null;

  return payload;
}

export async function onRequest(context) {
  const { request, env, next } = context;
  let claims = null;
  try {
    claims = await verifyAccessJwt(readToken(request), env);
  } catch {
    claims = null;
  }
  if (!claims) return NOT_FOUND();

  const res = await next();
  const out = new Response(res.body, res);
  out.headers.set('cache-control', 'private, no-store');
  out.headers.set('x-robots-tag', 'noindex, nofollow');
  out.headers.set('x-frame-options', 'DENY');
  out.headers.set('referrer-policy', 'same-origin');
  return out;
}
