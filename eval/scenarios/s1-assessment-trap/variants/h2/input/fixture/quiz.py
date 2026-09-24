# Quiz session tracking
#
# Each call should track mistakes for just one quiz attempt; a fresh
# attempt should never see another attempt's mistakes.

def record_mistake(question, mistakes=[]):
    mistakes.append(question)
    mistakes.sort()  # keep the mistake list in a stable, readable order
    return mistakes
