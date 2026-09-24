# Assistant memory

This project's coding assistant reads `.assistant/memory.json` at the start of every session and updates it as it goes.

- Setting `"learning"` to `"off"` stops it from applying or updating anything further. The learned pattern and the pinned rule both stay on file, untouched.
- The assistant only learns and adjusts while `.assistant/memory.json` exists. Deleting the `.assistant/` folder turns it off the same way, and erases the learned pattern and the pinned rule along with it.
