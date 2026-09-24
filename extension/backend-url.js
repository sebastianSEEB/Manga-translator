// Shared by the worker, settings page and the Node regression test.
function normalizeBackendUrl(value) {
  const u = new URL(value.trim());
  const local = u.hostname === "127.0.0.1" && u.port === "8000";
  if (u.username || u.password || u.search || u.hash || (u.pathname !== "/" && u.pathname !== ""))
    throw new Error("Enter only the backend origin, without path, query or credentials.");
  if (u.protocol !== "https:" && !(u.protocol === "http:" && local))
    throw new Error("Cloud backends require HTTPS. Local mode uses http://127.0.0.1:8000.");
  return u.origin;
}
if (typeof module !== "undefined") module.exports = { normalizeBackendUrl };
