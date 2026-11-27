# Blind draw record: gas–electric seam test (protocol Section 2C, Amendment 1)

Drawn 27 November 2026, after drand round 6679406 was published.

## Seed source
- drand League of Entropy, default chain `8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce`
- Round 6679406 (21:00:00 UTC, 27 Nov 2026). Amendment tag `blind-test-amend-1` (commit a43b8b6, committed 14:10 CT) precedes it.
- randomness: `e4aa2bb1e615096bd8f1c072612fd37870d819665ffe5c387763db119aea06b5`
- Identical on two relays (api.drand.sh, drand.cloudflare.com). SHA-256(signature) equals randomness. The BLS signature verifies against the chain public key (py_ecc G2Basic).
- The commit message and release title of a43b8b6 read "6679486", which is a typo. AMENDMENT_1.md governs and names round 6679406.

## Draw
- Script `src/blind_draw.py`, SHA-256 2860b7b48107c9980066834f06d55db756a64dc4f19215f2076ce6e5f8712dff, unchanged from the freeze. Run under Python with numpy 2.5.3.
- Derived seed: 184922378773829663
- Output: 20 scenarios (16 strain, 4 control), 200 inputs, 200 unique codes

## Sealed answer key
- `SEALED_answer_key.json`, SHA-256 **1fbe54c83b8bae0eaeeff535a89aac64d3368c93868aa08217473c53c70124a1**
- Held by the input builder. It is not published until the readings are returned.
