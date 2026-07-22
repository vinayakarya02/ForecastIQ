# Security Policy

## Supported versions
| Version | Supported |
|---------|-----------|
| 1.0.x   | ✅ |

## Reporting a vulnerability
ForecastIQ is a local analytics application with no authentication layer or external network calls, so
its attack surface is small. If you nonetheless discover a security issue:

1. **Do not** open a public issue.
2. Report it privately via [GitHub Security Advisories](https://github.com/vinayakarya02/ForecastIQ/security/advisories/new),
   or by emailing the maintainer.
3. Include a description, reproduction steps, and potential impact.

You can expect an acknowledgement within a few days.

## Handling data
- The app runs against a **local SQLite warehouse**; no data leaves the machine.
- Datasets and the built database are git-ignored and never committed.
- SQL is built with parameterised queries or values drawn from the warehouse's own dimensions (not free
  user text); filter values are quote-escaped before interpolation.
