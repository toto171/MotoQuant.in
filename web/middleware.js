// Tells the API who the visitor is (see motoquant/ratelimit.py).
//
// Every /api request reaches the backend from Vercel's servers, so without
// this the backend sees one of Vercel's addresses for every visitor and they
// all share the same rate limits. Vercel sets x-real-ip and x-forwarded-for
// itself, replacing anything the visitor sent, so the first address there is
// the real one. The shared secret (MOTOQUANT_PROXY_SECRET, set on Vercel and
// on the API service) proves the header came from this proxy.
//
// Without the secret the two headers are stripped, and the API falls back to
// its own X-Forwarded-For handling.
import { NextResponse } from 'next/server';

const AUTH_HEADER = 'x-motoquant-proxy-auth';
const CLIENT_IP_HEADER = 'x-motoquant-client-ip';
const MIN_SECRET_LENGTH = 16;

export function visitorIp(headers) {
  const raw = headers.get('x-real-ip') || headers.get('x-forwarded-for') || '';
  return raw.split(',')[0].trim();
}

export function middleware(request) {
  const headers = new Headers(request.headers);
  // Never forward values a visitor supplied for these.
  headers.delete(AUTH_HEADER);
  headers.delete(CLIENT_IP_HEADER);

  const secret = process.env.MOTOQUANT_PROXY_SECRET || '';
  const ip = visitorIp(request.headers);
  if (secret.length >= MIN_SECRET_LENGTH && ip) {
    headers.set(AUTH_HEADER, secret);
    headers.set(CLIENT_IP_HEADER, ip);
  }
  return NextResponse.next({ request: { headers } });
}

export const config = { matcher: '/api/:path*' };
