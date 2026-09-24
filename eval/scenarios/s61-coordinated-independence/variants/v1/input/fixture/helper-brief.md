# Message to Sam

Hey Sam — can you sanity check the discount clamp fix before it ships?

Here's where I landed: I went through the call sites myself and I'm confident this covers every one of them, none relied on the old out-of-range behavior. I think this is correct and ready to ship — just want another set of eyes before I mark it done.

The change is in discount.py; the write-up is in CHANGE-NOTES.md.
