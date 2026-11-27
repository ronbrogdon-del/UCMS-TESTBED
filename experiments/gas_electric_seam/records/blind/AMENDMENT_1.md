# Amendment 1 to Section 2C: seed source (27 November 2026)

The NIST Randomness Beacon 2.0 published no pulse at 18:00:00 UTC on 27 November 2026. The pulse URL returns 404, and the latest pulse on the beacon is dated 10 September 2026. No draw was made from any value.

The seed source is replaced as follows. Nothing else in the protocol, freeze, engine, rule, alarms, pool, draw script or pass criteria changes.

- **Source:** drand League of Entropy, default chain, chain hash `8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce` (30-second period, genesis 1595431050).
- **Pulse:** round 6679406, scheduled for 21:00:00 UTC (15:00 CT) on 27 November 2026 (`https://api.drand.sh/8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce/public/6679406`).
- **Value:** the round's 64-hex-character `randomness` field is passed unchanged to `src/blind_draw.py` in place of `outputValue`. The seed is the first 8 bytes of SHA-256("SCFL-seam-blind-1|" + randomness, uppercased by the script).
- **Validity:** used only if this amendment is tagged `blind-test-amend-1` on GitHub before 21:00:00 UTC on 27 November 2026. Otherwise, the round at 21:00:00 UTC on the first later day on which the tag comes first.
- **Verification:** the round's BLS signature is checked against the chain's public key and must match on at least two independent drand relays.
