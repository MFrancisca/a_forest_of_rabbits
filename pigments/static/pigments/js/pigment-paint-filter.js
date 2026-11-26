/*
 * Turns the "Paint" filter on the admin Pigments listing into a searchable
 * Select2 dropdown (see PaintFilterSelect in pigments/wagtail_hooks.py).
 */
(function () {
  'use strict';

  function enhance(select) {
    if (select.dataset.select2Ready || !window.jQuery || !window.jQuery.fn.select2) {
      return; // Without Select2 (or jQuery) the plain <select> still works.
    }
    select.dataset.select2Ready = 'true';
    var $select = window.jQuery(select);

    $select.select2({
      width: '100%',
      allowClear: true,
      placeholder: 'Any paint',
      // The list opens on <body> (Select2's default): Wagtail's filter panel
      // scrolls its contents, which would clip it. See the clickaway handler below.
    });

    // Select2 reports changes as jQuery events. Wagtail's filter form listens
    // for a native "change" to refresh the listing, so send one.
    $select.on('select2:select select2:unselect', function () {
      select.dispatchEvent(new Event('change', { bubbles: true }));
    });

    // Select2 4.0 can't focus its search box under jQuery 3.6 (the version
    // Wagtail ships), so typing right after opening would go nowhere.
    $select.on('select2:open', function () {
      var field = document.querySelector('.select2-container--open .select2-search__field');
      if (field) field.focus();
    });
  }

  function init() {
    document.querySelectorAll('select[data-pigment-paint-filter]').forEach(enhance);
  }

  // After the listing refreshes, redraw Select2 so it shows the <select>'s
  // current value (a jQuery-only event, so it doesn't reach the form and loop).
  function resync() {
    if (!window.jQuery) return;
    document.querySelectorAll('select[data-pigment-paint-filter]').forEach(function (select) {
      if (select.dataset.select2Ready) window.jQuery(select).trigger('change.select2');
    });
  }

  function start() {
    init();
    // Removing an active-filter pill re-renders the filter panel with a fresh
    // <select>; enhance it when it arrives.
    var pending = false;
    new MutationObserver(function () {
      if (pending) return;
      pending = true;
      window.requestAnimationFrame(function () {
        pending = false;
        init();
      });
    }).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start);
  } else {
    start();
  }
  document.addEventListener('w-swap:success', resync);

  // A click in Select2's list (on <body>, outside Wagtail's filter panel) would
  // count as a click away and close the panel. Wagtail lets this be cancelled.
  document.addEventListener('w-dropdown:clickaway', function (event) {
    var target = event.detail && event.detail.target;
    if (target && target.closest && target.closest('.select2-container, .select2-dropdown')) {
      event.preventDefault();
    }
  });
})();
