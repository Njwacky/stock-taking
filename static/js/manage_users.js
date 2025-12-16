// Manage users functionality
function updateUserSelectionCount() {
  const checks = [...document.querySelectorAll('.row-check')];
  const count = checks.filter(c => c.checked).length;
  const selCountElement = document.getElementById('sel_count');
  if (selCountElement) {
    selCountElement.textContent = count;
  }
}

document.addEventListener('change', function(e){
  if(e.target.classList && e.target.classList.contains('row-check')){
    updateUserSelectionCount();
  }
  // Also handle select all checkbox
  if(e.target.id === 'select_all'){
    const allChecked = e.target.checked;
    document.querySelectorAll('.row-check').forEach(cb => cb.checked = allChecked);
    updateUserSelectionCount();
  }
});

document.addEventListener('DOMContentLoaded', function() {
  updateUserSelectionCount();
});
