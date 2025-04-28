function showLoadingSpinner() {
    var input = document.querySelector('input[name="url"]');
    var button = document.querySelector('button');
    if (input.value.trim() !== '') {
        button.style.display = 'none';
        var spinner = document.createElement('div');
        spinner.className = 'spinner';
        button.parentNode.appendChild(spinner);
    }
}
document
.getElementById('load-xx-btn')
.addEventListener('click', () => {
  fetch('/xx')
    .then(r => r.text())
    .then(html => {
      document.getElementById('xx-container').innerHTML = html;
    })
    .catch(console.error);
});
document.getElementById("load-xx-btn").onclick = function() {
  // Navigate to the blueprint’s page
  location = "{{ url_for('xx_bp.index') }}";
};