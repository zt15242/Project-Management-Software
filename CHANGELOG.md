# Changelog

## v1.0.3 - 2026-05-27

- Verified remote version detection by bumping the release version.
- Improved reliability for reading GitHub remote `backend/VERSION`.

## v1.0.2 - 2026-05-27

- Added the sidebar version panel for system administrators.
- Added backend version/status APIs and Docker restart support.
- Updated deployment scripts to protect local `.env` files during Git updates.
- Rebuild backend and frontend services when `backend/VERSION` changes.
- Disabled MongoDB backup during migration/deployment scripts.
- Fixed Docker dependency installation and pydantic/zhipuai compatibility.
