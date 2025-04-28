document.addEventListener("DOMContentLoaded", function() {
  const providerSelect = document.getElementById('provider');
  const gmailOptions = document.getElementById('gmail-options');
  const outlookOptions = document.getElementById('outlook-options');

  function toggleOptions() {
      if (providerSelect.value === 'gmail') {
          gmailOptions.style.display = 'block';
          outlookOptions.style.display = 'none';
      } else if (providerSelect.value === 'outlook') {
          gmailOptions.style.display = 'none';
          outlookOptions.style.display = 'block';
      } else {
          gmailOptions.style.display = 'none';
          outlookOptions.style.display = 'none';
      }
  }

  providerSelect.addEventListener('change', toggleOptions);
  toggleOptions(); // Initialize correctly on page load
});
