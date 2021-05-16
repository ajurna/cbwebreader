// If absolute URL from the remote server is provided, configure the CORS
// header on that server.
const nav = JSON.parse(document.getElementById('nav').textContent);
const last_read_page = JSON.parse(document.getElementById('last_read_page').textContent);
var url = "/comic/read/" + nav.cur_path + "/pdf"

// Loaded via <script> tag, create shortcut to access PDF.js exports.
var pdfjsLib = window['pdfjs-dist/build/pdf'];


// The workerSrc property shall be specified.
pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/pdfjs/build/pdf.worker.js';

var pdfDoc = null,
    pageNum = last_read_page,
    pageRendering = false,
    pageNumPending = null,
    scale = 0.8,
    canvas = document.getElementById('the-canvas'),
    ctx = canvas.getContext('2d');

/**
 * Get page info from document, resize canvas accordingly, and render page.
 * @param num Page number.
 */
function renderPage(num) {
  pageRendering = true;
  // Using promise to fetch the page
  pdfDoc.getPage(num).then(function(page) {
    let viewport = page.getViewport({scale: (window.innerWidth *.95) / page.getViewport({scale:1.0}).width});
    canvas.height = viewport.height;
    canvas.width = viewport.width;

    // Render PDF page into canvas context
    let renderContext = {
      canvasContext: ctx,
      viewport: viewport
    };
    let renderTask = page.render(renderContext);

    // Wait for rendering to finish
    renderTask.promise.then(function() {
      pageRendering = false;
      if (pageNumPending !== null) {
        // New page rendering is pending
        renderPage(pageNumPending);
        pageNumPending = null;
      }
    }).then(function () {
        document.getElementById('the-canvas').scrollIntoView({behavior: 'smooth'})
        $.ajax({url: "/comic/set_page/" + nav.cur_path + "/" + (num-1) + "/"})
    });
  });

  // Update page counters
  document.getElementById('page_num').textContent = num;
}

/**
 * If another page rendering in progress, waits until the rendering is
 * finised. Otherwise, executes rendering immediately.
 */
function queueRenderPage(num) {
  if (pageRendering) {
    pageNumPending = num;
  } else {
    renderPage(num);
  }
}

/**
 * Displays previous page.
 */
function onPrevPage() {
    if (pageNum <= 1) {
        if (nav.prev_type === 'ComicBook'){
            window.location = "/comic/read/"+ nav.prev_path +"/"
        } else {
            window.location = "/comic/"+ nav.prev_path +"/"
        }
    } else {
        pageNum--;
        queueRenderPage(pageNum);
    }

}
document.getElementById('prev').addEventListener('click', onPrevPage);

/**
 * Displays next page.
 */
function onNextPage() {
    if (pageNum >= pdfDoc.numPages) {
        if (nav.next_type === 'ComicBook'){
            window.location = "/comic/read/"+ nav.next_path +"/"
        } else {
            window.location = "/comic/"+ nav.next_path +"/"
        }
    } else {
        pageNum++;
        queueRenderPage(pageNum);
    }

}
document.getElementById('next').addEventListener('click', onNextPage);

/**
 * Asynchronously downloads PDF.
 */
pdfjsLib.getDocument(url).promise.then(function(pdfDoc_) {
  pdfDoc = pdfDoc_;
  document.getElementById('page_count').textContent = pdfDoc.numPages;

  // Initial/first page rendering
  renderPage(pageNum);
});

$(document).keydown(function(e) { // add arrow key support
    switch(e.which) {
        case 37: // left
            onPrevPage()
        break;

        case 38: // up
            window.scrollTo({
              top: window.scrollY-window.innerHeight*.7,
              left: 0,
              behavior: 'smooth'
            });
        break;

        case 39: // right
            onNextPage()
        break;

        case 40: // down
            window.scrollTo({
              top: window.scrollY+window.innerHeight*.7,
              left: 0,
              behavior: 'smooth'
            });
        break;

        default: return; // exit this handler for other keys
    }
    e.preventDefault(); // prevent the default action (scroll / move caret)
});

var hammertime = new Hammer(document.getElementById('the-canvas'), {});
hammertime.on('swipeleft', function () {
    onNextPage()
})
hammertime.on('swiperight', function () {
    onPrevPage()
})
hammertime.on('tap', function () {
    onNextPage()
})