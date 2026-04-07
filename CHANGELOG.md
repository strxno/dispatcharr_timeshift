# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.6] - 2026-04-07

### Fixed

- **URL resolver recursion** — After `uninstall_hooks()` cleared module globals, a subsequent `install_hooks()` could save the wrapped `URLResolver.resolve` as the “original,” causing infinite recursion on normal routes (for example `/api/m3u/accounts/`). The patch now follows the same `_is_timeshift_patch` / `_native_func` pattern as the other hooks so the real Django resolver is always recovered.
- **Stats / active streams showing “Anonymous”** — The patched `stream_xc` now calls `stream_ts(request, channel_uuid, user)` with the authenticated user, matching core Dispatcharr so live connections are attributed correctly.
- **Timeshift when catch-up is not the first stream** — `get_live_streams` advertised `tv_archive` from the first stream with catch-up but could still expose the **first priority** stream’s provider id. The advertised `stream_id` now comes from that catch-up stream when present. `timeshift_proxy` also resolves the first ordered stream with `tv_archive` when the URL still matches a non–catch-up source (legacy clients).

### Added

- **Redirect stream profile** — For channels using Dispatcharr’s **Redirect** profile, `player_api.php` now sets **`direct_source`** to the provider URL derived from the **same catch-up stream** used for `stream_id` (M3U default profile + `transform_url`), so direct play and catch-up metadata stay aligned. Proxy profile behavior is unchanged (`direct_source` remains empty).

[1.2.6]: https://github.com/cedric-marcoux/dispatcharr_timeshift/compare/v1.2.5...v1.2.6
