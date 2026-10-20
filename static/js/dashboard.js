/* Inventory workspace: filters, pagination and bulk selection. */
(function () {
    'use strict';

    const state = {
        user: '',
        search: '',
        sort: 'timestamp',
        order: 'desc',
        page: '1',
    };

    const $ = (id) => document.getElementById(id);

    function readStateFromUrl() {
        const params = new URLSearchParams(window.location.search);
        state.user = params.get('user') || '';
        state.search = params.get('search') || '';
        state.sort = params.get('sort') || 'timestamp';
        state.order = params.get('order') || 'desc';
        state.page = params.get('page') || '1';
    }

    function selectedItems() {
        return document.querySelectorAll('.kit-checkbox:checked');
    }

    function syncSelection() {
        const all = document.querySelectorAll('.kit-checkbox');
        const checked = selectedItems();
        const count = checked.length;

        const stickyCount = $('sticky-selected-count');
        const regularCount = $('selected-count');
        if (stickyCount) stickyCount.textContent = count;
        if (regularCount) regularCount.textContent = count;

        const stickyBar = $('sticky-bulk-actions-bar');
        const regularBar = $('bulk-actions-bar');
        [stickyBar, regularBar].forEach((bar) => {
            if (bar) bar.style.display = count > 0 ? 'flex' : 'none';
        });

        const selectAll = $('select-all');
        if (selectAll) {
            selectAll.checked = count > 0 && count === all.length;
            selectAll.indeterminate = count > 0 && count < all.length;
        }
    }

    function bindRowCheckboxes() {
        document.querySelectorAll('.kit-checkbox').forEach((box) => {
            box.addEventListener('change', syncSelection);
        });
        const selectAll = $('select-all');
        if (selectAll) {
            selectAll.addEventListener('change', function () {
                document.querySelectorAll('.kit-checkbox').forEach((box) => {
                    box.checked = selectAll.checked;
                });
                syncSelection();
            });
        }
    }

    function showLoading() {
        let overlay = $('loading-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'loading-overlay';
            overlay.setAttribute('role', 'status');
            overlay.setAttribute('aria-live', 'polite');
            overlay.innerHTML = '<div class="loading-spinner">Loading inventory…</div>';
            document.body.appendChild(overlay);
        }
        overlay.style.display = 'flex';
    }

    function hideLoading() {
        const overlay = $('loading-overlay');
        if (overlay) overlay.style.display = 'none';
    }

    function renderStockBars(rows) {
        const container = $('stockBars');
        if (!container || !Array.isArray(rows) || !rows.length) return;

        const peak = rows.reduce(
            (max, row) => Math.max(max, Number(row.total_quantity) || 0),
            0
        );
        const fragment = document.createDocumentFragment();

        rows.forEach((row) => {
            const quantity = Number(row.total_quantity) || 0;
            const users = Number(row.user_count) || 0;

            const item = document.createElement('div');
            item.className = 'stock-bar';

            const head = document.createElement('div');
            head.className = 'stock-bar-head';

            const name = document.createElement('span');
            name.className = 'stock-bar-name';
            name.textContent = row.kit_type || 'Unassigned';

            const value = document.createElement('span');
            value.className = 'stock-bar-value';
            value.textContent = quantity.toLocaleString();
            const meta = document.createElement('small');
            meta.textContent = ` units · ${users} user${users === 1 ? '' : 's'}`;
            value.append(meta);

            head.append(name, value);

            const track = document.createElement('div');
            track.className = 'stock-bar-track';
            const fill = document.createElement('div');
            fill.className = 'stock-bar-fill';
            fill.style.width = `${peak ? Math.round((quantity / peak) * 100) : 0}%`;
            track.appendChild(fill);

            item.append(head, track);
            fragment.appendChild(item);
        });

        container.replaceChildren(fragment);
    }

    function updateTable(html) {
        const container = $('table-container');
        if (container && html) {
            container.innerHTML = html;
            bindRowCheckboxes();
            syncSelection();
        }
    }

    function updatePagination(html) {
        const container = $('pagination-container');
        if (container && typeof html === 'string') {
            container.innerHTML = html;
        }
    }

    function queryString() {
        return new URLSearchParams(state).toString();
    }

    function fetchData(pushHistory) {
        const url = `${window.location.pathname}?${queryString()}`;
        showLoading();
        if (pushHistory) {
            window.history.pushState({ path: url }, '', url);
        }

        fetch(url, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                Accept: 'application/json',
            },
        })
            .then((response) => {
                if (!response.ok) throw new Error('Request failed');
                return response.json();
            })
            .then((data) => {
                if (!data.success) {
                    window.location.href = url;
                    return;
                }
                updateTable(data.table_html);
                updatePagination(data.pagination_html);
                renderStockBars(data.kit_stats);
            })
            .catch(() => {
                window.location.href = url;
            })
            .finally(hideLoading);
    }

    function applyFilters(event) {
        if (event) event.preventDefault();
        const form = $('filter-form');
        if (!form) return;
        const data = new FormData(form);
        state.user = data.get('user') || '';
        state.search = data.get('search') || '';
        state.sort = data.get('sort') || 'timestamp';
        state.order = data.get('order') || 'desc';
        state.page = '1';
        fetchData(true);
    }

    function syncControls() {
        const form = $('filter-form');
        if (!form) return;
        ['user', 'search', 'sort', 'order'].forEach((name) => {
            const control = form.elements.namedItem(name);
            if (control) {
                control.value = state[name] || (name === 'sort' ? 'timestamp' : name === 'order' ? 'desc' : '');
            }
        });
    }

    readStateFromUrl();

    document.addEventListener('DOMContentLoaded', function () {
        syncSelection();
        bindRowCheckboxes();

        const filterForm = $('filter-form');
        if (filterForm) filterForm.addEventListener('submit', applyFilters);

        const bulkForm = $('bulk-delete-form');
        if (bulkForm) {
            bulkForm.addEventListener('submit', function (event) {
                const count = selectedItems().length;
                if (!count) {
                    event.preventDefault();
                    window.alert('Select at least one stock item first.');
                    return;
                }
                if (!window.confirm(`Delete ${count} selected stock item(s)? This cannot be undone.`)) {
                    event.preventDefault();
                }
            });
        }

        const pagination = $('pagination-container');
        if (pagination) {
            pagination.addEventListener('click', function (event) {
                const link = event.target.closest('.page-link');
                if (!link || !link.dataset.page) return;
                event.preventDefault();
                state.page = link.dataset.page;
                fetchData(true);
            });
        }

        window.addEventListener('popstate', function (event) {
            const url = event.state && event.state.path
                ? new URL(event.state.path, window.location.origin)
                : new URL(window.location.href);
            const params = new URLSearchParams(url.search);
            state.user = params.get('user') || '';
            state.search = params.get('search') || '';
            state.sort = params.get('sort') || 'timestamp';
            state.order = params.get('order') || 'desc';
            state.page = params.get('page') || '1';
            syncControls();
            fetchData(false);
        });
    });
})();
