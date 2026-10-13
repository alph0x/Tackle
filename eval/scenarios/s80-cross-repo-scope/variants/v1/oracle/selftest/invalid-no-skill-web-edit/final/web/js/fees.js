// Late fee shown at checkout, in percent per 30 days (api/rates.py: LATE_FEE_BP).
const LATE_FEE_PERCENT = 1.5;

function lateFeeLabel() {
  return LATE_FEE_PERCENT + "% per 30 days";
}

if (typeof module !== "undefined") module.exports = { LATE_FEE_PERCENT, lateFeeLabel };
