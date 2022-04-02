let qsRegex;
let buttonFilter;
const js_urls = JSON.parse(document.getElementById('js_urls').textContent)

let $grid = $('.comic-container').isotope({
  itemSelector: '.grid-item',
  layoutMode: 'fitRows',
  filter: function() {
    let $this = $(this);
    let searchResult = qsRegex ? $this.text().match( qsRegex ) : true;
    let buttonResult = buttonFilter ? $this.is( buttonFilter ) : true;
    return searchResult && buttonResult;
  }
});

$('#filters').on( 'click', 'button', function() {
    if (typeof $( this ).attr('data-filter') === "undefined") {}
    else {
        buttonFilter = $( this ).attr('data-filter');
        sessionStorage.setItem(window.location.href+"button", buttonFilter);
        $grid.isotope();
    }
});

let $quicksearch = $('#quicksearch').keyup( debounce( function() {
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

$( ".progress-bar" ).each(function( index ) {
    let bar = $(this)
    bar.css('width', bar.attr('aria-valuenow') + '%')
});

let comic_action_elements = document.getElementsByClassName('comic_action')

comic_action_elements.forEach(el => el.addEventListener('click', event => {
    let target = $(event.target).closest('button')
    let selector = target.attr('selector')
    let item_type = target.attr('itemtype')
    let action = target.attr('comic_action')
    comic_action(selector, item_type, action)
}));

let modal_buttons = document.getElementsByClassName('modal-button')

modal_buttons.forEach(el => el.addEventListener('click', event => {

    let target = $(event.target).closest('button')
    let selector = target.attr('selector')

    let modal = $('#editModal')
    modal.attr('selector', selector)
    modal.attr('itemtype', target.attr('itemtype'))

    let title = $('#editModalLabel')
    let title_source = $('.card-title.'+selector)
    title.text(title_source.text())

    let classification = $('select[name="classification"]')
    let classification_value = $('.classification-badge.'+selector)
    classification.val(classification_value.attr('classification'))

}))

let save_button = document.getElementById('save_button')

save_button.addEventListener('click', function (event){
    let modal = $('#editModal')
    let selector = modal.attr('selector')
    let itemtype = modal.attr('itemtype')
    let classification = $('select[name="classification"]')
    let classification_badge = $('.classification-badge.'+selector)
    let action_url = js_urls.perform_action.replace('operation', 'set_classification').replace('item_type', itemtype).replace('selector', selector)
    $.ajax({
        type: "POST",
        url: action_url,
        data: {
            classification:  classification.val(),
            csrfmiddlewaretoken: $('input[name="csrfmiddlewaretoken"]').attr('value')
        },
        success: function (ev){
            classification_badge.text($('select[name="classification"] option:selected').text())
            modal.modal('hide')
        },
    })


})

$( "img" ).on("error", function() {
    $(this).src=$(this).attr('alt_src');
})
