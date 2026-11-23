# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-11-23

### Added

- Loadout scan: hold the laser pointer on a teammate and their weapons with overclocks, their grenade and their
  perks float around them in their class colour, tied to them by thin lines. It starts after the pointer rests
  on the dwarf for a moment, follows the dwarf, dims when the pointer slips off and folds back into the dwarf
  when you look away. It runs only while the laser pointer is out.

## [0.3.0] - 2026-11-23

### Fixed

- B did nothing in missions for players who are not the host. The game gives each player a new player controller
  on the way from the Space Rig into a mission, and a client gets it from the host a moment after the level
  starts; the mod kept listening to the old one. It now moves to the new controller when it arrives (no new
  timer).

## [0.2.0] - 2026-11-23

### Added

- Every player's build and perks reach every client when the host runs this version: each player's mod sends its
  own build to the host, which shares it with everyone (`DB_BuildShare_v2`). Works in one lobby with 0.1.0 and
  with players without the mod.

### Changed

- Perks the game does not share show as "Not available" instead of an empty row.
- A build is sent when it changes (the game's own events), not on a timer, and is worked out again only when the
  loadout or perks in the save changed.
- The team window works out a column and the roster strip again only when what they show changed.
- No background timers: the mod looks for the class selection screen only for a short while after the level starts,
  a class selection starts or a game window opens; the overlay refreshes itself only while it is on screen; the
  host keeps the 0.1.0 perk table up only while a player without this version is in the lobby. The only timer left
  runs once a second while the Dwarf Builds window is open.

### Fixed

- Clients saw empty perk rows for other players and often only part of the host's upgrades
  ([#1](https://github.com/byrodi/dwarf-builds-drg/issues/1)).
- TAKE BUILD cleared the slot's overclock or upgrade when the code named one this game version does not have. It
  now keeps the slot's own and says so; the build shows UNKNOWN OVERCLOCK.

Thanks to [Elytras](https://github.com/Elytras) for the report, the analysis and the relay design, which this
version takes from their rewrite of the mod.

## [0.1.0] - 2026-11-22

### Added

- The Dwarf Builds window (B): one column per player with weapons, upgrade tiers, overclocks, equipment and
  perks, with tooltips in the game's style.
- Your team's builds on the class selection screen, next to your own.
- Build codes (DB1): COPY CODE under any player, PASTE FROM CLIPBOARD on the BUILD CODE tab with a preview.
- TAKE BUILD: saves a build into one of your loadout slots, using only what you own.
- BROWSE, PUBLISH MY BUILD and OPEN IN BROWSER for the Dwarf Builds website.
- Lobby-size mods: a roster strip, class filters and pages of 4 for more than 4 players.
- Mod Hub page to change the key that opens the window.
- Works on the release game and on the experimental branch.

[unreleased]: https://github.com/byrodi/dwarf-builds-drg/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/byrodi/dwarf-builds-drg/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/byrodi/dwarf-builds-drg/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/byrodi/dwarf-builds-drg/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/byrodi/dwarf-builds-drg/releases/tag/v0.1.0
