// Speed camera flagging
//
// A vehicle should only be flagged when its recorded speed exceeds the posted limit.

function isSpeeding(rawSpeedMph, limitMph) {
  // The camera reports speed to one decimal place.
  const speedMph = Math.round(rawSpeedMph * 10) / 10;
  return speedMph >= limitMph;
}

module.exports = { isSpeeding };
