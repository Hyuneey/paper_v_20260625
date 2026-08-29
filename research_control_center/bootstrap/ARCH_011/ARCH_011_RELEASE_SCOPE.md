# ARCH-011 Release Scope

## Public thesis release

- source and schemas/contracts;
- public configs, tests, and synthetic fixtures;
- RCC architecture/claim/governance documents;
- sanitized example artifacts and public checksums;
- dependency lock, environment manifest, installation and staged smoke instructions;
- data acquisition/provenance instructions and license/terms notices;
- explicit statement that result integrity is not scientific validation.

## Exclude

- raw HAI or other restricted payloads;
- sealed labels/test2 and private paths;
- credentials, `.env` custody bindings, tokens, or provider secrets;
- private numeric/model/threshold payloads and restricted predictions;
- raw provider responses when custody prohibits release.

## Checkpoint strategy

ARCH-011 does not push. After user decisions and one reviewed privacy/cleanliness/stale-branch check, a single RCC branch checkpoint push is reasonable. It must not include private assets or imply scientific-authority mutation.
