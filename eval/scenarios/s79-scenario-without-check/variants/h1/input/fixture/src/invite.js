"use strict";

const codes = new Map();

function issue(code, owner) {
  codes.set(code, { owner, usedBy: null });
}

function redeem(code, user) {
  const entry = codes.get(code);
  if (!entry) return { ok: false, reason: "unknown_code" };
  entry.usedBy = user;
  return { ok: true };
}

function lookup(code) {
  return codes.get(code) || null;
}

module.exports = { issue, redeem, lookup, reset: () => codes.clear() };
