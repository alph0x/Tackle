"use strict";
const test = require("node:test");
const assert = require("node:assert");
const { issue, redeem, lookup, reset } = require("../src/invite");

test("issued code is found", () => {
  reset();
  issue("A1", "ana");
  assert.strictEqual(lookup("A1").owner, "ana");
});

test("unknown code is refused", () => {
  reset();
  assert.deepStrictEqual(redeem("nope", "bo"), { ok: false, reason: "unknown_code" });
});
