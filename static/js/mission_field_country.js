(function () {
  "use strict";

  function setup() {
    var countryField = document.getElementById("id_country");
    var regionField = document.getElementById("id_region");
    var stateField = document.getElementById("id_state");

    if (!countryField) return;

    // Store original options
    var regionOptions = [];
    var stateOptions = [];

    if (regionField) {
      for (var i = 0; i < regionField.options.length; i++) {
        regionOptions.push({
          value: regionField.options[i].value,
          text: regionField.options[i].text,
        });
      }
    }

    if (stateField) {
      for (var i = 0; i < stateField.options.length; i++) {
        stateOptions.push({
          value: stateField.options[i].value,
          text: stateField.options[i].text,
        });
      }
    }

    function toggle() {
      var isBrasil = countryField.value === "BR";

      if (regionField) {
        regionField.innerHTML = "";
        if (isBrasil) {
          regionOptions.forEach(function (opt) {
            var option = new Option(opt.text, opt.value);
            regionField.add(option);
          });
        } else {
          regionField.add(new Option("---------", ""));
        }
      }

      if (stateField) {
        stateField.innerHTML = "";
        if (isBrasil) {
          stateOptions.forEach(function (opt) {
            var option = new Option(opt.text, opt.value);
            stateField.add(option);
          });
        } else {
          stateField.add(new Option("---------", ""));
        }
      }
    }

    countryField.addEventListener("change", toggle);

    // Run on page load only if NOT Brasil (preserve current selections)
    if (countryField.value !== "BR") {
      toggle();
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", setup);
  } else {
    setup();
  }
})();
