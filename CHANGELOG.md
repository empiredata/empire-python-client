## 0.3.3

Documentation:

  - Changed the help text

## 0.3.2

Fix:

  - `empire.walkthrough` now demonstrates materialized views. (It
  wasn't merged into 0.3.1)

Packaging:

  - Improved packaging for PyPi

## 0.3.1

Breaking changes:

  - PyPi package is now called `empire-client`. The module is still
  called `empire`.

Features:

  - `empire.walkthrough` now demonstrates materialized views.

## 0.3

Breaking changes:

  - Materialized views are now manipulated through `materialize_view`,
  `drop_view`, and `view_ready`

  - Optional string parameter `enduser`, when creating an Empire
  instance. This parameter is mandatory for performing materialized
  view operations.

Dependencies:

  - New dependency on `[python-dateutil](https://labix.org/python-dateutil)`

Features:

  - `empire.view_materialized_at("viewname")` returns a `datetime`
  object with the time the view was last materialized.

## 0.2

Features:

  - `query` returns Python dicts

License:

  - Changed to Apache License, Version 2.0

## 0.1

Features:

  - `connect`
  - `describe`
  - `query`
  - `insert`
  - `create_view`, `drop_view`, `refresh_view`
  - `walkthrough`
