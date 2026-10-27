# Decisions

The user's rulings on scope, style and trade-offs, newest last. Read before asking the user anything; if a later
decision replaces one, mark the old one "replaced by D<n>" instead of deleting it. Binding term spellings live in
`glossary.md`; this file holds the why.

Rows D1-D4 were recorded before this file existed (from the old CLAUDE.md/glossary); options and reasons not kept.

| # | Date | Question | Options offered | Decision and reason |
|---|---|---|---|---|
| D1 | 2026-10-08 | Honorifics and name order | keep (-san), drop; JP or Western order | Keep honorifics, JP name order (Mita-san, Joukouji Nagomu); faithful translation. |
| D2 | 2026-10-08 | Debug menus and sound test | translate, leave JP | Leave Japanese. |
| D3 | 2026-10-08 | Choice length | wrap, one line | One line, <= 45 chars. |
| D4 | 2026-10-10 | Patch format | xdelta, BPS | BPS (build/zero_one_sp_en.bps), build verifies re-apply. |
| D5 | 2026-10-27 | Repo layout | keep scripts/ package, template layout | fan-translation-template layout (tools/, script/, AGENTS.md, docs/re/). |
| D6 | 2026-10-27 | L-menu titles too long for the 64 px list (issue #1) | initial family name, given name only, family name only | Initial the family name ('J. Nobuhiko', 'K. Tsutomu'): keeps JP order; descriptions keep full names. |
