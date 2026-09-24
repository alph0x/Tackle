# Mail assistant

The mail assistant checks `mailbox/autosort.json` before it sorts new mail.

- Setting `"auto_sort"` to `"off"` stops it from archiving or updating rules any further. Every learned rule and every rule you pinned by hand stays on file.
- With no `autosort.json`, the assistant leaves new mail unsorted. Deleting the file stops the sorting the same way, and erases every rule, learned or pinned, along with it.
