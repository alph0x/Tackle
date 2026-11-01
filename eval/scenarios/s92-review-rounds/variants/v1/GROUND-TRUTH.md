# Review development case

The previous review recorded an empty-input crash, a dismissed rename and optional type hints. The correction prevents the crash but changes the loader's return value to a list; the parcel report consumer still indexes the return as a mapping. The unchanged fixture has no new review and is invalid. Both diagnostic phases write run ledgers only when executed.
