var qsRegex;
var buttonFilter;
    var $grid = $('.comic-container').isotope({
      itemSelector: '.grid-item',
      layoutMode: 'fitRows',
      filter: function() {
        var $this = $(this);
        var searchResult = qsRegex ? $this.text().match( qsRegex ) : true;
        var buttonResult = buttonFilter ? $this.is( buttonFilter ) : true;
        return searchResult && buttonResult;
      }
    });
    $('#filters').on( 'click', 'button', function() {
      buttonFilter = $( this ).attr('data-filter');
      sessionStorage.setItem(window.location.href+"button", buttonFilter);
      $grid.isotope();
    });

    var $quicksearch = $('#quicksearch').keyup( debounce( function() {
         qsRegex = new RegExp($quicksearch.val(), 'gi');
         sessionStorage.setItem(window.location.href+'text', $quicksearch.val());
      $grid.isotope();
    }) );

    // debounce so filtering doesn't happen every millisecond
    function debounce( fn, threshold ) {
      var timeout;
      threshold = threshold || 100;
      return function debounced() {
        clearTimeout( timeout );
        var args = arguments;
        var _this = this;
        function delayed() {
          fn.apply( _this, args );
        }
        timeout = setTimeout( delayed, threshold );
      };
    }
setInterval(function (){
    $grid.isotope();
}, 1000)

let field = document.getElementById("quicksearch");

// See if we have an autosave value
// (this will only happen if the page is accidentally refreshed)
if (sessionStorage.getItem(window.location.href+'text') || sessionStorage.getItem(window.location.href+'button')) {
  // Restore the contents of the text field
  field.value = sessionStorage.getItem(window.location.href+'text');
  qsRegex = new RegExp($quicksearch.val(), 'gi');
  buttonFilter = sessionStorage.getItem(window.location.href+'button');
  $grid.isotope();
}

// Listen for changes in the text field
field.addEventListener("change", function() {
  // And save the results into the session storage object

});

function comic_action(selector, item_type, action) {
    $.ajax({
        url: '/comic/action/' + action + '/' + item_type + '/' + selector + '/',
        success: function (){window.location.reload()}
    })

}
