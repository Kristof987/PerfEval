FLASH_HIDE_ALERTS_SCRIPT = """
<script>
setTimeout(() => {
  const alerts = window.parent.document.querySelectorAll('[data-testid="stAlert"]');
  alerts.forEach(a => { a.style.display = 'none'; });
}, 3500);
</script>
"""
