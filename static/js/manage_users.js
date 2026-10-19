// Keep bulk-selection state, count and action visibility in sync.
function updateUserSelectionCount() {
    const checks = Array.from(document.querySelectorAll('.row-check'));
    const selected = checks.filter(check => check.checked).length;
    const countElement = document.getElementById('sel_count');
    const actionsBar = document.querySelector('.bulk-actions-bar');
    const selectAll = document.getElementById('select_all');

    if (countElement) countElement.textContent = selected;
    if (actionsBar) actionsBar.style.display = selected > 0 ? 'flex' : 'none';
    if (selectAll) {
        selectAll.checked = checks.length > 0 && selected === checks.length;
        selectAll.indeterminate = selected > 0 && selected < checks.length;
    }
}

document.addEventListener('change', function(event) {
    if (event.target.id === 'select_all') {
        document.querySelectorAll('.row-check').forEach(check => {
            check.checked = event.target.checked;
        });
        updateUserSelectionCount();
    } else if (event.target.classList && event.target.classList.contains('row-check')) {
        updateUserSelectionCount();
    }
});

document.addEventListener('DOMContentLoaded', updateUserSelectionCount);
