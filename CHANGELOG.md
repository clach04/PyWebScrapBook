# Changelog
* This project generally follows [semantic versioning](https://semver.org/). For a version `x.y.z`, `x` means a major (backward incompatible) change, `y` means a minor (backward compatible) change, and `z` means a patch (bug fix). Few versions may not strictly follow this rule due to historical reasons, though.
* Versions before 1.0 are in initial development. APIs are not stable for these versions, even a `y` version can involve a breaking change, and only partial notable changes are summarized in this document. See full commit history in the source repository for details.
* Client requirement in this document refers to the version of [`WebScrapBook`](https://github.com/danny0838/webscrapbook) browser extension.

## [1.1.0] - 2021-12-10
* Dropped support of config `app.base`.
* Fixed an issue that the mimetype of `.js` becomes `application/x-javascript` in some environment.
* Fixed several errors of unit tests.

## [1.0.0] - 2021-12-07
* Bumped version to 1.0.*.

## [0.48.0] - 2021-11-13
* Updated converted CSS for `wsb convert migrate`.

## [0.47.0] - 2021-11-09
* Load item icons lazily for generated static site files.

## [0.46.0] - 2021-11-04
* Expose `backup_dir` config to the client if it's web accessible.
* `backup` and `unbackup` actions now return the target directory name.

## [0.45.0] - 2021-10-25
* Added support of HTZ, MAFF, and single HTML formats for the `migrate` converter.

## [0.44.2] - 2021-09-21
* Fixed a compatibility issue for saved tree data with old browsers not supporting ES2019.

## [0.44.1] - 2021-05-16
* Fulltext cache no more include text content in `<textarea>` or `<template>` tags.
* Fixed potential bad handling of `<frame>` tags for converters.

## [0.44.0] - 2021-05-08
* Added support of `single_file` format for `items` converter.
* Added support of more common MIME types.
* Fixed translation of certain common MIME types to a fixed file extension.
* Fixed several get_meta_refresh errors in Python 3.6.
* Fixed several test errors.

## [0.43.0] - 2021-05-04
* Added support of custom MIME types mapping using `~/.config/wsb/mime.types`.
* Added `wsb help mimetypes` for documentation about customizing MIME types mapping.
* Added support of some common MIME types.
* Reworked handling of some HTTP headers and HTML attributes to conform with the spec better.
* Fixed an issue that meta charset be ignored when parsing a meta refresh.
* `items` converter now preserves file metadata for the generated HTZ or MAFF files.
* Fixed incorrect icon path after a conversion of the `items` converter.
* `wsb2sb` converter no more changes the linefeed format for output files.
* Fixed potential bad handling of XHTML files for the `wsb2sb` converter.
* Fixed incorrect rewriting of content in special tags like `<template>`, `<xmp>`, etc., for `migrate` and `items` converters.

## [0.42.0] - 2021-05-01
* Added support of migrating several older WebScrapBook data for the `migrate` converter. The behavior can be switched with `--convert-*` options.
* `migrate` converter no more changes the linefeed format for output files.
* Adjusted log message format of several utilities.
* Fixed missing support of hash in source URL for the generated static index file.
* Fixed a potential error when converting a legacy ScrapBook ID with the `migrate` converter.
* Fixed an issue of generating extra loader elements if one exists for the `migrate` converter.
* Fixed potential bad handling of XHTML files for the `migrate` converter.

## [0.41.0] - 2021-04-27
* Hash part of source URL is now considered when viewing an item in the generated map file.
* Added support of `limit:` command for search page.
* Added `items` converter.

## [0.40.0] - 2021-04-17
* `server.browse` now defaults to `false`.

## [0.39.0] - 2021-04-12
* Fixed a security issue that may allow the user to access any directory on Windows.
* Fixed an issue that `file2wsb` converter does not handle a page named `index.html` with a support folder.
* No more generate a title from ID if title is empty for the checker and some converters.
* `file2wsb` converter now generates an item for every normal file.
* `file2wsb` converter now preserves the original filename by default, with an added `--no-preserve-filename` option to tweak the behavior.

## [0.38.0] - 2021-04-11
* Fixed an issue of crash for `check` if a page has an empty title.
* Renamed converter `migrate0` to `migrate`.
* Added `app.locale` config to determine the locale of the APP theme.
* Added support of downloading a folder or files and folders under a folder for the web interface.
* Added `--data-folder-suffixes` and `--ignore-*-meta` options for `file2wsb` converter.

## [0.36.0] - 2021-04-01
* Fixed an issue that auto backup may not include a deleted file.
* Added support of note for a backup.
* Added support for `unbackup` action.

## [0.35.2] - 2021-03-30
* Fixed an issue that backup does not work for `sb2wsb` converter if input path is not absolute.

## [0.35.0] - 2021-03-27
* Fixed an issue that fulltext cache does not work for iframes with srcdoc attribute. (Rebuild the fulltext cache to correct existing caches.)
* Added support of page conversion for `sb2wsb` and `wsb2sb` converters.
* Added `migrate0` converter.

## [0.32.0] - 2020-11-05
* Added `file2wsb` and `wsb2file` converters.

## [0.30.0] - 2020-10-29
* ID for item added by `wsb check --resolve-unindexed-files` is now always in standard format.

## [0.29.0] - 2020-10-27
* Added support for `backup` action.
* Fixed potential ID overwriting for item added by `wsb check --resolve-unindexed-files`.

## [0.28.0] - 2020-10-26
* Fixed a conversion error between "site" and legacy "combine" item type.
* Fixed a conversion error that wsb2sb converter converts an item other than "" type with marked property to "marked" type.
* Added support to convert data file between "postit" and legacy "note" item type.
* Added `app.backup_dir` config.

## [0.27.2] - 2020-10-26
* Fixed bad ID for item added by `wsb check --resolve-unindexed-files`.

## [0.26.0] - 2020-10-14
* Dropped support for `recursive` parameter of `list` server action.
* Added support of top-level None value for *.js tree files.

## [0.25.0] - 2020-10-12
* Added `export` and `import` command.
* Moved config `browser.index` to `app.index`.

## [0.24.0] - 2020-10-09
* Added `convert wsb2sb` command.

## [0.23.0] - 2020-10-05
* Bumped client requirement to >= 0.79.
* Adjusted locking mechanism:
  * A lock is now created under `.wsb/locks` instead of `.wsb/server/locks`.
  * A lock is now created as a file instead of a folder.
  * A lock is now created with an ID, and can be extended using the same ID. Releasing a lock now requires its ID.
  * The server now responses 503 rather than 500 for a timeout of `lock` server action.
* Added `cache`, `check`, and `convert` commands.

## [0.22.0] - 2020-09-22
* Removed shebang for script files.

## [0.21.0] - 2020-09-16
* A lock is now created using a hashed filename instead of a plain filename.

## [0.20.0] - 2020-09-13
* Added content security policy restriction for served web pages. They can no longer send AJAX requests and form actions to prevent a potential attack. A config `app.content_security_policy` is added to change the behavior.

## [0.18.1] - 2020-09-08
* Installation requirement is now declared as Python >= 3.6. Note that version compatibility is not thoroughly checked for prior versions, and some functionalities are known to break in Python < 3.7 for some versions despite marked as installable.
* Response of a server`config` action now exposes a new `WSB_EXTENSION_MIN_VERSION` value, which informs the client to apply self version checking.

## [0.17.0] - 2020-08-27
* Bumped client requirement to >= 0.75.6.
* Bumped requirement of `werkzeug` to >= 1.0.0.
* Removed `cryptography` from installation requirement. It is now an optional requirement (for ad hoc SSL key generating).
* Fixed a bug for zip editing through server actions in Python < 3.7.
* Response 404 rather than 400 for `list` server action when the directory is not found.
* Added unit tests.

## [0.15.0] - 2020-04-12
* Tokens are now created under `.wsb/server/tokens` instead of `.wsb/server/token`.

## [0.14.0] - 2020-04-01
* Switched backend server framework to `Flask` from `Bottle`.
* Added support for `app.allow_x_*` configs to prevent issues when serving behind a reverse proxy.
* Dropped support for `server.ssl_pw` config.

## [0.11.0] - 2020-01-14
* Added support of zip editing through server actions.

## [0.8.0] - 2019-09-01
* Added support for `book.*.no_tree` config.

## [0.6.0] - 2019-04-14
* Added `lock` and `unlock` actions.
* Merged `upload` action into `save`.

## [0.4.0] - 2019-04-06
* Added `wsbview` CLI executable.

## [0.1.5] - 2019-03-14
* First public release.
