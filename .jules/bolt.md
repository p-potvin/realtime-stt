# Bolt Learnings: String Combination Optimization
- Replace multiple iterations of `random.choice` concatenated together with cryptographic generators for identifiers.
- Example: Iterative string concatenations like `"".join(random.choices(CHARS, k=4))` take ~0.16s for 100,000 executions, whereas `secrets.token_hex(2)` takes only ~0.14s and is significantly more concise without caching problems or dependencies.
