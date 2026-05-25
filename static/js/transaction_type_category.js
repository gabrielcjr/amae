(function () {
    function filterCategories() {
        var typeSelect = document.getElementById('id_type');
        var categorySelect = document.getElementById('id_category');
        if (!typeSelect || !categorySelect) return;

        var selectedType = typeSelect.value;
        var currentValue = categorySelect.value;
        var currentStillValid = false;

        Array.prototype.forEach.call(categorySelect.options, function (option) {
            var optionType = option.dataset.type;
            var visible = !optionType || !selectedType || optionType === selectedType;
            option.hidden = !visible;
            option.disabled = !visible;
            if (option.value === currentValue && visible) {
                currentStillValid = true;
            }
        });

        if (!currentStillValid) {
            categorySelect.value = '';
        }
    }

    document.addEventListener('DOMContentLoaded', function () {
        var typeSelect = document.getElementById('id_type');
        if (!typeSelect) return;
        typeSelect.addEventListener('change', filterCategories);
        filterCategories();
    });
})();
