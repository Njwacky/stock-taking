# Merge / logic review — 23 Oct 2026

## 1. Why the merge broke the app

PR #13 (`arena/3d056e59-stock-taking`) was built on top of the old PR #12
commit and introduced a **second model named `Workspace`**:

| Location | Purpose | Fields |
|---|---|---|
| `stockT/models.py:83` | Multi-tenant workspace (used by `Kit`, `KitType`, `StockUsage`, `SessionTracker`, `WorkspaceMember`) | `name`, `slug`, `created_by`, `is_active`, `memberships` |
| `stockT/models.py:560` (before this fix) | Private inventory ("My Workspaces") | `owner`, `name`, `description`, `created_at` |

Commit `69b47a8` ("Merge branch 'main' into …") merged `main` into the PR #13
branch. Git saw the two classes as separate additions at different offsets and
**auto-merged them without a conflict**. Python only keeps the last binding of a
name, so Django's app registry ended up with the private `Workspace` and every
foreign key to the multi-tenant one became invalid.

Result on `main` before this fix:

```text
$ python manage.py check
RuntimeWarning: Model 'stockT.workspace' was already registered.

ERRORS:
stockT.Kit.workspace: (fields.E300) Field defines a relation with model 'Workspace',
    which is either not installed, or is abstract.
stockT.KitType.workspace: (fields.E300) ...
stockT.SessionTracker.workspace: (fields.E300) ...
stockT.StockUsage.workspace: (fields.E300) ...
stockT.WorkspaceMember.workspace: (fields.E300) ...
```

`check`, `migrate`, `runserver` and the tests all aborted, so the application
could not start at all after the merge.

### Migration graph was also corrupted

PR #13 added migrations that duplicated numbers already used by `main`:

```text
stockT/migrations/0002_seed_kit_types.py                 (main)
stockT/migrations/0002_workspace_workspaceproduct.py     (PR #13)
stockT/migrations/0003_workspacemember_alt...py         (main)
stockT/migrations/0003_workspaceproduct_version.py       (PR #13)
```

Two `0002` leaves and two `0003` leaves mean Django can never linearise the
graph ("Conflicting migrations detected; multiple leaf nodes").

### Other merge regressions

* `stockT/templates/base.html` was a hybrid of the **old top navbar**
  (`mobileMenuBtn`, `navLinks`, `fas` icons) and the **new sidebar shell**. The
  old layer had been deleted on `main` in PR #11, so the merge brought it back –
  two competing mobile navigations, missing `<body class="app-body">`, missing
  skip link and theme bootstrap.
* `register()` lost the workspace-provisioning block from `main`
  (`ensure_user_workspace`). With two authentication backends configured, the
  remaining `login(request, user)` also raised
  `ValueError: You have multiple authentication backends configured…`, so
  registration returned HTTP 500 and created users without a workspace.
* `LOGIN_REDIRECT_URL` pointed at `/workspaces/` while registration and every
  other flow ended at `/`.

## 2. What was changed

1. **Renamed the private feature** (kept the feature, removed the collision):
   * `Workspace` → `Inventory`
   * `WorkspaceProduct` → `InventoryProduct`
   * `owner.related_name` → `inventories`
   * FK field `workspace` → `inventory`
   * unique constraint → `unique_inventory_product_sku`
   * Updated `stockT/workspaces.py`, `stockT/tests/test_workspaces.py`.
   * The multi-tenant `Workspace` model is now the only `Workspace`.
2. **Replaced the conflicting migrations** with
   `stockT/migrations/0006_inventory_inventoryproduct.py`, which depends on the
   real `0005` leaf and creates the two renamed tables with the `version` field
   included.
3. **Restored the pre-merge `base.html`** (single sidebar navigation,
   `app-body`, skip link, dark-theme bootstrap, Inter font) and re-added:
   * the PWA icon set from PR #12,
   * the “My Workspaces” sidebar entry,
   * an SVG refresh icon in Add Stock (the only remaining Font Awesome use in
     templates).
4. **Restored registration provisioning** (`ensure_user_workspace` inside a
   transaction) and the explicit auth backend on `login()`. Login/registration
   now redirect to `/` consistently.
5. **Closed a privilege-escalation hole found during the audit**: role-admin
   (non-superuser) accounts and global managers could edit, deactivate or delete
   a **superuser** account through `edit-user`, `delete-user` and the bulk
   deactivate action. Administrator accounts can now only be edited/deleted/
   deactivated by a superuser. Regression tests added in
   `tests/unit/test_user_management.py`.

## 3. Verification

```text
python manage.py check                 # System check identified no issues
python manage.py makemigrations --check # No changes detected
python manage.py migrate               # applies 0001 → 0006 cleanly on a fresh DB
pytest tests/unit stockT/tests         # 249 passed
```

## 4. Things that are working as designed (not bugs)

* **Stock rows are not merged.** Adding VHB tape twice for the same person
  creates two `Kit` rows (e.g. quantities 5 and 3), and distribution does the
  same. This preserves per-batch condition/location/expiry information, and the
  dashboard statistics sum by kit type. If you expected one row with quantity
  8, that is a product decision (auto-merge identical active rows) rather than a
  crash — say the word and it can be added.
* **Usage approval is correct now.** It deducts FIFO across the user's active
  kits, refuses to over-draw (request stays pending), and ignores a second
  approval of an already-completed request.
* **Deployment caveat:** if a database ever applied the old
  `0002_workspace_workspaceproduct` / `0003_workspaceproduct_version`
  migrations, the orphan tables (`stockT_workspace`, `stockT_workspaceproduct`)
  are no longer mapped to models. The new `stockT_inventory*` tables start
  empty; copy the rows across manually if that database had real data.
