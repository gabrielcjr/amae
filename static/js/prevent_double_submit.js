(function () {
    document.addEventListener('submit', function (event) {
        var form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (form.dataset.submitted === 'true') {
            event.preventDefault();
            return;
        }
        form.dataset.submitted = 'true';
        var buttons = form.querySelectorAll('input[type=submit], button[type=submit]');
        buttons.forEach(function (btn) {
            btn.disabled = true;
            btn.style.opacity = '0.6';
            btn.style.cursor = 'wait';
        });
    }, true);

    window.addEventListener('pageshow', function (event) {
        if (!event.persisted) return;
        document.querySelectorAll('form[data-submitted="true"]').forEach(function (form) {
            form.dataset.submitted = '';
            form.querySelectorAll('input[type=submit], button[type=submit]').forEach(function (btn) {
                btn.disabled = false;
                btn.style.opacity = '';
                btn.style.cursor = '';
            });
        });
    });
})();
